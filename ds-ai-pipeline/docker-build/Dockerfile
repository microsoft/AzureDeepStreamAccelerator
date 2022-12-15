# Build Light Tracker's library and Light Detector's custom parser
FROM nvcr.io/nvidia/deepstream:6.1.1-devel as base
RUN apt-get update -y && apt-get install -y build-essential cmake libeigen3-dev
COPY src/lighttrack_source /tmp/lighttrack_source
WORKDIR /tmp/lighttrack_source/lightmot
RUN cmake . && make -j4
WORKDIR /tmp/lighttrack_source/lightdet
RUN cmake . && make -j4

# Do our application
FROM nvcr.io/nvidia/deepstream:6.1.1-samples

COPY src/requirements.amd.txt /
COPY src/aptpkgs.amd.txt /

WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps

RUN git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps && \
    apt-get update && \
    apt-get install -y dos2unix && \
    dos2unix /aptpkgs.amd.txt && \
    dos2unix /requirements.amd.txt && \
    apt-get install -y $(cat /aptpkgs.amd.txt) && \
    # Some packages are broken in the latest release of DeepStream
    apt-get --reinstall install libavcodec58 libavutil56 && \
    # Pip installs
    python3 -m pip install --upgrade pip && \
    pip3 install -r /requirements.amd.txt && \
    wget https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.4/pyds-1.1.4-py3-none-linux_x86_64.whl && \
    pip3 install pyds-1.1.4-py3-none-linux_x86_64.whl && \
    # Make our application folder
    mkdir -p /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline

WORKDIR /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline
COPY src .

# Light Tracker installation
COPY --from=base /tmp/lighttrack_source/lightmot/liblightmot.so /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/
COPY --from=base /tmp/lighttrack_source/lightdet/liblightdet.so /opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/

#####################
### Remove codecs ###
#####################
RUN apt-get update && apt-get remove -y \
    gstreamer1.0-alsa \
    && \
    rm \
        /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstdtsdec.so \
        /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstvpx.so \
        /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstaom.so
#####################

CMD python3 main.py