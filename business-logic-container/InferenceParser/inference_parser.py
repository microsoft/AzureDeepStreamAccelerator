
class ObjectDetectionResult:
    def from_json(self, message):
        self.classId = message["classId"]
        self.confidence = message["confidence"]
        self.label = message["label"]
        self.rect = message["rect"]
        self.customInfo=None
        if "customInfo" in message.keys():
            self.customInfo = message["customInfo"]

    def get_bbox_center(self):
        return self.rect[0]+0.5*self.rect[2], self.rect[1]+0.5*self.rect[3]

class ClassificationResult:
    def from_json(self, message):
        self.classId = message["classId"]
        self.confidence = message["confidence"]
        self.label = message["label"]

class SegmentationResult:
    def from_json(self, message):
        self.nClasses = message["nClasses"]
        self.height = message["height"]
        self.width = message["width"]
        self.classMap = message["classMap"]
        self.labels = message["labels"]

class CustomResult:
    def from_json(self, message):
        # put your custom inference definition here
        pass

class Inference:
    def from_json(self, message):
        self.source_info = message["sourceInfo"]
        self.type = message["type"]
        self.id = message["id"]
        self.detections = []

        for d in message["detections"]:
            if self.type == "detection":
                result = ObjectDetectionResult()
                result.from_json(d)
                self.detections.append(result)
            elif self.type == "classification":
                result = ClassificationResult()
                result.from_json(d)
                self.detections.append(result)
            elif self.type == "segmentation":
                result = SegmentationResult()
                result.from_json(d)
                self.detections.append(result)
            elif self.type == "custom":
                result = CustomResult()
                result.from_json(d)
                self.detections.append(result)

class Inferences:
    def __init__(self, message=None) -> None:
        if message is not None:
            self.parse_inferences(message=message)

    def parse_inferences(self, message):
        inferences_list = message["inferences"]
        self.inference_count = len(inferences_list)
        self.inferences_list = []
        self.pipeline_ids = []
        for i in inferences_list:
            inference = Inference()
            inference.from_json(i)
            self.pipeline_ids.append(inference.id)
            self.inferences_list.append(inference)