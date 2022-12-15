#!/bin/sh

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python # workaround for onnx

mkdir -p onnx_model_repo/ssd_mobilenet_v1/1/

wget -O onnx_model_repo/ssd_mobilenet_v1/1/model.onnx\
    https://media.githubusercontent.com/media/onnx/models/main/vision/object_detection_segmentation/ssd-mobilenetv1/model/ssd_mobilenet_v1_10.onnx

mkdir -p onnx_model_repo/yolov3/1/

wget -O onnx_model_repo/yolov3/1/model.onnx\
    https://media.githubusercontent.com/media/onnx/models/main/vision/object_detection_segmentation/yolov3/model/yolov3-10.onnx

# Tiny_yolov3 doesn't run out of the box in [DeepStream 6.0.1](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Overview.html)
# Provided python script massages the ONNX model to make it run
mkdir -p onnx_model_repo/tiny-yolov3/1/
wget -O onnx_model_repo/tiny-yolov3/1/model0.onnx\
    https://media.githubusercontent.com/media/onnx/models/main/vision/object_detection_segmentation/tiny-yolov3/model/tiny-yolov3-11.onnx
python3 tiny_yolov3_fix.py onnx_model_repo/tiny-yolov3/1/model0.onnx onnx_model_repo/tiny-yolov3/1/model.onnx

mkdir -p onnx_model_repo/yolov4/1

wget -O onnx_model_repo/yolov4/1/model.onnx\
    https://media.githubusercontent.com/media/onnx/models/main/vision/object_detection_segmentation/yolov4/model/yolov4.onnx

wget -O onnx_model_repo/yolov4/yolov4_anchors.txt\
    https://github.com/onnx/models/raw/main/vision/object_detection_segmentation/yolov4/dependencies/yolov4_anchors.txt

wget -O onnx_model_repo/yolov4/coco.names\
    https://github.com/onnx/models/raw/main/vision/object_detection_segmentation/yolov4/dependencies/coco.names

mkdir -p onnx_model_repo/efficientnet-lite4/1

wget -O onnx_model_repo/efficientnet-lite4/1/model.onnx\
    https://media.githubusercontent.com/media/onnx/models/main/vision/classification/efficientnet-lite4/model/efficientnet-lite4-11.onnx

wget -O onnx_model_repo/efficientnet-lite4/labels_map.txt\
    https://github.com/onnx/models/raw/main/vision/classification/efficientnet-lite4/dependencies/labels_map.txt

