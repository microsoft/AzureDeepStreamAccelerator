from typing import List, Optional
import subprocess
import typer
import os
from enum import Enum

app = typer.Typer()

class nvidia_deepstream_images(str, Enum):
    """
    Allowable DS image types to base the resulting image off of.
    """
    base = "base"
    development = "devel"
    triton = "triton"
    iot = "iot"
    samples = "samples"

class nvidia_device_type(str, Enum):
    """
    Allowable device types.
    """
    dGPU = "dGPU"  # dGPU is discrete GPU
    Jetson = "Jetson"

class nvidia_deepstream_backends(str, Enum):
    """
    Allowable DS Triton Inference Server backends.
    """
    pytorch = "pytorch"
    dali = "dali"
    onnxruntime = "onnxruntime"
    fil = "fil"
    python = "python"
    tensorflow1 = "tensorflow1"
    tensorflow2 = "tensorflow2"
    tensorrt = "tensorrt"
    square = "square"
    openvino_2021_4 = "openvino_2021_4"
    identity = "identity"
    repeat = "repeat"

DEEPSTREAM_JETSON_URL = "nvcr.io/nvidia/deepstream-l4t:6.1.1-"
DEEPSTREAM_DGPU_URL = "nvcr.io/nvidia/deepstream:6.1.1-"
PYTHON_BINDINGS_DGPU = "https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.4/pyds-1.1.4-py3-none-linux_x86_64.whl"
PYTHON_BINDINGS_JETSON = "https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.4/pyds-1.1.4-py3-none-linux_aarch64.whl"
LIGHT_TRACKER_BUILD_STAGE_DGPU_URL = "nvcr.io/nvidia/deepstream:6.1.1-devel"
LIGHT_TRACKER_BUILD_STAGE_JETSON_URL = "nvcr.io/nvidia/l4t-base:r35.1.0"

def add_run_and_add_commands(f, add, run):
    if add != None:
        for item in add:
            f.write(f"COPY {item}\n")
    if run != None:
        for item in run:
            f.write(f"RUN {item}\n")

def commands_to_jetson(f, light_tracker: bool):
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources\n")
    f.write(f"RUN git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git\n")
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps\n")
    f.write(f"COPY src/requirements.arm.txt /\n")
    f.write(f"COPY src/aptpkgs.arm.txt /\n")
    f.write(f"RUN apt-get update && apt-get install -y dos2unix && dos2unix /aptpkgs.arm.txt && dos2unix /requirements.arm.txt && apt-get install -y $(cat /aptpkgs.arm.txt)\n")
    f.write(f"RUN apt-get --reinstall install libavcodec58 libavutil56 libavformat58\n")
    f.write(f"RUN python3 -m pip install --upgrade pip \n")
    f.write(f"RUN pip3 install -r /requirements.arm.txt \n")
    f.write(f"RUN pip3 install azure-monitor-opentelemetry-exporter --pre\n")
    f.write(f"RUN pip3 install {PYTHON_BINDINGS_JETSON} \n")
    f.write(f"RUN mkdir /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline\n")
    # Strip out the codecs
    f.write(f"RUN apt-get update && apt-get remove -y gstreamer1.0-alsa\n")
    f.write(f"RUN rm /usr/lib/aarch64-linux-gnu/gstreamer-1.0/libgstdtsdec.so\n")
    f.write(f"RUN rm /usr/lib/aarch64-linux-gnu/gstreamer-1.0/libgstvpx.so\n")
    f.write(f"RUN rm /usr/lib/aarch64-linux-gnu/gstreamer-1.0/libgstaom.so\n")
    # --------------------
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline\n")
    f.write(f"COPY src .\n")

    if light_tracker:
        f.write(f"COPY --from=l4t-base /tmp/lighttrack_source/lightmot/liblightmot.so /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/\n")
        f.write(f"COPY --from=l4t-base /tmp/lighttrack_source/lightdet/liblightdet.so /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/\n")

