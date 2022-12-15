from .yolov4_parser import Yolov4Parser
from .yolov3_parser import Yolov3Parser
from .ssd_mobilenet_v1 import SSDMobilenetV1
from .body_pose_parser import BodyPoseParser2D
from .user_parser import UserParser
import sys 
import importlib
import os 

def create_parser_from_user_pyfile(pyFile):
    try:
        sys.path.append(os.path.dirname(pyFile))
        m = importlib.import_module(os.path.basename(pyFile).split(".")[0])        
        uparser = UserParser(user_funct=m)
    except Exception as e:
        print("Error creating parser from user pyfile: {}".format(e))
        return None
    return uparser

def create_sgie_parser_from_user_pyfile(pyFile):

    try:
        sys.path.append(os.path.dirname(pyFile))
        m = importlib.import_module(os.path.basename(pyFile).split(".")[0])        
        sgie_id = m.gie_unique_id
        parse_sgie_model = m.parse_sgie_model
    except Exception as e:
        print("Error creating parser from user pyfile: {}".format(e))
        return None, None
    return sgie_id, parse_sgie_model

def get_parser_by_name(parser_name: str):
    if parser_name == "yolov4":
        return Yolov4Parser()

    if parser_name in ("tiny_yolov3"):
        return Yolov3Parser()
    
    if parser_name == "ssd_mobilenet_v1":
        return SSDMobilenetV1()

    if parser_name == "bodypose2d":
        return BodyPoseParser2D()

    return None 

def get_available_parsers():
    return ["yolov4", "tiny-yolov3", "ssd_mobilenet_v1", "bodypose2d"]