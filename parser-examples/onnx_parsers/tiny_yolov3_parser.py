import numpy as np

from onnx_pipeline import ONNXPipeline
from nms import nms

max_output_size = 20
iou_threshold = 0.5
score_threshold = 0.6

def yxyx2box(yxyx):
    yxyx = (yxyx/416).clip(0,1)
    return [yxyx[1], yxyx[0], yxyx[3], yxyx[2]]

class tiny_yolov3(ONNXPipeline):
    def __init__(self, config_file, class_file_name):
        class_names = [name.strip() for name in open(args.class_file_name).readlines()]
        super(tiny_yolov3, self).__init__(config_file, class_names)

    def parser(self, output_layer_info):
        """ Get data from output_layer_info and fill object_list
            with several NvDsInferObjectDetectionInfo.
    
            Keyword arguments:
            - output_layer_info : represents the neural network's output.
                (NvDsInferLayerInfo list)
            - detection_param : contains per class threshold.
                (DetectionParam)
            - box_size_param : element containing information to discard boxes
                that are too small. (BoxSizeParam)
            - nms_param : contains information for performing non maximal
                suppression. (NmsParam)
    
            Return:
            - Bounding boxes. (NvDsInferObjectDetectionInfo list)
        """
        boxes = self.find_layer_as_array(output_layer_info, 'yolonms_layer_1')
        scores = self.find_layer_as_array(output_layer_info, 'yolonms_layer_1:1')
        if boxes is None or scores is None:
            sys.stderr.write("ERROR: some layers missing in output tensors\n")
            return []
    
        indices = (scores > iou_threshold).nonzero()
    
        box_score_class = [yxyx2box(boxes[idx[0], idx[2], :])+[scores[idx], idx[1]] for idx in zip(*indices) ]
    
        box_score_class.sort(reverse=True, key=lambda x: x[4])
        box_score_class = np.array(box_score_class[:max_output_size])
        #    print(box_score_class)
        if len(box_score_class) > 0:
            bboxes = nms(box_score_class, iou_threshold=iou_threshold)
            # print('bboxes', bboxes)
            return [self.bbox2det(bb) for bb in bboxes]
        else:
            return []
        
if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('input', nargs='?', default='sample_720p.h264')
    p.add_argument('output', nargs='?', default='tiny_yolov3_out.mp4')
    p.add_argument('--config_file', default='tiny_yolov3_nopostprocess.txt')
    p.add_argument('--class_file_name', default='onnx_model_repo/yolov4/coco.names')
    args = p.parse_args()

    pipeline = tiny_yolov3(args.config_file, args.class_file_name)
    pipeline.run(args.input, args.output)