def commands_to_dgpu(f, light_tracker: bool):
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources\n")
    f.write(f"RUN git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git\n")
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps\n")
    f.write(f"COPY src/requirements.amd.txt /\n")
    f.write(f"COPY src/aptpkgs.amd.txt /\n")
    f.write(f"RUN apt-get update && apt-get install -y dos2unix && dos2unix /aptpkgs.amd.txt && dos2unix /requirements.amd.txt && apt-get install -y $(cat /aptpkgs.amd.txt)\n")
    f.write(f"RUN apt-get --reinstall install libavcodec58 libavutil56\n")
    f.write(f"RUN python3 -m pip install --upgrade pip \n")
    f.write(f"RUN pip3 install -r /requirements.amd.txt \n")
    f.write(f"RUN pip3 install azure-monitor-opentelemetry-exporter --pre\n")
    f.write(f"RUN pip3 install {PYTHON_BINDINGS_DGPU} \n")
    f.write(f"WORKDIR /usr/lib/x86_64-linux-gnu\n")
    f.write(f"RUN wget https://nvidia.box.com/shared/static/mwtq4z847uz3v37ba8ntmk3ahfv5fnrm -O libnvinfer_plugin.so.8.2.5.1\n")
    f.write(f"RUN mkdir /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline\n")
    # Strip out the codecs
    f.write(f"RUN apt-get update && apt-get remove -y gstreamer1.0-alsa\n")
    f.write(f"RUN rm /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstdtsdec.so\n")
    f.write(f"RUN rm /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstvpx.so\n")
    f.write(f"RUN rm /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstaom.so\n")
    # --------------------
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline\n")
    f.write(f"COPY src .\n")

    if light_tracker:
        f.write(f"COPY --from=l4t-base /tmp/lighttrack_source/lightmot/liblightmot.so /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/\n")
        f.write(f"COPY --from=l4t-base /tmp/lighttrack_source/lightdet/liblightdet.so /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/\n")

def command_to_main(f):
    f.write(f"CMD export LD_LIBRARY_PATH=${{" + "LD_LIBRARY_PATH}:/opt/tritonserver/lib  && python3 main.py\n")

def command_to_main_jetson(f):
    f.write(f"CMD export LD_LIBRARY_PATH=${{" + "LD_LIBRARY_PATH}:/opt/nvidia/deepstream/deepstream/lib  && python3 main.py\n")

def commands_to_light_tracker_jetson(f):
    f.write(f"FROM {LIGHT_TRACKER_BUILD_STAGE_JETSON_URL} AS l4t-base\n")
    f.write(f"RUN apt-get update -y && apt-get install -y build-essential cmake cuda deepstream-6.1 libeigen3-dev\n")
    f.write(f"COPY src/lighttrack_source /tmp/lighttrack_source\n")
    f.write(f"WORKDIR /tmp/lighttrack_source/lightmot\n")
    f.write(f"RUN cmake . && make -j4\n")
    f.write(f"WORKDIR /tmp/lighttrack_source/lightdet\n")
    f.write(f"RUN cmake . && make -j4\n")

def commands_to_light_tracker_dgpu(f):
    f.write(f"FROM {LIGHT_TRACKER_BUILD_STAGE_DGPU_URL} as base\n")
    f.write(f"RUN apt-get update -y && apt-get install -y build-essential cmake libeigen3-dev\n")
    f.write(f"COPY src/lighttrack_source /tmp/lighttrack_source\n")
    f.write(f"WORKDIR /tmp/lighttrack_source/lightmot\n")
    f.write(f"RUN cmake . && make -j4\n")
    f.write(f"WORKDIR /tmp/lighttrack_source/lightdet\n")
    f.write(f"RUN cmake . && make -j4\n")

def generate_deepstream_dockerfile_for_jetson(deepstream_image_type: nvidia_deepstream_images, run: str, add: str, docker_file_path: str, light_tracker: bool):
    deepstream_image = DEEPSTREAM_JETSON_URL + deepstream_image_type
    f = open(docker_file_path, 'w')
    if light_tracker:
        commands_to_light_tracker_jetson(f)
    f.write(f"FROM {deepstream_image}\n")
    commands_to_jetson(f, light_tracker)
    add_run_and_add_commands(f, add, run)
    command_to_main_jetson(f)
    f.close()

