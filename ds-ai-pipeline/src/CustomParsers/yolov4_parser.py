import numpy as np
from scipy import special
import logging

from .nms import nms
from .base_custom_parser import BaseCustomParser, BoundingBox
from .common import get_labels

XYSCALE = np.array([1.2, 1.1, 1.05])
ANCHORS = np.array([12,16, 19,36, 40,28, 36,75, 76,55, 72,146, 142,110, 192,243, 459,401], dtype=np.float32).reshape(3, 3, 2)
STRIDES = np.array([8, 16, 32])

class Yolov4Parser(BaseCustomParser):
    def __init__(self) -> None:
        super().__init__(model_type=BaseCustomParser.DET_MODEL, name="yolov4")
        self.network_size=(416,416)
        self.image_size=(416,416)
        self.labels = get_labels("coco80")
        self.det_th = 0.5        
        self.mns_th = 0.213

    def parse_det_model(self, raw_outputs: dict):       
        try:
            Ilayer = raw_outputs["Identity:0"]
            Ilayer1 = raw_outputs["Identity_1:0"]
            Ilayer2 = raw_outputs["Identity_2:0"]
        except:
            logging.error("Yolov4Parser. Error: some layers missing in output tensors")
            return []
    
        detections = [Ilayer[np.newaxis,...], Ilayer1[np.newaxis,...], Ilayer2[np.newaxis,...]]
        pred_bbox = postprocess_bbbox(detections, ANCHORS, STRIDES, XYSCALE)


        input_size = self.network_size[0]
        bboxes = postprocess_boxes(pred_bbox=pred_bbox, org_img_shape=self.network_size, 
                                   input_size=input_size, score_threshold=self.det_th)
        bboxes = nms(bboxes, self.mns_th, method='nms') 
    
        width, height = self.image_size
        result=[]
        for bb in bboxes:           
            x = int( width *bb[0]/input_size )
            y = int( height*bb[1]/input_size )
            w = int( width *bb[2]/input_size ) - x + 1
            h = int( height*bb[3]/input_size ) - y + 1
            score = bb[4]
            class_id = int(bb[5])
            result.append(BoundingBox(x=x, y=y, w=w, h=h, class_id=class_id, score=score))
        return result, None 


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


if '__main__' == __name__:
    pass
    
