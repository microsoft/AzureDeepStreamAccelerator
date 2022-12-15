import numpy as np
from scipy import special

from nms import nms
from onnx_pipeline import ONNXPipeline


def get_anchors(anchors_path, tiny=False):
    '''loads the anchors from a file'''
    with open(anchors_path) as f:
        anchors = f.readline()
    anchors = np.array(anchors.split(','), dtype=np.float32)
    return anchors.reshape(3, 3, 2)

ANCHORS = 'onnx_model_repo/yolov4/yolov4_anchors.txt'
STRIDES = [8, 16, 32]
XYSCALE = [1.2, 1.1, 1.05]

ANCHORS = get_anchors(ANCHORS)
STRIDES = np.array(STRIDES)

def postprocess_bbbox(pred_bbox, ANCHORS, STRIDES, XYSCALE=[1,1,1]):
    '''define anchor boxes'''
    for i, pred in enumerate(pred_bbox):
        conv_shape = pred.shape
        output_size = conv_shape[1]
        conv_raw_dxdy = pred[:, :, :, :, 0:2]
        conv_raw_dwdh = pred[:, :, :, :, 2:4]
        xy_grid = np.meshgrid(np.arange(output_size), np.arange(output_size))
        xy_grid = np.expand_dims(np.stack(xy_grid, axis=-1), axis=2)

        xy_grid = np.tile(np.expand_dims(xy_grid, axis=0), [1, 1, 1, 3, 1])
        xy_grid = xy_grid.astype(np.float)

        pred_xy = ((special.expit(conv_raw_dxdy) * XYSCALE[i]) - 0.5 * (XYSCALE[i] - 1) + xy_grid) * STRIDES[i]
        pred_wh = (np.exp(conv_raw_dwdh) * ANCHORS[i])
        pred[:, :, :, :, 0:4] = np.concatenate([pred_xy, pred_wh], axis=-1)

    pred_bbox = [np.reshape(x, (-1, np.shape(x)[-1])) for x in pred_bbox]
    pred_bbox = np.concatenate(pred_bbox, axis=0)
    return pred_bbox

def postprocess_boxes(pred_bbox, org_img_shape, input_size, score_threshold):
    '''remove boundary boxs with a low detection probability'''
    valid_scale=[0, np.inf]
    pred_bbox = np.array(pred_bbox)

    pred_xywh = pred_bbox[:, 0:4]
    pred_conf = pred_bbox[:, 4]
    pred_prob = pred_bbox[:, 5:]

    # (1) (x, y, w, h) --> (xmin, ymin, xmax, ymax)
    pred_coor = np.concatenate([pred_xywh[:, :2] - pred_xywh[:, 2:] * 0.5,
                                pred_xywh[:, :2] + pred_xywh[:, 2:] * 0.5], axis=-1)
    # (2) (xmin, ymin, xmax, ymax) -> (xmin_org, ymin_org, xmax_org, ymax_org)
    org_h, org_w = org_img_shape
    resize_ratio = min(input_size / org_w, input_size / org_h)

    dw = (input_size - resize_ratio * org_w) / 2
    dh = (input_size - resize_ratio * org_h) / 2

    pred_coor[:, 0::2] = 1.0 * (pred_coor[:, 0::2] - dw) / resize_ratio
    pred_coor[:, 1::2] = 1.0 * (pred_coor[:, 1::2] - dh) / resize_ratio

    # (3) clip some boxes that are out of range
    pred_coor = np.concatenate([np.maximum(pred_coor[:, :2], [0, 0]),
                                np.minimum(pred_coor[:, 2:], [org_w - 1, org_h - 1])], axis=-1)
    invalid_mask = np.logical_or((pred_coor[:, 0] > pred_coor[:, 2]), (pred_coor[:, 1] > pred_coor[:, 3]))
    pred_coor[invalid_mask] = 0

    # (4) discard some invalid boxes
    bboxes_scale = np.sqrt(np.multiply.reduce(pred_coor[:, 2:4] - pred_coor[:, 0:2], axis=-1))
    scale_mask = np.logical_and((valid_scale[0] < bboxes_scale), (bboxes_scale < valid_scale[1]))

    # (5) discard some boxes with low scores
    classes = np.argmax(pred_prob, axis=-1)
    scores = pred_conf * pred_prob[np.arange(len(pred_coor)), classes]
    score_mask = scores > score_threshold
    mask = np.logical_and(scale_mask, score_mask)
    coors, scores, classes = pred_coor[mask], scores[mask], classes[mask]

    return np.concatenate([coors, scores[:, np.newaxis], classes[:, np.newaxis]], axis=-1)

class yolov4(ONNXPipeline):
    def __init__(self, config_file, class_file_name):
        class_names = [name.strip() for name in open(args.class_file_name).readlines()]
        super(yolov4, self).__init__(config_file, class_names)

    def parser(self, output_layer_info):
        Identity_layer = self.find_layer_as_array(output_layer_info, "Identity:0")
        Identity_1_layer = self.find_layer_as_array(output_layer_info, "Identity_1:0")
        Identity_2_layer = self.find_layer_as_array(output_layer_info, "Identity_2:0")
    
    #    print('output_layer_info', [(l.layerName, list(l.dims.d)) for l in output_layer_info])
        if Identity_layer is None or Identity_1_layer is None or Identity_2_layer is None:
            sys.stderr.write("ERROR: some layers missing in output tensors\n")
            return []
    
        detections = [Identity_layer, Identity_1_layer, Identity_2_layer]
        #print('Identity_2_layer', Identity_2_layer))
        pred_bbox = postprocess_bbbox(detections, ANCHORS, STRIDES, XYSCALE)
        #print('pred_bbox', pred_bbox)
    
        original_image_size = (416, 416)
        input_size = 416
        bboxes = postprocess_boxes(pred_bbox, original_image_size, input_size, 0.5)
        bboxes = nms(bboxes, 0.213, method='nms')
    
        for bb in bboxes:
            bb[0] /= 416
            bb[2] /= 416
            bb[1] /= 416
            bb[3] /= 416
    
    #    print('bboxes', bboxes)
    
        return [self.bbox2det(bb) for bb in bboxes]
    
if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('input', nargs='?', default='sample_720p.h264')
    p.add_argument('output', nargs='?', default='yolov4_out.mp4')
    p.add_argument('--config_file', default='yolov4_nopostprocess.txt')
    p.add_argument('--class_file_name', default='onnx_model_repo/yolov4/coco.names')
    args = p.parse_args()

    pipeline = yolov4(args.config_file, args.class_file_name)
    pipeline.run(args.input, args.output)
    
