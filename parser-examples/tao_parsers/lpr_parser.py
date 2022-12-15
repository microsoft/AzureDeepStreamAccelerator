from tao_pipeline import TAOPipeline, layer2array, make_elm_or_print_err, bus_call, sgie_src_pad_buffer_probe, osd_sink_pad_buffer_probe, GSListIter

import sys
from configparser import ConfigParser

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

import pyds
import numpy as np

from datetime import datetime

class lprParser(TAOPipeline):
    def __init__(self, config, class_names, image_width=1280, image_height=720,
                 lpr_config='', tracker_config='', pgie_config=''):
        # array of str names
        self.class_names = class_names
        self.lpr_dict = [name.strip() for name in open(config).readlines()]
        self.image_width = image_width
        self.image_height = image_height
        self.lpr_config = lpr_config
        self.tracker_config = tracker_config
        self.frame_objs = []
        self.pgie_config = pgie_config
        trafficcamnet_config =  ConfigParser()
        trafficcamnet_config.read(pgie_config)
        self.pgie_dims = trafficcamnet_config['property']['input-dims'].split(';')
        
        
    def parser(self, layers_info):
        outputStrBuffer = layer2array(layers_info[0])
        outputConfBuffer = layer2array(layers_info[1])

        if outputStrBuffer is None or outputConfBuffer is None:
            return []
        label = [self.lpr_dict[i] for i in outputStrBuffer if i < len(self.lpr_dict)]
        if 3 <= len(label):
            print('Plate License', ''.join(label))
        return label

    def dump_objects(self, frame_meta):
        frame_number = frame_meta.frame_num
        timestamp = datetime.fromtimestamp(frame_meta.ntp_timestamp/1e9)
