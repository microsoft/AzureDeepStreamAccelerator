import numpy as np
import pyds

model_type   = 1  
name         = "ONNXSSDParser"

def parse_custom_model(config, raw_outputs: dict):
    try:
        num_detection_layer = raw_outputs["num_detections:0"]
        score_layer = raw_outputs["detection_scores:0"]
        class_layer = raw_outputs["detection_classes:0"]
        box_layer = raw_outputs["detection_boxes:0"]
    except:
        print("ONNXSSDParser. Error: some layers missing in output tensors")
        return [], None 
   
    num_detection = int(num_detection_layer[0])
    scores = score_layer[:num_detection, None]
    classes = class_layer[:num_detection, None].astype('int')
    boxes = box_layer[:num_detection, :].clip(0, 1)

    bboxes = np.concatenate((boxes, scores, classes), axis=1)
    bboxes = nms(bboxes, 0.23, method='nms')
    w, h = config.image_size                       

    # this `data` will be used in add_custom_to_meta() to insert detection metadata
    data = [bbox2det(b, w=w, h=h) for b in bboxes]

    # here custom message to be serialized in inference result message
    custom_msg={"NoDetections": len(data)}

    return data, custom_msg        

def add_custom_to_meta(config, data, batch_meta, frame_meta):
    UNTRACKED_OBJECT_ID = 0xffffffffffffffff
    labels=['none','person','bicycle','car','motorcycle','airplane','bus','train','truck','boat','traffic light','fire hydrant',
    'street sign','stop sign','parking meter','bench', 'bird','cat','dog','horse','sheep','cow','elephant','bear','zebra','giraffe','hat','backpack',
    'umbrella','shoe','eye glasses','handbag','tie','suitcase','frisbee','skis','snowboard','sports ball', 'kite','baseball bat',
    'baseball glove','skateboard','surfboard','tennis racket','bottle','plate','wine glass','cup','fork','knife','spoon','bowl',
    'banana','apple','sandwich','orange','broccoli','carrot','hot dog','pizza','donut','cake','chair','couch','potted plant',
    'bed','mirror','dining table','window','desk','toilet','door','tv','laptop','mouse','remote','keyboard','cell phone','microwave','oven',
    'toaster','sink','refrigerator','blender','book','clock','vase','scissors','teddy bear','hair drier','toothbrush']

    for obj in data:
        ##############################
        ### Add detection            #
        ##############################
        obj_meta = pyds.nvds_acquire_obj_meta_from_pool(batch_meta)
        # Set bbox properties. These are in input resolution.
        rect_params = obj_meta.rect_params
        rect_params.left   = obj.x
        rect_params.top    = obj.y
        rect_params.width  = obj.w
        rect_params.height = obj.h

        # Set object info including class, detection confidence, etc.
        obj_meta.confidence = obj.score
        obj_meta.class_id = obj.class_id
    
        # There is no tracking ID upon detection. The tracker will assign an ID.
        obj_meta.object_id = UNTRACKED_OBJECT_ID
        obj_meta.obj_label = labels[obj.class_id]

        ####################################
        ### Customize how show the bbox    #
        ####################################
        # Semi-transparent yellow backgroud
        rect_params.has_bg_color = 0
        rect_params.bg_color.set(1, 1, 0, 0.4)
    
        # Red border of width 3
        rect_params.border_width = 3
        rect_params.border_color.set(1, 0, 0, 1)
    
        # Set display text for the object.
        txt_params = obj_meta.text_params
        if txt_params.display_text:
            pyds.free_buffer(txt_params.display_text)
    
        txt_params.x_offset = int(rect_params.left)
        txt_params.y_offset = max(0, int(rect_params.top) - 10)
        txt_params.display_text = obj_meta.obj_label + " " + "{:04.3f}".format(obj.score)

        # Font , font-color and font-size
        txt_params.font_params.font_name = "Serif"
        txt_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        txt_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        txt_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        txt_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
    
        ### Finally, add metadata of the detected object 
        pyds.nvds_add_obj_meta_to_frame(frame_meta, obj_meta, None)


########################################
#         helper functions             #
########################################
def nms(bboxes, iou_threshold, sigma=0.3, method='nms'):

    def bboxes_iou(boxes1, boxes2):
        boxes1 = np.array(boxes1)
        boxes2 = np.array(boxes2)
        boxes1_area = (boxes1[..., 2] - boxes1[..., 0]) * (boxes1[..., 3] - boxes1[..., 1])
        boxes2_area = (boxes2[..., 2] - boxes2[..., 0]) * (boxes2[..., 3] - boxes2[..., 1])
        left_up       = np.maximum(boxes1[..., :2], boxes2[..., :2])
        right_down    = np.minimum(boxes1[..., 2:], boxes2[..., 2:])
        inter_section = np.maximum(right_down - left_up, 0.0)
        inter_area    = inter_section[..., 0] * inter_section[..., 1]
        union_area    = boxes1_area + boxes2_area - inter_area
        ious          = np.maximum(1.0 * inter_area / union_area, np.finfo(np.float32).eps)
        return ious


    classes_in_img = list(set(bboxes[:, 5]))
    best_bboxes = []

    for cls in classes_in_img:
        cls_mask = (bboxes[:, 5] == cls)
        cls_bboxes = bboxes[cls_mask]

        while len(cls_bboxes) > 0:
            max_ind = np.argmax(cls_bboxes[:, 4])
            best_bbox = cls_bboxes[max_ind]
            best_bboxes.append(best_bbox)
            cls_bboxes = np.concatenate([cls_bboxes[: max_ind], cls_bboxes[max_ind + 1:]])
            iou = bboxes_iou(best_bbox[np.newaxis, :4], cls_bboxes[:, :4])
            weight = np.ones((len(iou),), dtype=np.float32)

            assert method in ['nms', 'soft-nms']

            if method == 'nms':
                iou_mask = iou > iou_threshold
                weight[iou_mask] = 0.0

            if method == 'soft-nms':
                weight = np.exp(-(1.0 * iou ** 2 / sigma))

            cls_bboxes[:, 4] = cls_bboxes[:, 4] * weight
            score_mask = cls_bboxes[:, 4] > 0.
            cls_bboxes = cls_bboxes[score_mask]

    return best_bboxes

class BoundingBox:
    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0, class_id: int = 0, score: float = 0) -> None:
        self.x=x
        self.y=y
        self.w=w
        self.h=h
        self.class_id=class_id
        self.score=score

def bbox2det(bbox, w: int, h: int):
    return BoundingBox(score=bbox[4], 
                       class_id=int(bbox[5]), 
                       x = int(w*bbox[1]), 
                       y = int(h*bbox[0]), 
                       w = int((bbox[3]-bbox[1])*w), 
                       h = int((bbox[2]-bbox[0])*h) )