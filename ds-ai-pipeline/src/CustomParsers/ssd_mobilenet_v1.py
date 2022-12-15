import numpy as np
from .base_custom_parser import BoundingBox, BaseCustomParser
from .common import get_labels
import logging
from .nms import nms

def bbox2det(bbox, w: int, h: int):
    return BoundingBox(score=bbox[4], 
                       class_id=int(bbox[5]), 
                       x = int(w*bbox[1]), 
                       y = int(h*bbox[0]), 
                       w = int((bbox[3]-bbox[1])*w), 
                       h = int((bbox[2]-bbox[0])*h) )

class SSDMobilenetV1(BaseCustomParser):
    def __init__(self) -> None:
        super().__init__(model_type=BaseCustomParser.DET_MODEL, name="onnx_ssd")
        self.network_size=(300,300)
        self.image_size=(300,300)
        self.labels = get_labels("coco90", background_label="unlabeled")
        self.det_th = 0.5        
        self.mns_th = 0.213

    def parse_det_model(self, raw_outputs: dict):       
        try:
            num_detection_layer = raw_outputs["num_detections:0"]
            score_layer = raw_outputs["detection_scores:0"]
            class_layer = raw_outputs["detection_classes:0"]
            box_layer = raw_outputs["detection_boxes:0"]
        except:
            logging.error("SSDMobilenetV1. Error: some layers missing in output tensors")
            return []
   
        num_detection = int(num_detection_layer[0])
        scores = score_layer[:num_detection, None]
        classes = class_layer[:num_detection, None].astype('int')
        boxes = box_layer[:num_detection, :].clip(0, 1)

        bboxes = np.concatenate((boxes, scores, classes), axis=1)
        bboxes = nms(bboxes, self.mns_th, method='nms')

        w, h = self.image_size                       
        return [bbox2det(b, w=w, h=h) for b in bboxes], None             

if '__main__' == __name__:
    pass

