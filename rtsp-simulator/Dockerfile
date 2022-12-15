# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# Other option is arm64
ARG ARCH=amd64

# if AMD64
FROM nvcr.io/nvidia/deepstream:6.1.1-samples AS deepstream-container-amd64
FROM ubuntu:18.04 AS base-amd64
COPY --from=deepstream-container-amd64 /opt/nvidia/deepstream/deepstream/samples/streams/ /live/mediaServer/media/
# else if ARM64
FROM nvcr.io/nvidia/deepstream-l4t:6.1.1-samples AS deepstream-container-arm64
FROM ubuntu:18.04 AS base-arm64
COPY --from=deepstream-container-arm64 /usr/bin/qemu-aarch64-static /usr/bin/
COPY --from=deepstream-container-arm64 /opt/nvidia/deepstream/deepstream/samples/streams/ /live/mediaServer/media/
# fi

FROM base-${ARCH}
COPY ./videos/ /live/mediaServer/media/
COPY ./DynamicRTSPServer.patch /

# Change all video files to MKV files then compile
RUN apt-get update && \
    apt-get install -y ffmpeg dos2unix && \
    rm /live/mediaServer/media/*.jpg && \
    for file in /live/mediaServer/media/*; do filename=$(basename -- "$file"); extension="${filename##*.}"; filename="${filename%.*}"; ffmpeg -i "$file" -c copy /live/mediaServer/media/"$filename".mkv; done && \
    rm /live/mediaServer/media/*.mp4 && \
    # A few of the videos do not survive being converted from mp4. Remove them
    rm /live/mediaServer/media/sample_720p.mkv && \
    rm /live/mediaServer/media/sample_qHD.mkv && \
    rm /live/mediaServer/media/sonyc_mixed_audio.mkv && \
    rm /live/mediaServer/media/sonyc_mixed_audio.wav && \
    dos2unix /DynamicRTSPServer.patch && \
    apt-get purge -y --auto-remove ffmpeg dos2unix && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends make build-essential wget libssl-dev && \
    wget http://www.live555.com/liveMedia/public/live555-latest.tar.gz && \
    tar -xzf live555-latest.tar.gz && \
    rm live555-latest.tar.gz && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    cd live && \
    cp /DynamicRTSPServer.patch ./ && \
    patch -u /live/mediaServer/DynamicRTSPServer.cpp -i ./DynamicRTSPServer.patch && \
    ./genMakefiles linux && \
    make && \
    apt-get purge -y --auto-remove gcc libc6-dev make

WORKDIR /live/mediaServer

EXPOSE 554

ENTRYPOINT [ "./live555MediaServer" ]