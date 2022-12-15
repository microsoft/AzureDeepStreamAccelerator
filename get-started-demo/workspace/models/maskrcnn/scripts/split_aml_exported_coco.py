#!/usr/bin/env python
import argparse
import os
import os.path as osp
import sys
import collections
import datetime
import shutil
from random import sample, seed
import glob
import json

def read_coco_file(coco_file):
    with open(coco_file) as f_in:
        return json.load(f_in)

def prepare_image_lists(input_dir, input_coco_data, split_pct):

    categories = {}  
    file_count = len(input_coco_data["images"])
    print(f"No. of files = {file_count}")

    # get categories: class_id and class name
    for i in range(0, len(coco_data["categories"])):
        categories[coco_data["categories"][i]["id"]] = coco_data["categories"][i]["name"]
        ca_id = categories[coco_data["categories"][i]["id"]]
        # print(f"id[{i}], categories id = {ca_id}")

    # base set of files    
    img_files = [i for i in os.listdir(input_dir) if i.endswith('.jpg') or i.endswith('.png')]
    copy_files = img_files.copy()

    # determine which files go to which location
    seed(42) # set random seed for reproducibility
    train_count = int(round(split_pct * len(img_files), 0))
    test_val_count = len(img_files) - train_count

    val_count = int((test_val_count+1)/2)
    test_count = test_val_count - val_count

    # filter the training files
    test_val_files = sample(img_files, test_val_count)
    train_files = [i for i in img_files if i not in test_val_files]    

    # val_files
    val_files = sample(test_val_files, val_count)
    #test_files
    test_files = [i for i in test_val_files if i not in val_files]


    # make sure we didn't lose anything
    assert len(train_files) + len(test_val_files) == len(copy_files)
    assert file_count == len(copy_files)

    return (train_files, val_files, test_files, categories)
    # return
 
def copy_files_to_dir(input_dir, output_dir, file_lst):
    for f in file_lst:
        src_file = os.path.join(input_dir, f)
        target_file = os.path.join(output_dir, f)       
        shutil.copyfile(src_file, target_file)

def prepare_output_directories(output_dir_path):
    output_dirs = ['train', 'val', 'test']
    for d in output_dirs:
        target_dir = os.path.join(output_dir_path, d)        
        if not os.path.exists(target_dir):
            print(f"Creating directory: {target_dir}")
            os.makedirs(target_dir)

        image_dir = os.path.join(target_dir, 'images') 
        if not os.path.exists(image_dir):
            print(f"Creating directory: {image_dir}")
            os.makedirs(image_dir)

def create_coco_info():
    now = datetime.datetime.now()
    info=dict(
        description="null",
        url="null",
        version="null",
        year=now.year,
        contributor="null",
        date_created=now.strftime("%Y-%m-%d %H:%M:%S.%f"),
    )

    # print(f"info = {info}")
    return info

def create_coco_categories(coco_data):
    class_name_to_id = {}
    coco_categories = []
    for i in range(0, len(coco_data["categories"])):
        class_name = coco_data["categories"][i]["name"]
        class_id = coco_data["categories"][i]["id"]

        class_name_to_id[class_name] = class_id
        categories[coco_data["categories"][i]["id"]] = class_name

        coco_categories.append(
            dict(supercategory="null", id=class_id, name=class_name,)
        )

    # print(f"categories = {coco_categories}")
    return coco_categories, class_name_to_id

def create_coco_images_annotations(coco_data, train_files, val_files, test_files):

    exclude_files = val_files + test_files
    print(f"exclude_files = {exclude_files}")

    coco_images_train = []
    coco_images_val = []
    coco_images_test = []
    coco_val_ids = []
    coco_test_ids = []

    for i in range(0, len(coco_data["images"])):
        coco_file_name = coco_data["images"][i]["file_name"]
        index = coco_file_name.rfind('/')
        current_name = coco_file_name[(index+1):]
        # print(f"current_name[{i}] = {current_name}")
        current_id = coco_data["images"][i]["id"]

        _id = current_id
        _license=0
        _url="null"
        _file_name = current_name
        _width=int(coco_data["images"][i]["width"])
        _height=int(coco_data["images"][i]["height"])
        _coco_url = coco_data["images"][i]["coco_url"]
        _date_captured = coco_data["images"][i]["date_captured"]

        if current_name not in exclude_files:
            # print(f"export filename[{i}] = {coco_file_name},")
            coco_images_train.append(
                dict(id=_id, license=_license, url=_url, file_name=_file_name, width=_width, height=_height, coco_url=_coco_url, date_captured=_date_captured,)
                )
        # for val
        elif current_name in val_files:
            coco_images_val.append(
                dict(id=_id, license=_license, url=_url, file_name=_file_name, width=_width, height=_height, coco_url=_coco_url, date_captured=_date_captured,)
                )
            coco_val_ids.append(current_id)
        # for test
        elif current_name in test_files:
            coco_images_test.append(
                dict(id=_id, license=_license, url=_url, file_name=_file_name, width=_width, height=_height, coco_url=_coco_url, date_captured=_date_captured,)
                )
            coco_test_ids.append(current_id)
    # print(f"coco_images_val = {coco_images_val}")
    # print(f"coco_images_test = {coco_images_test}")

    # create coco annotation format
    coco_ann_train, coco_ann_val, coco_ann_test = create_coco_annotation(coco_data, train_files, coco_val_ids, coco_test_ids)
    # print(f"coco_annotations_val = {coco_ann_val}")

    return coco_images_train, coco_ann_train, coco_images_val, coco_ann_val, coco_images_test, coco_ann_test

