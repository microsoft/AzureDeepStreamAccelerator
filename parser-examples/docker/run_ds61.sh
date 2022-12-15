#!/bin/sh

docker run --gpus=all --rm -ti --name=ds61 -e TERM\
    -v ${PWD}:${PWD} -w ${PWD}\
    ds61 "$@"