#        print('frame_meta.ntp_timestamp', timestamp)
#        print('frame_meta.source_id', frame_meta.source_id)
#        print('frame_meta.source_frame_width', frame_meta.source_frame_width)
#        print('frame_meta.source_frame_height', frame_meta.source_frame_height)

        objects = [pyds.NvDsObjectMeta.cast(l_obj.data)
                   for l_obj in GSListIter(frame_meta.obj_meta_list)]

        source_info = {'id': frame_meta.source_id,
                       'timestamp': timestamp.isoformat()[:-3]+'Z',
                       'width': self.image_width,
                       'height': self.image_height,
                       'frameid': frame_number
                       }
        
        inferences = [{'classId': o.class_id,
                       'confidence': o.confidence,
                       'label': self.class_names[o.class_id],
                       'rect': [o.rect_params.left*self.image_width/float(self.pgie_dims[2]),
                                o.rect_params.top*self.image_height/float(self.pgie_dims[1]),
                                o.rect_params.width*self.image_width/float(self.pgie_dims[2]),
                                o.rect_params.height*self.image_height/float(self.pgie_dims[1])]
                       } for o in objects]

                       
        self.frame_objs.append({'sourceInfo': source_info,
                                'type': 'detection',
                                'inference': inferences
                                })
                                

    def run(self, input_video_name, output_video_name):
        #GObject.threads_init()
        Gst.init(None)
        pipeline = Gst.Pipeline()
        if not pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")

        source = make_elm_or_print_err("filesrc", "file-source", "Source")        

        # Since the data format in the input file is elementary h264 stream,
        # we need a h264parser
        h264parser = make_elm_or_print_err("h264parse", "h264-parser", "H264Parser")

        # Use nvdec_h264 for hardware accelerated decode on GPU
        decoder = make_elm_or_print_err("nvv4l2decoder", "nvv4l2-decoder", "Decoder")

        # Create nvstreammux instance to form batches from one or more sources.
        streammux = make_elm_or_print_err("nvstreammux", "Stream-muxer", "NvStreamMux")

        # Use nvinferserver to run inferencing on decoder's output,
        # behaviour of inferencing is set through config file
        trafficcamnet = make_elm_or_print_err('nvinfer', 'trafficcamnet', 'trafficcamnet')
        trafficcamnet.set_property("config-file-path", self.pgie_config)

        lpd = make_elm_or_print_err('nvinfer', 'lpd', 'lpd')
        lpd.set_property("config-file-path", 'lpd_us_config.txt')
        # Use convertor to convert from NV12 to RGBA as required by nvosd
        nvvidconv = make_elm_or_print_err("nvvideoconvert", "convertor", "Nvvidconv")

        # Create OSD to draw on the converted RGBA buffer
        nvosd = make_elm_or_print_err("nvdsosd", "onscreendisplay", "OSD (nvosd)")

        nvvidconv2 = make_elm_or_print_err("nvvideoconvert", "convertor2", "Converter 2 (nvvidconv2)")

        capsfilter = make_elm_or_print_err("capsfilter", "capsfilter", "capsfilter")

        caps = Gst.Caps.from_string("video/x-raw, format=I420")
        capsfilter.set_property("caps", caps)

        # On Jetson, there is a problem with the encoder failing to initialize
        # due to limitation on TLS usage. To work around this, preload libgomp.
        # Add a reminder here in case the user forgets.
        preload_reminder = "If the following error is encountered:\n" + \
                           "/usr/lib/aarch64-linux-gnu/libgomp.so.1: cannot allocate memory in static TLS block\n" + \
                           "Preload the offending library:\n" + \
                           "export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1\n"
        encoder = make_elm_or_print_err("avenc_mpeg4", "encoder", "Encoder", preload_reminder)

        encoder.set_property("bitrate", 2000000)

        codeparser = make_elm_or_print_err("mpeg4videoparse", "mpeg4-parser", 'Code Parser')

        container = make_elm_or_print_err("qtmux", "qtmux", "Container")

        sink = make_elm_or_print_err("filesink", "filesink", "Sink")

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
        pipeline.add(trafficcamnet)

        pipeline.add(nvvidconv)
        pipeline.add(nvosd)
        pipeline.add(nvvidconv2)
        pipeline.add(capsfilter)
        pipeline.add(encoder)
        pipeline.add(codeparser)
        pipeline.add(container)
        pipeline.add(sink)
        pipeline.add(lpd)

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
        streammux.link(trafficcamnet)
        
        if self.tracker_config:
            tracker = make_elm_or_print_err('nvtracker', 'tracker', 'tracker')
            tracker_config = ConfigParser()
            tracker_config.read(self.tracker_config)
            for k, v in tracker_config['tracker'].items():
                try:
                    v = int(v)
                except:
                    pass
                tracker.set_property(k, v)
                print('tracker.set_property(', k, ',', v, ')')
            pipeline.add(tracker)
            trafficcamnet.link(tracker)
            tracker.link(lpd)
        else:
            trafficcamnet.link(lpd)

        if self.lpr_config:
            lpr = make_elm_or_print_err('nvinfer', 'lpr', 'lpr')
            lpr.set_property("config-file-path", self.lpr_config)
            pipeline.add(lpr)
            lpd.link(lpr)
            lpr.link(nvvidconv)
            lprsrcpad = lpr.get_static_pad("src")
            if not lprsrcpad:
                print(" Unable to get src pad of lpr \n")
            lprsrcpad.add_probe(Gst.PadProbeType.BUFFER, sgie_src_pad_buffer_probe(self), 0)
        else:
            lpd.link(nvvidconv)

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

        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe(self), 0)

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
    import json

    p = argparse.ArgumentParser()
    p.add_argument('--input', nargs='?', default='sample_720p-4.h264')
    p.add_argument('--output', nargs='?', default='lpr_out.mp4')
    p.add_argument('--config', nargs='?', default='dict.txt')
    p.add_argument('--class_file_name', default='labels_trafficnet.txt')
    p.add_argument('--tracker_config')
    p.add_argument('--lpr_config', default='lpr_config_sgie_us.txt')
    p.add_argument('--pgie_config', default='trafficamnet_config.txt')
    args = p.parse_args()

    class_names = [name.strip() for name in open(args.class_file_name).readlines()]
    pipeline = lprParser(config=args.config, class_names=class_names,
                         lpr_config=args.lpr_config,
                         tracker_config=args.tracker_config,
                         pgie_config=args.pgie_config)

    pipeline.run(args.input, args.output)
    with open('lpr.json', 'w') as lpr:
        json.dump({'schemaVersion': '0.1',
                   'detections': pipeline.frame_objs},
                  lpr, indent=2)