def create_coco_annotation(coco_data, train_files, coco_val_ids, coco_test_ids):
    coco_annotations_train = []
    coco_annotations_val = []
    coco_annotations_test = []
    exclude_ids = coco_val_ids + coco_test_ids
    print(f"exclude_ids = {exclude_ids}")

    for i in range(0, len(coco_data["annotations"])):
        current_id = coco_data["annotations"][i]["image_id"]

        _id = coco_data["annotations"][i]["id"]
        _segmentation = coco_data["annotations"][i]["segmentation"]               
#        _segmentation = [0.0,0.0,0.0]                  
        _image_id = coco_data["annotations"][i]["image_id"]
        _category_id= coco_data["annotations"][i]["category_id"]
        _area = coco_data["annotations"][i]["area"]
        _bbox = coco_data["annotations"][i]["bbox"]
        _iscrowd = 0

        if current_id not in exclude_ids:           
            coco_annotations_train.append(
                dict(id=_id, segmentation=_segmentation, image_id=_image_id, category_id=_category_id, area=_area, bbox=_bbox, iscrowd=_iscrowd,)
            )
        # for val
        elif current_id in coco_val_ids:
            coco_annotations_val.append(
                dict(id=_id, segmentation=_segmentation, image_id=_image_id, category_id=_category_id, area=_area, bbox=_bbox, iscrowd=_iscrowd,)
            )
        # for test
        elif current_id in coco_test_ids:
            coco_annotations_test.append(
                dict(id=_id, segmentation=_segmentation, image_id=_image_id, category_id=_category_id, area=_area, bbox=_bbox, iscrowd=_iscrowd,)
            )

    return coco_annotations_train, coco_annotations_val, coco_annotations_test

def export_annotation_coco(output_dir, train_files, val_files, test_files, coco_data):

    now = datetime.datetime.now()

    coco_categories, class_name_to_id = create_coco_categories(coco_data)
    coco_images_train, coco_ann_train, coco_images_val, coco_ann_val, coco_images_test, coco_ann_test = create_coco_images_annotations(coco_data, train_files, val_files, test_files)

    # for train
    data_train = dict(
        info=create_coco_info(),
        licenses=[dict(url=None, id=0, name=None,)],
        images = coco_images_train,
        annotations = coco_ann_train,
        categories = coco_categories,
    )
    # output annotations.json on train
    out_train_dir = os.path.join(output_dir, "train")        
    annotation_train_file = osp.join(out_train_dir, "annotations.json")
    with open(annotation_train_file, "w") as f_train:
        json.dump(data_train, f_train)

    # for val
    data_val = dict(
        info=create_coco_info(),
        licenses=[dict(url=None, id=0, name=None,)],
        images = coco_images_val,
        annotations = coco_ann_val,
        categories = coco_categories,
    )
    # output annotations.json on val folder
    out_val_dir = os.path.join(output_dir, "val")        
    annotation_val_file = osp.join(out_val_dir, "annotations.json")
    with open(annotation_val_file, "w") as f_val:
        json.dump(data_val, f_val)

    # for test
    data_test = dict(
        info=create_coco_info(),
        licenses=[dict(url=None, id=0, name=None,)],
        images = coco_images_test,
        annotations = coco_ann_test,
        categories = coco_categories,
    )
    # output annotations.json on test folder
    out_test_dir = os.path.join(output_dir, "test")        
    annotation_test_file = osp.join(out_test_dir, "annotations.json")
    with open(annotation_test_file, "w") as f_test:
        json.dump(data_test, f_test)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations_file", help="path to coco annotations file exported from Azure Machine Learning")
    parser.add_argument("--input_dir", help="path to input directory of images")
    parser.add_argument("--output_dir", help="path to output directory to write split datasets")
    parser.add_argument('--train_pct', help="Percentage represented as decimal for how to split dat into train and validation set", type=float,default=.8)
    args = parser.parse_args()
    return args

# ----------------------------------------
if __name__ == "__main__":
    args = parse_args()

    print(args.annotations_file)
    print(args.input_dir)
    print(args.output_dir)
    print(args.train_pct)
 
    input_file = args.annotations_file
    input_dir = args.input_dir
    output_dir = args.output_dir
    TRAIN_PCT = args.train_pct
    print(f"train pct = {TRAIN_PCT}") 
    print(f"\n output_dir={output_dir}")

    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)

    prepare_output_directories(output_dir)

    coco_data = read_coco_file(input_file)
    # print(f"coco data = {coco_data}")

    # train_files, val_files, test_files
    (train_files, val_files, test_files, categories) = prepare_image_lists(input_dir, coco_data, TRAIN_PCT)

    print(f"Training image count: {len(train_files)}")
    print(f"Validation image count: {len(val_files)}")
    print(f"Testing image count: {len(test_files)}")
    # print(f"Validation images ={val_files}")
    # print(f"Testing images = {test_files}")

    train_dir_path = os.path.join(output_dir, "train/images")
    val_dir_path = os.path.join(output_dir, "val/images")
    test_dir_path = os.path.join(output_dir, "test/images")

    copy_files_to_dir(input_dir, train_dir_path, train_files)
    copy_files_to_dir(input_dir, val_dir_path, val_files)
    copy_files_to_dir(input_dir, test_dir_path, test_files)    

    # export annotation file
    export_annotation_coco(output_dir, train_files, val_files, test_files, coco_data)
