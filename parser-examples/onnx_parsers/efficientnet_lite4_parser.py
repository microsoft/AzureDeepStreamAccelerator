import numpy as np
import json

from nms import nms
from onnx_pipeline import ONNXPipeline

class efficientnet_lite4(ONNXPipeline):
    def __init__(self, config_file, class_file_name):
        class_names = list(json.load(open(class_file_name)).values())
        super(efficientnet_lite4, self).__init__(config_file, class_names)

    def parser(self, output_layer_info):
        """ Get data from output_layer_info and fill object_list
            with several NvDsInferObjectDetectionInfo.
    
            Keyword arguments:
            - output_layer_info : represents the neural network's output.
                (NvDsInferLayerInfo list)

            Return:
            - Bounding boxes. (NvDsInferObjectDetectionInfo list)
        """
        classes = self.find_layer_as_array(output_layer_info, 'Softmax:0')[0]
        if classes is None:
            sys.stderr.write("ERROR: some layers missing in output tensors\n")
            return []
    
        #print('classes.shape', classes.shape)
        #print('classes', classes)
    
        top_5 = classes.argsort()[-5:][::-1]    # descending
    
        #print([(self.class_names[k], classes[k]) for k in top_5])
        
        return [self.bbox2det((0.01, 0.2 + p*0.1, 0.02, 0.21 + p*0.1, classes[k], k))
               for p, k in enumerate(top_5)]

    def frame_stats(self, frame_meta, display_meta):
        pass                            # classification model. no obj stats.
    
if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('input', nargs='?', default='sample_720p-4.h264')
    p.add_argument('output', nargs='?', default='efficientnet_lite4_out.mp4')
    p.add_argument('--config_file', default='efficientnet_lite4_nopostprocess.txt')
    p.add_argument('--class_file_name', default='onnx_model_repo/efficientnet-lite4/labels_map.txt')
    args = p.parse_args()

    pipeline = efficientnet_lite4(args.config_file, args.class_file_name)
    pipeline.run(args.input, args.output)
    
    
    