def generate_deepstream_dockerfile(deepstream_image_type: nvidia_deepstream_images, run: str, add: str, docker_file_path: str, light_tracker: bool):
    deepstream_image = DEEPSTREAM_DGPU_URL + deepstream_image_type
    f = open(docker_file_path, 'w')
    if light_tracker:
        commands_to_light_tracker_dgpu(f)
    f.write(f"FROM {deepstream_image}\n")
    commands_to_dgpu(f, light_tracker)
    add_run_and_add_commands(f, add, run)
    command_to_main(f)
    f.close()

def generate_triton_dockerfile_for_jetson(backends, run: str, add: str, docker_file_path: str, light_tracker: bool):
    f = open(docker_file_path, 'w')
    if light_tracker:
        commands_to_light_tracker_jetson(f)
    f.write(f"FROM {DEEPSTREAM_JETSON_URL}triton AS full\n")
    f.write(f"FROM {DEEPSTREAM_JETSON_URL}base\n")
    f.write(f"ENV TRITON_SERVER_USER=triton-server\n")
    f.write(f"RUN userdel tensorrt-server > /dev/null 2>&1 || true &&     if ! id -u $TRITON_SERVER_USER > /dev/null 2>&1 ; then         useradd $TRITON_SERVER_USER;     fi &&     [ `id -u $TRITON_SERVER_USER` -eq 1000 ] &&     [ `id -g $TRITON_SERVER_USER` -eq 1000 ]\n")
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream-6.1/samples samples/\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream-6.1/sources sources/\n")
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream/lib\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream/lib/libtritonserver.so .\n")
    for backend in backends:
        if (backend == nvidia_deepstream_backends.identity
                or backend == nvidia_deepstream_backends.onnxruntime
                or backend == nvidia_deepstream_backends.python
                or backend == nvidia_deepstream_backends.pytorch
                or backend == nvidia_deepstream_backends.tensorflow1
                or backend == nvidia_deepstream_backends.tensorflow2
                or backend == nvidia_deepstream_backends.tensorrt
                ):
            f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream/lib/triton_backends/{backend} /opt/nvidia/deepstream/deepstream/lib/triton_backends/{backend}\n")
    commands_to_jetson(f, light_tracker)
    add_run_and_add_commands(f, add, run)
    command_to_main_jetson(f)
    f.close()

def generate_triton_dockerfile(backends, run: str, add: str, docker_file_path: str, light_tracker: bool):
    f = open(docker_file_path, 'w')
    if light_tracker:
        commands_to_light_tracker_dgpu(f)
    f.write(f"FROM {DEEPSTREAM_DGPU_URL}triton AS full\n")
    f.write(f"FROM {DEEPSTREAM_DGPU_URL}base\n")
    f.write(f"ENV TRITON_SERVER_USER=triton-server\n")
    f.write(f"RUN userdel tensorrt-server > /dev/null 2>&1 || true &&     if ! id -u $TRITON_SERVER_USER > /dev/null 2>&1 ; then         useradd $TRITON_SERVER_USER;     fi &&     [ `id -u $TRITON_SERVER_USER` -eq 1000 ] &&     [ `id -g $TRITON_SERVER_USER` -eq 1000 ]\n")
    f.write(f"WORKDIR /opt/tritonserver\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/LICENSE .\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/TRITON_VERSION .\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/NVIDIA_Deep_Learning_Container_License.pdf .\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/bin bin/\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/lib lib/\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/include include/\n")
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1\n")
    f.write(f"RUN mkdir samples\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream-6.1/samples samples/\n")
    for backend in backends:
        f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/backends/{backend} /opt/tritonserver/backends/{backend}\n")
        f.write(f"RUN chown triton-server:triton-server /opt/tritonserver/backends\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/tritonserver/repoagents/checksum /opt/tritonserver/repoagents/checksum\n")
    f.write(f"RUN chown triton-server:triton-server /opt/tritonserver/repoagents\n")
    f.write(f"COPY --chown=1000:1000 --from=full /usr/bin/serve /usr/bin/.\n")
    f.write(f"WORKDIR /opt/nvidia\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/nvidia_entrypoint.sh .\n")
    f.write(f"WORKDIR /opt/nvidia/deepstream/deepstream-6.1\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream-6.1/entrypoint.sh .\n")
    f.write(f"COPY --chown=1000:1000 --from=full /opt/nvidia/deepstream/deepstream-6.1/sources .\n")
    f.write(f"COPY --chown=1000:1000 --from=full /usr/lib/x86_64-linux-gnu/libre2.so.5 /usr/lib/x86_64-linux-gnu/\n")
    f.write(f"COPY --chown=1000:1000 --from=full /usr/lib/x86_64-linux-gnu/libdcgm.so.2 /usr/lib/x86_64-linux-gnu/\n")
    commands_to_dgpu(f, light_tracker)
    add_run_and_add_commands(f, add, run)
    command_to_main(f)
    f.close()

