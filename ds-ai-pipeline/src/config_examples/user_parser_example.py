import numpy as np
from core import nms, COCO_LABELS, postprocess_bbbox, postprocess_boxes

XYSCALE = np.array([1.2, 1.1, 1.05])
ANCHORS = np.array([12,16, 19,36, 40,28, 36,75, 76,55, 72,146, 142,110, 192,243, 459,401], dtype=np.float32).reshape(3, 3, 2)
STRIDES = np.array([8, 16, 32])

# mandatory 
model_type   = 0 
# mandatory 
name         = "yolov4_parser_suplied_by_user"

# mandatory if model_type=0
labels       = COCO_LABELS

def parse_det_model(config, raw_outputs: dict):
    """
    This function must return 3 vector:
    For detection models (model_type = 0) 
        1: Nx4 vector containing bounding boxes. Ex.: [(x1, y1, w1, h1), (x1, y1, w1, h1), ...,(xN, yN, wN, hN)] 
        2: N   vector containing class ids. 
        3: N   vector containing the confidences 
        4: Custom message or None 
    For detection models (model_type = 1)
        TODO(otree): complete this  
    """
    try:
        Identity_layer = raw_outputs["Identity:0"]
        Identity_1_layer = raw_outputs["Identity_1:0"]
        Identity_2_layer = raw_outputs["Identity_2:0"]
    except:
        print("Yolov4Parser. Error: some layers missing in output tensors")
        return [], [], [], None 
    
    detections = [Identity_layer, Identity_1_layer, Identity_2_layer]
    pred_bbox = postprocess_bbbox(detections, ANCHORS, STRIDES, XYSCALE)

    input_size = 416
    bboxes = postprocess_boxes(pred_bbox=pred_bbox, org_img_shape=(416,416), 
                                   input_size=input_size, score_threshold=config.det_th)
    bboxes = nms(bboxes, config.mns_th, method='nms') 
    
    width, height = config.image_size
    bboxes = np.array(bboxes)
    bboxes[:,:4]  *= np.array([width/416.0, height/416.0, width/416.0, height/416.0])
    bboxes[:,2:4] -= bboxes[:,:2]

    return bboxes[:,:4], bboxes[:,5].astype(np.int), bboxes[:,4], "USER_PARSER" 

if __name__ == "__main__":
    pass