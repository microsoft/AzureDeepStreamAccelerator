# CLI TOOL USAGE INSTRUCTIONS

## Prerequisites

- [Python](https://www.python.org/downloads/)

After installing the prerequisites, you may install this tool by running `pip install .` or `pip install -e .` from this folder.

**Please note**: You must have Python installed on your system **and** it (along with its 'site-packages' directory) must be in your PATH.
If this is not the case, the CLI tool will install, but you won't be able to run it. Please see [the Python documentation](https://docs.python.org/3/using/windows.html)
for installation instructions and post-install modifications ([Mac/Linux](https://docs.python.org/3/using/unix.html))

## CLI TOOL HELP & COMMANDS

```
Usage: azdacli [OPTIONS] COMMAND [ARGS]...

Options:
  --help                          Show help message and exit.

Commands:
  build
  create
  push
```

## CREATE CUSTOM DEEPSTREAM DOCKER IMAGE COMMAND

```
Usage: azdacli create [OPTIONS]

Options:
  --deepstream-image-type         available options - [base|devel|triton|iot|samples]
                                  [default: samples]
  --device-type [dGPU|Jetson]     available options - [default: dGPU]
  --tag TEXT                      [required]
  --backend                       available options - [pytorch|dali|onnxruntime|fil|python|tensorflow1|tensorflow2|tensorrt|square|openvino_2021_4|identity|repeat]
  --add TEXT                      Provide: SOURCE file path <space>
                                  DESTINATION folder path - example:
                                  /home/source/folder/file /opt/nvidia/deepstr
                                  eam/deepstream-6.1/destination/folder/
  --run TEXT                      Type complete command in double quotes, example - "apt install python3-pip"
  --build-image / --no-build-image
                                  [default: build-image]
  --build-dir TEXT
                                  Provide file path of 'docker-build' folder
                                  under 'ds-ai-pipeline' code base. This is
                                  where docker file will be created
                                  [required]
  --help                          Show this message and exit.
```

## PUSH DOCKER IMAGE TO CONTAINER REGISTRY

```
Usage: azdacli push [OPTIONS]

Options:
  --image-name TEXT          [required]
  --container-registry TEXT  [required]
  --username TEXT            [required]
  --password TEXT            [required, comes with prompt]
  --help                     Show this message and exit.
```

## BUILD GENERIC DOCKER IMAGE

```
Usage: azdacli build [OPTIONS]

Options:
  --tag TEXT  [default: azdacliimage], Dockerfile has to be in the working directory
  --help      Show this message and exit.
```

## EXAMPLE

```
azdacli create \
--deepstream-image-type triton \
--device-type dGPU \
--tag demo1 \
--backend tensorrt \
--backend pytorch \
--run "git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps" --run "apt install -y python3-gi python3-dev python3-gst-1.0 python-gi-dev git python-dev python3 python3-pip python3.8-dev cmake g++ build-essential libglib2.0-dev libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev" --run "pip3 install https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.3/pyds-1.1.3-py3-none-linux_x86_64.whl" \
--build-image --build-dir /home/ds-ai-pipeline/docker-build
```