def check_docker():
    try:
        s = subprocess.Popen('docker ps', stdout=subprocess.PIPE)
        output = s.stdout.readline()[:9].decode("utf-8")
        if output == 'CONTAINER':
            return True
        else:
            return False
    except OSError:
        typer.echo("Can't launch docker - is it installed?")
        return False

def provision_azure_resource(resource_group_name, resource_type, availability_func, provision_func, details):
    while True:
        # TODO: Enforce regex on the input for the given type of resource
        name = input(f"Enter a name for a {resource_type}. Either one that already exists (in the {resource_group_name} Resource Group) or one that you want to create:")
        availability_result = availability_func({"name": name})
        if not availability_result.name_available:
            yes_no = ""
            while yes_no.lower() not in ("y", "n", "yes", "no"):
                yes_no = input(f"That name either belongs to a {resource_type} that already exists or it is invalid. Do you want to use this {resource_type}? Try using this one (y/n):")
            if yes_no.lower() in ("n", "no"):
                print(f"Chosen name ({name}) is already taken. Please use another one.")
                continue
        try:
            print(f"Provisioning {resource_type}", end="", flush=True)
            poller = provision_func(resource_group_name, name, details)
            print("...", end="", flush=True)
            result = poller.result()
            print("Done!")
            return name
        except Exception as e:
            print(e)

@app.command()
def build(tag: str = typer.Option(..., help="We will name the built Docker image with this tag."),
          path: str = typer.Option(..., help="Path to the Dockerfile."),
          context: str = typer.Option(default=None, help="Build context to use for the Dockerfile. Should be a path to a folder. Defaults to the Dockerfile's folder."),
          no_cache: bool = typer.Option(False, help="If given, we build the Docker image without cache (passing in --no-cache to Docker build).")):

    # Check the Dockerfile path
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        typer.echo(f"Given {path} for --path, but it does not point to a Dockerfile.")
        return -1

    # Check the build context path
    if context is None:
        typer.echo(f"No --context given, attempting to default to the directory of the Dockerfile ({path})")
        context = os.path.dirname(path)
    else:
        context = os.path.abspath(context)

    if not os.path.isdir(context):
        typer.echo(f"Given {context} for --context, but should be a directory.")
        return -1

    # Check if Docker is installed and running
    docker_installed = check_docker()
    if not docker_installed:
        typer.echo("Please check if Docker is installed and the Docker daemon is running.")
        return -1

    # Run the build command
    cache_or_not = "--no-cache" if no_cache else ""
    docker_command = f"docker build -f {path} -t {tag} {cache_or_not} {context}"
    typer.echo(docker_command)
    return subprocess.run(docker_command, shell=True).returncode

