import numpy as np
import logging

from .nms import nms
from .base_custom_parser import BaseCustomParser, BoundingBox
from .common import get_labels

MAX_OUTPUT_SIZE=20

def yxyx2box(yxyx):
    yxyx = (yxyx/416).clip(0,1)
    return [yxyx[1], yxyx[0], yxyx[3], yxyx[2]]

def get_det(bbox, w: int, h: int):
    return BoundingBox(
        x = int(bbox[0]*w),
        y = int(bbox[1]*h),
        w = int((bbox[2]-bbox[0])*w),
        h = int((bbox[3]-bbox[1])*h),
        score=bbox[4], class_id=int(bbox[5])
    )

class Yolov3Parser(BaseCustomParser):
    def __init__(self) -> None:
        super().__init__(model_type=BaseCustomParser.DET_MODEL, name="yolov4")
        self.network_size=(416,416)
        self.image_size=(416,416)
        self.labels = get_labels("coco80")
        self.det_th = 0.5        
        self.mns_th = 0.213

    def parse_det_model(self, raw_outputs: dict):       
        try:
            boxes = raw_outputs['yolonms_layer_1']
            scores = raw_outputs['yolonms_layer_1:1']
        except:
            logging.error("Yolov3Parser. Error: some layers missing in output tensors")
            return []

        boxes, scores = boxes[np.newaxis,...], scores[np.newaxis,...]
        indices = (scores >= self.det_th).nonzero()   
        box_score_class = [yxyx2box(boxes[idx[0], idx[2], :])+[scores[idx], idx[1]] for idx in zip(*indices)]   
        box_score_class.sort(reverse=True, key=lambda x: x[4])
        box_score_class = np.array(box_score_class[:MAX_OUTPUT_SIZE])
        w, h = self.image_size
        if len(box_score_class) > 0:
            bboxes = nms(box_score_class, iou_threshold=self.det_th)
            return [get_det(bbox=b, w=w, h=h) for b in bboxes], None 
        else:
            return [], None

if '__main__' == __name__:
    pass
    
