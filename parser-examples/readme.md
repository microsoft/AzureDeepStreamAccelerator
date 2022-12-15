# Overview

Sample parsers for four(4) ONNX models and two(2) [Tao models](https://docs.nvidia.com/tao/tao-toolkit/text/overview.html)

## Prerequisite

Nvidia docker runtime. For details, see [Jetson](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_docker_containers.html#recommended-minimal-l4t-setup-necessary-to-run-the-new-docker-images-on-jetson).

Please ensure that there are at least 25GB free space for `/var/lib/docker` on dGPU device and 10GB for Jetson.

A simple way to free up some space is

	sudo apt-get clean

**Note**

Make sure that the following lines are in `/etc/docker/daemon.json`

	{
	    "runtimes": {
             	"nvidia": {
	            "path": "nvidia-container-runtime",
        	    "runtimeArgs": []
		        }
    		}
	}

If not, create `/etc/docker/daemon.json` if necessary and add the above lines to it.  Restart dockerd

	service dockerd restart


## Prepare Docker

Download and build [DeepStream Python Binding](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git) using the [instruction](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/tree/master/bindings)

I included a pre-build [python wheel](docker/pyds-1.1.1-py3-none-linux_x86_64.whl) along with a [Dockerfile](docker/Dockerfile)

	cd parser-examples/docker
	docker build -t ds61 .

or on Jetson

	docker build -t ds61 -f Dockerfile-l4t .

To start the docker, run

	docker/run_ds61.sh

## ONNX Models

	cd	parser-examples/onnx_parsers

### Fetch ONNX models
	
From [ONNX Model Zoo](https://github.com/onnx/models)

	onnx_parsers/prepare_onnx_model_repo.sh

### Parsers

1. SSD-MobilenetV1
	[ssd_mobilenet_v1](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/ssd-mobilenetv1#ssd-mobilenetv1)

	cd onnx_parsers

	python3 onnx_ssd_parser.py  /opt/nvidia/deepstream/deepstream-6.0/samples/streams/sample_720p.h264

	Inference results will be in out.mp4


1. YOLOv4
	[yolov4](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/yolov4#yolov4)


	python3 [yolov4_parser.py](onnx_parsers/yolov4_parser.py)  /opt/nvidia/deepstream/deepstream-6.0/samples/streams/sample_720p.h264

	output written to `yolov4-out.mp4`

	**Preprocessing**

	Input image normalized to [0,1].   In [yolov4_nopostprocess.txt](onnx_parsers/yolov4_nopostprocess.txt), `infer_config.preprocess.normalize.scale_factor=3.92156862745e-3` (1/255.0)

	**Postprocessing**
	
	Outputs three (3) layers of type `float32`
	
	* `Identity:0` (52, 52, 3, 85)

	* `Identity_1:0` (26, 26, 3, 85)

	* `Identity:0` (13, 13, 3, 85)

	[layer2array](onnx_parsers/yolov4_parser.py) converts layer to numpy array of the same shape

	[prepare_onnx_model_repo.sh](onnx_parsers/prepare_onnx_model_repo.sh) also downloads 
	[yolov4_anchors.txt](https://raw.githubusercontent.com/hunglc007/tensorflow-yolov4-tflite/master/data/anchors/yolov4_anchors.txt) and [coco.names](https://raw.githubusercontent.com/hunglc007/tensorflow-yolov4-tflite/master/data/classes/coco.names)

	postprocessing [python code](onnx_parsers/yolov4_parser.py) copied from [postprocessing-steps](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/yolov4#postprocessing-steps)


1. Tiny YOLOv3
	[tiny-yolov3](https://github.com/onnx/models/tree/main/vision/object_detection_segmentation/tiny-yolov3#tiny-yolov3)
	
	Doesn't run out of the box in [DeepStream 6.0.1](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Overview.html)

	`tiny-yolov3` requires two inputs `input_1`(image data) and `image_shape` ((416, 416) for the model), while DeepStream 6.0.1 only supports image data without a [custom plugin](https://docs.nvidia.com/metropolis/deepstream/4.0/dev-guide/DeepStream_Development_Guide/baggage/nvdsinfer__custom__impl_8h.html). 

	`tiny-yolov3` also expects the image data in NCHW formats.  
	
	A python script [tiny_yolov3_fix.py](onnx_parsers/tiny_yolov3_fix.py) is provided to massage the inputs and skipped [NonMaxSuppression](https://github.com/onnx/onnx/blob/main/docs/Operators.md#NonMaxSuppression), which caused [nvinfer](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvinfer.html) to crash.

	A python implementation of NMS is provided in [tiny_yolov3_parser.py](onnx_parsers/tiny_yolov3_parser.py)

	`python3 tiny_yolov3_parser.py /opt/nvidia/deepstream/deepstream-6.0/samples/streams/sample_720p.h264`

	Inference results will be written to `tiny_yolov3_out.mp4`

1. Efficientnet lite4

	(EfficientNet-Lite4)[https://github.com/onnx/models/tree/main/vision/classification/efficientnet-lite4]	
	is a classification network.  Instead of bounding boxes for detected objects, it returns top 5 category names with confidence scores

	`python3 efficientnet_lite4_parser.py /opt/nvidia/deepstream/deepstream-6.0/samples/streams/sample_720p.h264`
	
	Outputs will be in `efficientnet_lite4_out.mp4`

	
## TAO Models

	cd parser-examples/tao_parsers


### Fetch Models From NGC

	sh prepare_models.sh

### Vehicle License Plate Recognization

The pipeline is based on https://github.com/NVIDIA-AI-IOT/deepstream_lpr_app. It uses three TAO models below

[TrafficCamNet](https://ngc.nvidia.com/catalog/models/nvidia:tao:trafficcamnet)

[LPD (license plate detection)](https://ngc.nvidia.com/catalog/models/nvidia:tao:lpdnet)

[LPR (license plate recognization)](https://ngc.nvidia.com/catalog/models/nvidia:tao:lprnet)

	cd tao_parsers

	python3 lpr_parser.py --output=lpr_out.mp4 --input=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264

will output the detection results in lpr_out.mp4 and recognized license plates to stdout.

** Note on Jetson **

LPR model crashes on Jetson during Tensor RT conversion.  To run TrafficCamNet and LPD only, 

	python3 lpr_parser.py --lpr_config=''	



### Bodypose 2D

The bodypose2D sample application uses [bodypose2D model](https://ngc.nvidia.com/catalog/models/nvidia:tao:bodyposenet) to detect human body parts coordinates. The application can output the 18 body parts:

1. nose
1. neck
1. right shoulder
1. right elbow
1. right hand
1. left shoulder
1. left elbow
1. left hand
1. right hip
1. right knee
1. right foot
1. left hip
1. left knee
1. left foot
1. right eye
1. left eye
1. right ear
1. left ear
    
**Network Outputs**

    * heatmaps (H1' x W1' x C) 
    * part affinity fields (H2' x W2' x P)

C is the number of confidence map channels - corresponds to number of keypoints + background

P is the number of part affinity field channels - corresponds to the (2 x number of edges used in the skeleton)

H1', W1' are the height and width of the output confidence maps respectively

H2', W2' are the height and width of the output part affinity fields respectively

**Post Processing**

Based on the python code in [Part Affinity Field Implementation in PyTorch](https://github.com/NiteshBharadwaj/part-affinity.git)

NMS and bipartite graph matching gives the final results with M x N X 3

N is the number of keypoints.

M is the number of humans detected in the image.


To run the model

	cd tao_parsers

	python3 bodypose2d_parser.py --output=bodypose2d_out.mp4 --input=/opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.h264

The detected body limbs (edges) will be overlaid in the output video bodypose2d_out.mp4
