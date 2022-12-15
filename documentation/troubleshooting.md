# Troubleshoot: Azure DeepStream Accelerator - Known issues

This article outlines troubleshooting steps where possible to known issues you may encounter when you are creating an Edge AI solution using Azure DeepStream Accelerator. If you're blocked by any of these issues or encounter any other issues, file a bug here:  [Support](../SUPPORT.md).

This article provides troubleshooting information and possible resolutions for the following issues:

- [The command-line interface (CLI) Tool](#the-command-line-interface-cli-tool)
- [Video Uploader](#video-uploader)
- [NVIDIA Container Runtime](#nvidia-container)
- [Tiny YOLOv3](#tiny-yolov3)
- [Viewing the result stream]()

## The command-line interface (CLI) Tool

### Issue: Installing with Python/Pip

If you install the CLI Tool and it finishes successfully, but you still can't run the tool, you may have more than one globally installed Python version on your system.

#### Troubleshooting steps:

If this is the case, CLI Tool may be installed to one of your other versions instead of the default.
As a general rule, you should have only one Python version installed globally on your system. If you want to have multiple versions, use virtual environments.

> [!NOTE]
> You must have Python installed on your system. Both Python and its site-packages directory must be in your PATH. If this is not the case, the CLI tool will be installed, but you won't be able to run it. Visit the [Python documentation](https://docs.python.org/3/using/windows.html) for installation instructions and post-installations modifications for [Mac/Linux](https://docs.python.org/3/using/unix.html).

## Video Uploader

### Issue: Video Uploader crashes after first deployment

If the Video Uploader module crashes after deployment, it may be because you have not linked your IoT Hub to your **Azure Storage Account**.

#### Troubleshooting steps:

See the [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md#getting-started) for information on how to link your IoT Hub to your **Azure Storage Account**.

## NVIDIA container

### Issue: NVIDIA container runtime

After you deploy the Edge AI model to your Edge device, you may encounter an error with your NVIDIA container runtime.

	```docker: Error response from daemon: Unknown runtime specified nvidia```

#### Potential troubleshooting steps:

You may be able to resolve this by updating the Docker ```daemon.json``` file.

1. To update the daemon file:

   a. Ensure the following lines are included in ```/etc/docker/daemon.json```


	```JSON
		{
			"runtimes": {
					"nvidia": {
					"path": "nvidia-container-runtime",
					"runtimeArgs": []
					}
				}
		}
	```

   b. If you don't have a ```/etc/docker/daemon.json``` file, create one and add the above lines to it.

   c. Restart ```dockerd``` by running the following command:

	```service dockerd restart```

### Issue: Runtime Error: Cannot create nvinfer

If you get a runtime error about creating nvinfer or nvinferserver plugins, and you are on a Jetson device, it is
possible you are not using the correct version of Jetpack. Please make sure to use Jetpack 5.0.x.

#### Troubleshooting steps:

Follow [NVIDIA's walkthrough for upgrading Jetpack](https://docs.nvidia.com/jetson/jetpack/install-jetpack/index.html#upgrade-jetpack).

## Tiny-YOLOv3

### Issue: Tiny-YOLOv3 image format conflicts with DeepStream 6.0.1

The tiny_YOLOv3 model requires two inputs, ```input_1```(image data) and ```image_shape```((416, 416) for the model),
while DeepStream 6.0.1 only supports image data without a [custom plugin](https://docs.nvidia.com/metropolis/deepstream/4.0/dev-guide/DeepStream_Development_Guide/baggage/nvdsinfer__custom__impl_8h.html). Also, tiny-yolov3 expects the image data in NCHW formats.

#### Troubleshooting steps:

To resolve these issues, we have provided a fix in ```tiny_yolov3_fix.py``` in a file that is automatically called by  ```prepare_onnx_model_repo.sh```.

This fix also ignores ```NonMaxSuppression``` to assist with resolving an issue with ```Gst-nvinfer``` (see below).

### Issue: NonMaxSuppression can cause Gst-nvinfer failure

The [NonMaxSuppression](https://github.com/onnx/onnx/blob/main/docs/Operators.md#NonMaxSuppression) operator can cause the [Gst-nvinfer](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvinfer.html)
plug-in to fail.

#### Troubleshooting steps:

To resolve this issue, use the NMS implementation included in ```tiny_yolov3_parser.py```.

## Viewing the Result Stream

### Issue: How do I view the result stream live?

See [this section of the getting started guide](./tutorial-getstarted-path.md#step-5-verify-your-results). You can configure your deployment
to stream RTSP and view that stream in a program like VLC.

## Next Steps

To learn more about creating an Edge AI solution using Azure DeepStream Accelerator, we recommend the following resources:

- [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md)
- [Tutorial: Azure DeepStream Accelerator - Getting started path](./tutorial-getstarted-path.md)
- [Tutorial: Azure DeepStream Accelerator - Pre-built model path](./tutorial-prebuiltmodel-path.md) 
- [Tutorial: Azure DeepStream Accelerator - Bring your own model path (BYOM) model path](./tutorial-byom-path.md)
