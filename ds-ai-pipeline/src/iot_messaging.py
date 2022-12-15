from os.path import join
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst
from datetime import datetime
import ctypes
import json
import numpy as np
import pyds
import queue
import logging
import uuid
import cv2


UNTRACKED_OBJECT_ID = 0xffffffffffffffff

class IotMSGHelper:
    def __init__(self, nframes: int, msg_queue=queue.Queue) -> None:
        self.nframes = nframes
        self.msg_queue = msg_queue
        self.sgie_parsers = {}
        self.pgie_custom_msg = {}
        self.padindex_to_srcname=[]
        self.frame_size=(1,1)
        self.config_id=""
        self.data_to_save=None
        self.ncounter = 0
        self.VIDEO_UPLOADER_DIRECTORY=""
        self.regions_of_interest=[]
        self.video_writers=None

    def register_sgie_parser(self, sgie_id, sgi_parser):
        self.sgie_parsers[sgie_id] = sgi_parser

    def add_custom_msg_from_pgie(self, stream_index, frame_number, custom_msg):
        self.pgie_custom_msg[(stream_index, frame_number)] = custom_msg

    def collect_data_for_iot_hub(self, pad, info, u_data):
        pipe_data = u_data
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            return

        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        if not batch_meta: return Gst.PadProbeReturn.OK
        l_frame = batch_meta.frame_meta_list
        inferences = []
        frames_to_save={k:[] for k in self.padindex_to_srcname}
        # iterate over frames
        while l_frame is not None:
            try: frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration: continue

            frame_number = frame_meta.frame_num
            stream_index = frame_meta.pad_index
            frame_width = frame_meta.source_frame_width
            frame_height = frame_meta.source_frame_height

            if pipe_data.rec_file_name is not None:
                n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
                cpy_frame = np.array(n_frame, copy=False, order='C')
                key = self.padindex_to_srcname[stream_index]
                frames_to_save[key].append(cv2.cvtColor(cpy_frame, cv2.COLOR_RGBA2BGR))

            sourceInfo = {
                "id": self.padindex_to_srcname[stream_index],
                "timestamp": datetime.now().isoformat(),
                "width": frame_width,
                "height": frame_height,
                "frameId": frame_number
            }
            customInfo={}
            detectionInfo={}
            clsInfo={}

            # check for a pgie custom message
            if (stream_index, frame_number) in self.pgie_custom_msg.keys():
                customInfo["sourceInfo"]=sourceInfo
                customInfo["type"]="custom"
                customInfo["id"]=self.config_id
                customInfo["detections"] = [self.pgie_custom_msg[(stream_index, frame_number)]]
                inferences.append(customInfo)
                del self.pgie_custom_msg[(stream_index, frame_number)]

            # iterate over frame_user_meta_list
            l_user = frame_meta.frame_user_meta_list
            while l_user is not None:
                try: seg_user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                except StopIteration: break
                if seg_user_meta and seg_user_meta.base_meta.meta_type == pyds.NVDSINFER_SEGMENTATION_META:
                    try:
                        segmeta = pyds.NvDsInferSegmentationMeta.cast(seg_user_meta.user_meta_data)
                    except StopIteration: break

                    # TODO(otre99): collect all necessary data
                    #masks = pyds.get_segmentation_masks(segmeta)

                try: l_user = l_user.next
                except StopIteration: break

            # iterate over obj_meta_list
            l_obj = frame_meta.obj_meta_list
            obj_detections=[]
            W, H = self.frame_size
            while l_obj is not None:
                try: obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration: continue

                obj_detections.append(
                    {
                        "classId": obj_meta.class_id,
                        "confidence": obj_meta.confidence,
                        "rect": [obj_meta.rect_params.left/W, obj_meta.rect_params.top/H,
                                 obj_meta.rect_params.width/W, obj_meta.rect_params.height/H],
                        "label": obj_meta.obj_label,
                        "id": str(uuid.uuid4()),
                        "unique_component_id": obj_meta.unique_component_id,
                        "tracking_id": obj_meta.object_id if obj_meta.object_id  != UNTRACKED_OBJECT_ID else -1
                    }
                )

                l_cls = obj_meta.classifier_meta_list
                # iterate over classifier_meta_list
                while l_cls is not None:
                    try: cls_data = pyds.NvDsClassifierMeta.cast(l_cls.data)
                    except StopIteration: break

                    # TODO(otre99): find the way of reading classication info

                    try: l_cls = l_cls.next
                    except StopIteration: break

                l_user = obj_meta.obj_user_meta_list
                # iterate over obj_user_meta_list
                while l_user is not None:
                    try: user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                    except StopIteration: break

                    if user_meta.base_meta.meta_type == pyds.NvDsMetaType.NVDSINFER_TENSOR_OUTPUT_META:
                        tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                        sgieid = tensor_meta.unique_id
                        if sgieid in self.sgie_parsers.keys():
                            model_outputs = self.get_numpy_layers(tensor_meta)
                            obj_detections[-1]["customInfo"] = self.sgie_parsers[sgieid](self, model_outputs)

                    try: l_user = l_user.next
                    except StopIteration: break

                try: l_obj = l_obj.next
                except StopIteration: break

            detectionInfo["sourceInfo"]=sourceInfo
            detectionInfo["type"]="detection"
            detectionInfo["id"]=self.config_id
            detectionInfo["detections"]=obj_detections
            inferences.append(detectionInfo)

            try: l_frame = l_frame.next
            except StopIteration: break

        if pipe_data.rec_file_name is not None:
            if self.data_to_save is None:
                # start collecting data (json)
                self.data_to_save=[pipe_data.rec_file_name, inferences]

                # start collecting data (video)
                self.init_video_writers(pipe_data.rec_file_name, batch_meta)
                self.record_frames(dd=frames_to_save)
            else:
                if pipe_data.rec_file_name != self.data_to_save[0]:
                    # save collected data
                    self.save_pending_data()

                    # start collecting new data (json)
                    self.data_to_save=[pipe_data.rec_file_name, inferences]

                    # start collecting data (video)
                    self.init_video_writers(pipe_data.rec_file_name, batch_meta)
                    self.record_frames(dd=frames_to_save)
                else:
                    # continue collecting new data (json)
                    self.data_to_save[1]+=inferences
                    # continue collecting data (video)
                    self.record_frames(dd=frames_to_save)
        else:
            self.save_pending_data()

        #Put message in queue to send to IoT Hub
        if self.ncounter%self.nframes == 0:
            message={
                "schemaVersion": "0.1",
                "events": [],
                "regionsOfInterest": self.regions_of_interest,
                "inferences": inferences
            }
            self.msg_queue.put(message)
        self.ncounter+=1

        return Gst.PadProbeReturn.OK

    def record_frames(self, dd):
        keys = self.video_writers.keys()&dd.keys()
        for k in keys:
            for frame in dd[k]:
                self.video_writers[k].write(frame)

    def save_pending_data(self):
        self.save_pending_data_video()
        self.save_pending_data_json()

    def save_pending_data_json(self):
        if self.data_to_save is not None:
            fname, data = self.data_to_save
            fpath = self.VIDEO_UPLOADER_DIRECTORY + fname + ".json"
            message = {
                "schemaVersion": "0.1",
                "events": [],
                "regionsOfInterest": self.regions_of_interest,
                "inferences": data
            }
            with open(fpath, 'w') as f:
                f.write(json.dumps(message))
            self.data_to_save=None

    def save_pending_data_video(self):
        if self.video_writers is not None:
            for key in self.video_writers.keys():
                self.video_writers[key].release()
            self.video_writers = None

    def init_video_writers(self, fname, batch_meta):
        self.video_writers={}
        l_frame = batch_meta.frame_meta_list
        while l_frame is not None:
            try: frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration: continue
            stream_index = frame_meta.pad_index
            key  =  self.padindex_to_srcname[stream_index]
            if len(self.padindex_to_srcname)==1:
                file_path = join(self.VIDEO_UPLOADER_DIRECTORY,  fname+".mp4")
            else:
                file_path = join(self.VIDEO_UPLOADER_DIRECTORY,  fname+"_"+key+".mp4")
            #fourcc = cv2.VideoWriter_fourcc('m','p', '4', 'v')
            #fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            fps = 30
            self.video_writers[key] = cv2.VideoWriter(file_path, fourcc, fps, self.frame_size)
            failed = not self.video_writers[key].isOpened()

            if failed == False:
                logging.info("New video: {}".format(file_path))
            else:
                logging.warn("Error. VideoWriter() failed to create the video file '{}' for writing".format(file_path))
                del self.video_writers[key]

            try: l_frame = l_frame.next
            except StopIteration: break
        if len(self.video_writers)==0:
            self.video_writers=None

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

            dims = np.trim_zeros(layer.dims.d, 'b')
            ptr = ctypes.cast(pyds.get_ptr(layer.buffer), ctypes.POINTER(dtype))
            arr = np.ctypeslib.as_array(ptr, shape=dims)
            result[layer.layerName] = arr.copy() if arr is not None else None
        return result

if __name__ == "__main__":
    pass
