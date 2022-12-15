from .base_custom_parser import BaseCustomParser, BoundingBox

class UserParser(BaseCustomParser):
    def __init__(self, user_funct) -> None:       
        super().__init__(model_type=user_funct.model_type, name=user_funct.name)

        self.user_funct = user_funct
        if hasattr(self.user_funct, "labels"):
            self.labels = self.user_funct.labels

    def parse_det_model(self, raw_outputs: dict):       
        bboxes, idxs, scores, custom_msg = self.user_funct.parse_det_model(self, raw_outputs)
        dets = [BoundingBox(x=box[0], y=box[1], w=box[2], h=box[3], score=sc, class_id=idx) for box, idx, sc in zip(bboxes, idxs, scores)]
        return dets, custom_msg

    def parse_custom_model(self, raw_outputs: dict):
        return self.user_funct.parse_custom_model(self, raw_outputs)

    def add_custom_to_meta(self, outputs, batch_meta, frame_meta):
        if hasattr(self.user_funct, "add_custom_to_meta"):
            self.user_funct.add_custom_to_meta(self, outputs, batch_meta, frame_meta)


if '__main__' == __name__:
    pass
    
    
