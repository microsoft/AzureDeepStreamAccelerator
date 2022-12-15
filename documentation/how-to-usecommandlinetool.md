# How to: Use the command line interface tool
Containers are useful tools for managing a wide variety of software deployments, including IoT solutions on the edge.
To simplify the container build process for this solution, we have included a command line interface (CLI) tool in this repository.
This CLI tool will help you package your model into a container and push it to your preferred registry

In our architecture, there are several containers, including:

- **AI Pipeline module**: Contains the DeepStream compatible CV model and communicates model inferences to the Business Logic module.
- **Controller module**: Enables management of the entire solution.
- **Business Logic module**: Contains event detection logic, based on user defined Regions of Interest (ROIs), and will be the typical place that you will put your own business logic code (if applicable).
It will determine if a pre-defined event occurs during a video segment and communicate this status to the Video Uploader.
- **RTSP Simulation module**: Converts a stored video file into an RTSP stream to facilitate development. This is useful for debugging and development, as it allows you to use a video file
instead of having to set up a camera for development, but this container is optional in a deployment.
- **Video Uploader module**: Processes video segments of pre-defined length.
Uploads only those segments containing pre-defined events to blob storage, based on input from the Business Logic module.

Of particular importance are these two:

1. **AI Pipeline module**
1. **Business Logic module**

These two containers are the ones you will typically be modifying. In particular, you will rebuild the AI pipeline module (typically without changing its source code)
to use whatever model you are bringing, while the business logic container will contain all of your application's source code.

This document describes the tool that you should use to build these containers.

## Prerequisites
- Make sure you have completed all the prerequisites in the [Quickstart article](./quickstart-readme.md).
- A trained CV model and parser.
- Container registry credentials.

## Model Compatability Matrix
[Triton Inference Server](https://github.com/triton-inference-server/server) is an NVIDIA framework for providing broad support
for different types of AI models. It allows you to bring an AI model from almost any deep learning framework and execute it
on NVIDIA hardware.

However, with this flexibility comes a price. It is quite large - the default DeepStream container with Triton Server integrated into it
for x86 machines is close to 20 GB.

Consult the table below to determine if you need to use Triton Inference Server.

| Model Type            | Needs Triton Server           |
|-----------------------|-------------------------------|
| TensorRT              | No                            |
| TAO                   | No                            |
| Tensorflow            | Yes                           |
| PyTorch               | Yes                           |
| ONNX                  | Yes                           |
| OpenVINO              | Yes                           |

Please remember that Triton Server images are significantly larger than DeepStream base images,
so if you can convert your model to TRT, you can save a few GBs in your edge deployment by doing so (not to mention there may be speed increases)!

If you must use Triton Inference Server, we can still pare down the size of the AI Pipeline container by
stripping out the backends that we don't need. For example, if you are using ONNX, you may not need the OpenVINO,
Tensorflow, and PyTorch backends. This document will describe how to strip out the backends you don't need using
the provided CLI tool.


## CLI Tool

### Installation

If you followed the [Quickstart](./quickstart-readme.md), you should already have the CLI tool installed. If not, see [here for instructions](../cli/README.md).

### Building a Docker image

To create an AI Pipeline image, use the `azdacli create` command. This command has several arguments. Run `azdacli create --help` for help.

Of particular note:

* `--build-dir`: This argument is required and must be the path on your system (relative or absolute) **to the 'docker-build' folder inside the `ds-ai-pipeline` folder**.
* `--device-type`: This option is how you specify ARM vs x86. Choose `dGPU` (the default) for x86 systems and `Jetson` for Jetson systems.
* `--tag`: This is the tag that we will give to the generated Docker image.
* `--backend`: If no backend is specified, we opt for the smallest image, which does not include Triton Inference Server. If you require Triton Inference Server
(see the [compatability matrix](#model-compatability-matrix)), you must specify which backend(s) you need. If you want multiple backends, specify this by
passing more than one `--backend` argument.
* `--add`: This is the way you will include custom assets into the created image. If you need to include a custom folder, make sure the folder is inside the `ds-ai-pipeline`
folder and specify where this folder is on your host system and where you want it in the built image. For example `--add "./my-custom-assets /"` will place
`my-custom-assets` into the root directory of the built image. Note the quotation marks around the argument.
* `--run`: This is the way you will install apt packages (or execute arbitrary additional Docker RUN commands). For example, `--run "apt-get install -y build-essential"`
* `--light-tracker`: This flag will make sure that we build in [Light Tracker](https://github.com/researchmm/LightTrack) support, in case you want to use this tracker.
will install build tools into the Docker image.

**Example command**

        azdacli create \
        --deepstream-image-type triton \
        --device-type dGPU \
        --tag "demo1" \
        --backend tensorrt \
        --backend pytorch \
        --add "source/sourcefile.txt opt/nvidia/destination/" \
        --add "source2/folder/ opt/nvidia/destination2" \
        --run "git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps" \
        --run "apt install -y python3-gi python3-dev python3-gst-1.0 python-gi-dev git python-dev python3 python3-pip python3.8-dev cmake g++ build-essential libglib2.0-dev libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev"

The above command will create an ARM image with Triton server installed (with TensorRT and PyTorch backends). It will add a few files/folders into the container, and it will run
several installation commands in addition to all the installations that we do to make our code run.

You may need to run `--run` commands to install dependencies for your model's parser.


## Uploading the Docker image to a container registry

To upload a created AI Pipeline image, use the `azdacli push`. This command has a few arguments. Run `azdacli push --help` for help.

## Docker CLI

Note that you can also use native Docker commands such as `docker push` to manipulate images created by the CLI Tool, in case that is more convenient for you.