@app.command()
def create(deepstream_image_type: nvidia_deepstream_images = typer.Option(default=nvidia_deepstream_images.samples, help="The type of DeepStream image to base the resulting image on."),
           device_type: nvidia_device_type = typer.Option(default=nvidia_device_type.dGPU, help="The target architecture to build for: dGPU (x86) or Jetson (ARM64)."),
           tag: str = typer.Option(..., help="The tag to use for the craeted image."),
           backend: Optional[List[nvidia_deepstream_backends]] = typer.Option(default=None, help="Backends to include if using Triton Inference Server. Each --backend argument is additive."),
           add: Optional[List[str]] = typer.Option(default=None, help='ADD commands to add to the Dockerfile we generate. Provide: SOURCE file path <space> DESTINATION folder path as a single string - example: "/home/source/folder/file /opt/nvidia/deepstream/deepstream-6.1/destination/folder/".'),
           run: Optional[List[str]] = typer.Option(default=None, help='RUN commands to add to the Dockerfile we generate.'),
           build_image: bool = typer.Option(default=True, help="If --build-image, we build the image based on the intermediate Dockerfile we generate. Otherwise we generate a Dockerfile but do not build its image."),
           build_dir: str = typer.Option(..., help="Provide file path of 'docker-build' folder under 'ds-ai-pipeline' code base. This is where docker file will be created"),
           force: bool = typer.Option(False, help="If --force is given, we will overwrite Dockerfile.custom if we find one already in the build directory. Otherwise, if one is present, we fail with a warning."),
           no_cache: bool = typer.Option(False, help="If given, we build the Docker image without cache (passing in --no-cache to Docker build)."),
           light_tracker: bool = typer.Option(False, help="If given, we build the Light Tracker libraries. This is needed in order to use Light Tracker.")):

    if not os.path.isdir(build_dir):
        typer.echo(f"Given --build-dir of {build_dir}, but it should be a directory.")
        return -1

    # Create the docker file path
    docker_file_path = os.path.join(os.path.abspath(build_dir), "Dockerfile.custom")

    # Check if we already have a generated dockerfile.
    if os.path.exists(docker_file_path) and not force:
        typer.echo(f"Dockerfile.custom already present at {docker_file_path}. Use --force to overwrite.")
        return -1

    if device_type == nvidia_device_type.Jetson and deepstream_image_type == nvidia_deepstream_images.triton:
        generate_triton_dockerfile_for_jetson(backend, run, add, docker_file_path, light_tracker)
    elif device_type == nvidia_device_type.Jetson and deepstream_image_type != nvidia_deepstream_images.triton:
        generate_deepstream_dockerfile_for_jetson(deepstream_image_type, run, add, docker_file_path, light_tracker)
    elif device_type == nvidia_device_type.dGPU and deepstream_image_type == nvidia_deepstream_images.triton:
        generate_triton_dockerfile(backend, run, add, docker_file_path, light_tracker)
    else:
        generate_deepstream_dockerfile(deepstream_image_type, run, add, docker_file_path, light_tracker)

    typer.echo(f"Docker file created at {docker_file_path}")

    if build_image:
        context = os.path.dirname(os.path.dirname(docker_file_path))  # Directory one up from Dockerfile's dir
        build(tag, docker_file_path, context, no_cache)

@app.command()
def push(image_name: str = typer.Option(...),
         container_registry: str = typer.Option(...),
         username: str = typer.Option(...),
         password: str = typer.Option(..., prompt=True, hide_input=True)):

    docker_login_cmd = f"docker login {container_registry} --username {username} --password={password}"
    proc = subprocess.run(docker_login_cmd, shell=True)
    if proc.returncode != 0:
        typer.echo(f"Got nonzero return code from docker login command: {proc.returncode}")
        typer.echo("Could not complete push command.")
        return -1

    new_image_name = f"{container_registry}/{image_name}"
    docker_tag_cmd = f"docker tag {image_name} {new_image_name}"
    typer.echo(docker_tag_cmd)
    proc = subprocess.run(docker_tag_cmd, shell=True)
    if proc.returncode != 0:
        typer.echo(f"Got nonzero return code from docker tag command: {proc.returncode}")
        typer.echo("Could not complete push command.")
        return -1

    docker_push_cmd = f"docker push {new_image_name}"
    typer.echo(docker_push_cmd)
    proc = subprocess.run(docker_push_cmd, shell=True)
    if proc.returncode != 0:
        typer.echo(f"Got nonzero return code from docker push command: {proc.returncode}")
        typer.echo("Could not complete push command.")
        return -1