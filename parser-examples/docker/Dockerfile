FROM	nvcr.io/nvidia/deepstream:6.1-triton

ENV  	DEBIAN_FRONTEND noninteractive

RUN	apt-get install --no-install-recommends -y python3-cairo python3-scipy python3-yaml python3-pip
RUN	pip3 install -U pip 
RUN	pip3 install onnx==1.10.2
COPY	pyds-1.1.1-py3-none-linux_x86_64.whl /tmp/
RUN	pip3 install /tmp/pyds-1.1.1-py3-none-linux_x86_64.whl && /bin/rm -r -f /tmp/pyds-1.1.1-py3-none-linux_x86_64.whl
RUN	ln -sf deepstream /opt/nvidia/deepstream/deepstream-6.0
