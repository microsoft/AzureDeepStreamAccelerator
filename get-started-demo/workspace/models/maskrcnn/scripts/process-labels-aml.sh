#!/usr/bin/env bash
#PWD="$(pwd)"
PWD=$PROJECT_DIR
# BASE_DIR="${PWD}/workspace/data/inputs"

OUT_DIR="${PWD}/data/split-images"
TRAIN_DIR="${OUT_DIR}/train"
VAL_DIR="${OUT_DIR}/val"
TEST_DIR="${OUT_DIR}/test"

echo $PWD
echo $TRAIN_DIR
echo $VAL_DIR
echo $TEST_DIR

echo "Cloning Tensorflow models directory (for conversion utilities)"
if [ ! -e tf-models ]; then
  git clone http://github.com/tensorflow/models tf-models
fi

echo $(pwd)
(cd tf-models/research && protoc object_detection/protos/*.proto --python_out=.)

echo $PWD
echo $(pwd)
# Setup packages
touch tf-models/__init__.py
touch tf-models/research/__init__.py

TRAIN_IMAGE_DIR="${TRAIN_DIR}/images"
VAL_IMAGE_DIR="${VAL_DIR}/images"
TEST_IMAGE_DIR="${TEST_DIR}/images"

TRAIN_COCO_ANNOTATION_FILE="${TRAIN_DIR}/annotations.json"
VAL_ANNOTATION_FILE="${VAL_DIR}/annotations.json"
TESTDEV_ANNOTATION_FILE="${TEST_DIR}/annotations.json"

echo $TRAIN_IMAGE_DIR
echo $VAL_IMAGE_DIR
echo $TEST_IMAGE_DIR
echo "---Annotation files---"
echo $TRAIN_COCO_ANNOTATION_FILE
echo $VAL_ANNOTATION_FILE
echo $TESTDEV_ANNOTATION_FILE

OUTPUT_DIR="${OUT_DIR}/tfrecords"

echo "output folder:"
echo $OUTPUT_DIR

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

echo $SCRIPT_DIR

PYTHONPATH="tf-models:tf-models/research" python $SCRIPT_DIR/create_coco_tf_record.py \
  --logtostderr \
  --include_masks \
  --train_image_dir="${TRAIN_IMAGE_DIR}" \
  --val_image_dir="$VAL_IMAGE_DIR" \
  --test_image_dir="${TEST_IMAGE_DIR}" \
  --train_object_annotations_file="${TRAIN_COCO_ANNOTATION_FILE}" \
  --val_object_annotations_file="${VAL_ANNOTATION_FILE}" \
  --testdev_annotations_file="${TESTDEV_ANNOTATION_FILE}" \
  --output_dir="${OUTPUT_DIR}" \