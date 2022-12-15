import sys
import numpy as np
from nms import nms
from onnx_pipeline import ONNXPipeline

import pyds

IOU_THRESHOLD = 0.3

class onnx_ssd(ONNXPipeline):
    def __init__(self, config_file, class_file_name):
        class_names = [name.strip() for name in open(args.class_file_name).readlines()]
        super(onnx_ssd, self).__init__(config_file, class_names)

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
        num_detection_layer = self.find_layer_as_array(output_layer_info, "num_detections:0")
        score_layer = self.find_layer_as_array(output_layer_info, "detection_scores:0")
        class_layer = self.find_layer_as_array(output_layer_info, "detection_classes:0")
        box_layer = self.find_layer_as_array(output_layer_info, "detection_boxes:0")
    
        if num_detection_layer is None or score_layer is None or class_layer is None or box_layer is None:
            sys.stderr.write("ERROR: some layers missing in output tensors\n")
            return []
    
        num_detection = int(num_detection_layer[0][0])

        scores = score_layer[0, :num_detection, None]
        classes = class_layer[0, :num_detection, None].astype('int')
        boxes = box_layer[0, :num_detection, :].clip(0, 1)

        bboxes = np.concatenate((boxes, scores, classes), axis=1)
        
        bboxes = nms(bboxes, IOU_THRESHOLD, method='nms')
        #print('bboxes', bboxes)
        # flip x, y
        object_list = [self.bbox2det((bb[1], bb[0], bb[3], bb[2], bb[4], bb[5])) for bb in bboxes]
        return object_list
    
if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('input', nargs='?', default='sample_720p-4.h264')
    p.add_argument('output', nargs='?', default='ssd_out.mp4')
    p.add_argument('--config_file', default='onnx_ssd_nopostprocess.txt')
    p.add_argument('--class_file_name', default='labels.txt')
    args = p.parse_args()

    pipeline = onnx_ssd(args.config_file, args.class_file_name)
    pipeline.run(args.input, args.output)
    
