from cgi import print_arguments
import gi
gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

import pyds
import numpy as np
import ctypes
import logging

UNTRACKED_OBJECT_ID = 0xffffffffffffffff

class BoundingBox:
    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0, class_id: int = 0, score: float = 0) -> None:
        self.x=x
        self.y=y
        self.w=w
        self.h=h
        self.class_id=class_id
        self.score=score

class BaseCustomParser:
    DET_MODEL = 0
    CUSTOM_MODEL = 1   
    def __init__(self, model_type: int, name: str, msg_helper=None) -> None:
        self.model_type = model_type
        self.name = name

        self.network_size=(-1,-1)
        self.image_size=(-1,-1)
        self.labels = []
        self.det_th = 0.5        
        self.mns_th = 0.213
        self.msg_helper = msg_helper

    def get_name(self):
        return self.name

    def parse_det_model(self, raw_outputs: dict):       
        pass 

    def parse_custom_model(self, raw_outputs: dict):
        pass

    def add_custom_to_meta(self, outputs, batch_meta, frame_meta):
        pass

    def pgie_src_pad_buffer_probe(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        
        if not gst_buffer:
            print("Unable to get GstBuffer ")
            return
    
        # Retrieve batch metadata from the gst_buffer
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        l_frame = batch_meta.frame_meta_list

        # iterate through the frames    
        while l_frame is not None:
            try: frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration: break
    
            frame_number = frame_meta.frame_num
            stream_index = frame_meta.pad_index

            l_user = frame_meta.frame_user_meta_list
            while l_user is not None:
                try: user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                except StopIteration: break
                if user_meta.base_meta.meta_type != pyds.NvDsMetaType.NVDSINFER_TENSOR_OUTPUT_META: 
                    try: l_user = l_user.next
                    except StopIteration: break
                    continue               

                tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                raw_outputs = self.get_numpy_layers(tensor_meta=tensor_meta) 

                # process detection model 
                if self.model_type == BaseCustomParser.DET_MODEL:
                    detections, custom_msg = self.parse_det_model(raw_outputs=raw_outputs)
                    # passing custom message to IotMSGHelper
                    if custom_msg and self.msg_helper:
                        self.msg_helper.add_custom_msg_from_pgie(stream_index, frame_number, custom_msg)
                    self.add_detections_to_meta(detections=detections, batch_meta=batch_meta, frame_meta=frame_meta, labels=self.labels)
                
                elif self.model_type == BaseCustomParser.CUSTOM_MODEL:
                    outputs, custom_msg = self.parse_custom_model(raw_outputs=raw_outputs)                    
                    # passing custom message to IotMSGHelper
                    if custom_msg and self.msg_helper:
                        self.msg_helper.add_custom_msg_from_pgie(stream_index, frame_number, custom_msg)
                    self.add_custom_to_meta(outputs, batch_meta, frame_meta)


                try: l_user = l_user.next
                except StopIteration: break
       
            try: 
                frame_meta.bInferDone = True
                l_frame = l_frame.next
            except StopIteration: break
        return Gst.PadProbeReturn.OK

    @staticmethod
    def add_detections_to_meta(detections, labels, batch_meta, frame_meta):
        """ Inserts an object into the metadata """
        # this is a good place to insert objects into the metadata.

        for obj in detections:
            obj_meta = pyds.nvds_acquire_obj_meta_from_pool(batch_meta)
            # Set bbox properties. These are in input resolution.
            rect_params = obj_meta.rect_params
            rect_params.left   = obj.x
            rect_params.top    = obj.y
            rect_params.width  = obj.w
            rect_params.height = obj.h

            # Set object info including class, detection confidence, etc.
            obj_meta.confidence = obj.score
            obj_meta.class_id = obj.class_id
    
            # There is no tracking ID upon detection. The tracker will assign an ID.
            obj_meta.object_id = UNTRACKED_OBJECT_ID

            if not 0 <= obj.class_id < len(labels):
                logging.warning("CustomParser. Warning: class_id has wrong value!")
                obj_meta.obj_label = "---"
            else:    
                obj_meta.obj_label = labels[obj.class_id]

            # Semi-transparent yellow backgroud
            rect_params.has_bg_color = 0
            rect_params.bg_color.set(1, 1, 0, 0.4)
    
            # Red border of width 3
            rect_params.border_width = 3
            rect_params.border_color.set(1, 0, 0, 1)
    
    
            # Set display text for the object.
            txt_params = obj_meta.text_params
            if txt_params.display_text:
                pyds.free_buffer(txt_params.display_text)
    
            txt_params.x_offset = int(rect_params.left)
            txt_params.y_offset = max(0, int(rect_params.top) - 10)
            txt_params.display_text = obj_meta.obj_label + " " + "{:04.3f}".format(obj.score)

            # Font , font-color and font-size
            txt_params.font_params.font_name = "Serif"
            txt_params.font_params.font_size = 10
            # set(red, green, blue, alpha); set to White
            txt_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

            # Text background color
            txt_params.set_bg_clr = 1
            # set(red, green, blue, alpha); set to Black
            txt_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
    
            # Inser the object into current frame meta
            # This object has no parent
            pyds.nvds_add_obj_meta_to_frame(frame_meta, obj_meta, None)

    @staticmethod
    def get_numpy_layers(tensor_meta):
        result={}
        for i in range(tensor_meta.num_output_layers):
            layer = pyds.get_nvds_LayerInfo(tensor_meta, i)

            dtype=None
            if layer.dataType == 0: dtype = ctypes.c_float
            elif layer.dataType == 2: dtype = ctypes.c_int8
            elif layer.dataType == 3: dtype = ctypes.c_int32           
            else: return None 

            dims = np.trim_zeros(layer.dims.d, 'b') #.tolist()
            ptr = ctypes.cast(pyds.get_ptr(layer.buffer), ctypes.POINTER(dtype))
            arr = np.ctypeslib.as_array(ptr, shape=dims)
            result[layer.layerName] = arr.copy() if arr is not None else None            
        return result