from collections import defaultdict
import sys

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

import pyds
import numpy as np
import ctypes

UNTRACKED_OBJECT_ID = 0xffffffffffffffff

def layer2array(layer):
    #print('layer2array', layer.layerName, layer.dataType, layer.dims.d)
    if 0 == layer.dataType:
        c_type = ctypes.c_float
    elif 3 == layer.dataType:
        c_type = ctypes.c_int32

    dims = np.trim_zeros(layer.dims.d, 'b').tolist()
    ptr = ctypes.cast(pyds.get_ptr(layer.buffer), ctypes.POINTER(c_type))
    if ptr:
        return np.ctypeslib.as_array(ptr, shape=dims)
    return None

class GSListIter:
    def __init__(self, gslist):
        self.front = gslist

    def __iter__(self):
        return self

    def __next__(self):
        ret = self.front
        if ret is None:
            raise StopIteration
        self.front = ret.next
        return ret

def bus_call(bus, message, loop):
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t==Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        sys.stderr.write("Warning: %s: %s\n" % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    return True

def make_elm_or_print_err(factoryname, name, printedname='', detail=""):
    """ Creates an element with Gst Element Factory make.
        Return the element  if successfully created, otherwise print
        to stderr and return None.
    """
    print("Creating", name)
    elm = Gst.ElementFactory.make(factoryname, name)
    if not elm:
        print("Unable to create " + printedname + " \n")
        if detail:
            print(detail)
    return elm

class sgie_src_pad_buffer_probe:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __call__(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            print("Unable to get GstBuffer ")
            return
    
        # Retrieve batch metadata from the gst_buffer
        # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
        # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
        self.pipeline.batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

        for l_frame in GSListIter(self.pipeline.batch_meta.frame_meta_list):
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)

            for l_obj in GSListIter(frame_meta.obj_meta_list):
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                for obj_user in GSListIter(obj_meta.obj_user_meta_list):
                    user_meta = pyds.NvDsUserMeta.cast(obj_user.data)
                    tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                    layers_info = [pyds.get_nvds_LayerInfo(tensor_meta, i)
                                   for i in range(tensor_meta.num_output_layers)]

                    outputs = self.pipeline.parser(layers_info)
                    self.pipeline.add_meta_to_frame(frame_meta, outputs)
                    
        return Gst.PadProbeReturn.OK

class pgie_src_pad_buffer_probe:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __call__(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            print("Unable to get GstBuffer ")
            return
    
        # Retrieve batch metadata from the gst_buffer
        # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
        # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
        self.pipeline.batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

        for l_frame in GSListIter(self.pipeline.batch_meta.frame_meta_list):
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)

            for l_user in GSListIter(frame_meta.frame_user_meta_list):
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                tensor_meta = pyds.NvDsInferTensorMeta.cast(user_meta.user_meta_data)
                layers_info = [pyds.get_nvds_LayerInfo(tensor_meta, i)
                               for i in range(tensor_meta.num_output_layers)]

                outputs = self.pipeline.parser(layers_info)
                self.pipeline.add_meta_to_frame(frame_meta, outputs)
                    
        return Gst.PadProbeReturn.OK

class osd_sink_pad_buffer_probe:
    def __init__(self, pipeline):
        self.pipeline = pipeline

    def __call__(self, pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            print("Unable to get GstBuffer ")
            return

        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

        for l_frame in GSListIter(batch_meta.frame_meta_list):
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            self.pipeline.dump_objects(frame_meta)

        return Gst.PadProbeReturn.OK

class TAOPipeline:
    def __init__(self, config, image_width=1280, image_height=720):
        # array of str names
        self.config = config
        self.image_width = image_width
        self.image_height = image_height
        
    def parser(self, layers_info):
        return []

    def add_meta_to_frame(self, frame_meta, outputs):
        pass

    def dump_objects(self, frame_meta):
        pass

    def run(self, input_video_name, output_video_name):
        #GObject.threads_init()
        Gst.init(None)
        pipeline = Gst.Pipeline()
        if not pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")

        source = make_elm_or_print_err("filesrc", "file-source")

        # Since the data format in the input file is elementary h264 stream,
        # we need a h264parser
        h264parser = make_elm_or_print_err("h264parse", "h264-parser")

        # Use nvdec_h264 for hardware accelerated decode on GPU
        decoder = make_elm_or_print_err("nvv4l2decoder", "nvv4l2-decoder")

        # Create nvstreammux instance to form batches from one or more sources.
        streammux = make_elm_or_print_err("nvstreammux", "Stream-muxer")

        pgie = make_elm_or_print_err('nvinfer', 'pgie')
        pgie.set_property("config-file-path", self.config)

        # Use convertor to convert from NV12 to RGBA as required by nvosd
        nvvidconv = make_elm_or_print_err("nvvideoconvert", "convertor")

        # Create OSD to draw on the converted RGBA buffer
        nvosd = make_elm_or_print_err("nvdsosd", "onscreendisplay", "OSD (nvosd)")

        nvvidconv2 = make_elm_or_print_err("nvvideoconvert", "convertor2")

        capsfilter = make_elm_or_print_err("capsfilter", "capsfilter")

        caps = Gst.Caps.from_string("video/x-raw, format=I420")
        capsfilter.set_property("caps", caps)

        # On Jetson, there is a problem with the encoder failing to initialize
        # due to limitation on TLS usage. To work around this, preload libgomp.
        # Add a reminder here in case the user forgets.
        preload_reminder = "If the following error is encountered:\n" + \
                           "/usr/lib/aarch64-linux-gnu/libgomp.so.1: cannot allocate memory in static TLS block\n" + \
                           "Preload the offending library:\n" + \
                           "export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1\n"
        encoder = make_elm_or_print_err("avenc_mpeg4", "encoder")

        encoder.set_property("bitrate", 2000000)

        codeparser = make_elm_or_print_err("mpeg4videoparse", "mpeg4-parser")

        container = make_elm_or_print_err("qtmux", "qtmux")

        sink = make_elm_or_print_err("filesink", "filesink")

        sink.set_property("location", output_video_name)
        sink.set_property("sync", 0)
        sink.set_property("async", 0)

        print("Playing file %s "%input_video_name)
        source.set_property("location", input_video_name)
        streammux.set_property("width", self.image_width)
        streammux.set_property("height", self.image_height)
        streammux.set_property("batch-size", 1)
        streammux.set_property("batched-push-timeout", 4000000)

        print("Adding elements to Pipeline \n")
        pipeline.add(source)
        pipeline.add(h264parser)
        pipeline.add(decoder)
        pipeline.add(streammux)
        pipeline.add(pgie)
        pipeline.add(nvvidconv)
        pipeline.add(nvosd)
        pipeline.add(nvvidconv2)
        pipeline.add(capsfilter)
        pipeline.add(encoder)
        pipeline.add(codeparser)
        pipeline.add(container)
        pipeline.add(sink)

        # we link the elements together
        # file-source -> h264-parser -> nvh264-decoder ->
        # nvinfer -> nvvidconv -> nvosd -> video-renderer
        print("Linking elements in the Pipeline \n")
        source.link(h264parser)
        h264parser.link(decoder)
        sinkpad = streammux.get_request_pad("sink_0")
        if not sinkpad:
            sys.stderr.write(" Unable to get the sink pad of streammux \n")
        srcpad = decoder.get_static_pad("src")
        if not srcpad:
            sys.stderr.write(" Unable to get source pad of decoder \n")
        srcpad.link(sinkpad)
        streammux.link(pgie)
        pgie.link(nvvidconv)
        nvvidconv.link(nvosd)
        nvosd.link(nvvidconv2)
        nvvidconv2.link(capsfilter)
        capsfilter.link(encoder)
        encoder.link(codeparser)
        codeparser.link(container)
        container.link(sink)

        # create an event loop and feed gstreamer bus mesages to it
        loop = GLib.MainLoop()
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # Add a probe on the primary-infer source pad to get inference output tensors

        # Lets add probe to get informed of the meta data generated, we add probe to
        # the sink pad of the osd element, since by that time, the buffer would have
        # had got all the metadata.
        osdsinkpad = nvosd.get_static_pad("sink")
        if not osdsinkpad:
            sys.stderr.write(" Unable to get sink pad of nvosd \n")

        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER,
                             osd_sink_pad_buffer_probe(self), 0)

        pgie_srcpad = pgie.get_static_pad("src")
        if not pgie_srcpad:
            print(" Unable to get src pad of pgie \n")

        pgie_srcpad.add_probe(Gst.PadProbeType.BUFFER,
                            pgie_src_pad_buffer_probe(self), 0)


        # start play back and listen to events
        print("Starting pipeline \n")
        pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except:
            pass
       # cleanup
        pipeline.set_state(Gst.State.NULL)

if '__main__' == __name__:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--input', default='sample_720p-4.h264')
    p.add_argument('--output', default='tao_out.mp4')
    p.add_argument('--config')
    args = p.parse_args()

    pipeline = TAOPipeline(config=config)

    pipeline.run(args.input, args.output)
