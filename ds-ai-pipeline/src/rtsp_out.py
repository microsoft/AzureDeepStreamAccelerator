from asyncio import subprocess
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from datetime import datetime
from dataclasses import dataclass
from multiprocessing import Process
from TwinParser import Twin, PipelineConfig
import common.utils as ds_utils
import CustomParsers as custom_parsers
import iot_messaging as iot_utils
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GLib
import logging
import math
import os
import pyds
import subprocess
import time

@dataclass
class PipelineData:
    config: PipelineConfig
    ds_pipeline: Gst.Element
    recording: bool
    rec_file_name: str
    timeout_id: int
    last_time: datetime

# GLOBAL CONSTANTS
AUTO_STOP_RECORD_TIMEOUT = 300 #Seconds to auto stop recording
GIE_TYPE = "nvinfer"  # "nvinferserver"
CODEC = "H264"
BITRATE = 4000000
MUXER_OUTPUT_WIDTH = 1280
MUXER_OUTPUT_HEIGHT = 720
MUXER_BATCH_TIMEOUT_USEC = 4000000
TILED_OUTPUT_WIDTH = 1280
TILED_OUTPUT_HEIGHT = 720
MAX_DISPLAY_LEN = 64
OSD_PROCESS_MODE = 0
OSD_DISPLAY_TEXT = 1
SINK_SYNC = 0
MUX_SYNC_INPUTS = 0
DISPLAY_ON_SCREEN = False
NFRAMES_TO_SEND_DATA = 30

#File Sink Settings
ONE_SECOND = 1000000000
VIDEO_UPLOADER_DIRECTORY = "/tmp/VideoUploaderCache/"

# Message Settings
MSCONV_CONFIG_FILE = "azda_msgconv_config.txt"
SCHEMA_TYPE = 0
AZURE_CONFIG_FILE = "cfg_azure.txt"
AZURE_PROTO_LIB = "/opt/nvidia/deepstream/deepstream-6.1/lib/libnvds_azure_edge_proto.so"
AZURE_EDGE_MODULE_OUTPUT = "inference"

# Some global state
source_list = {}
twin = Twin.get_instance()
running_pipeline_count = 0
procs = []
terminated = True

def create_rtsp_out_branch(pipeline, encoder):
    """
    Create a branch for RTSP output sink. This can be used for debugging purpose if
    develping in a container on a remote machine etc. Do the folowing steps to view the
    rtsp stream:
    - Create an SSH tunnel from your local machine to remote host: ssh -L 8554:localhost:8554 <remote host>
    - Point RTSP player such as VLC to rtsp://localhost:8554/<pipeline name>
    """

    if CODEC == "H264":
        rtppay = ds_utils.create_gst_element("rtph264pay", "rtppay_func")
    elif CODEC == "H265":
        rtppay = ds_utils.create_gst_element("rtph265pay", "rtppay_func")
    pipeline.add(rtppay)

    # Make the UDP sink
    updsink_port_num = 5400
    sink = ds_utils.create_gst_element("udpsink", "udpsink_func")
    pipeline.add(sink)

    sink.set_property("host", "224.224.255.255")
    sink.set_property("port", updsink_port_num)
    sink.set_property("async", False)
    sink.set_property("sync", 1)
    sink.set_property("qos", 0)

    rtsp_queue = ds_utils.create_gst_element("queue", "rtspqueue_func")
    pipeline.add(rtsp_queue)

    encoder.link(rtsp_queue)
    #Link queue to the downstreamd elements
    rtsp_queue.link(rtppay)
    rtppay.link(sink)

def record_message_handler(data: PipelineData):
    """
    Handler for the record events
    """
    logging.debug(f"Record Event:{data.config.startRecording.is_set()}")
    logging.debug(f"Recording:{data.recording}")
    if data.config.startRecording.is_set():
        if not data.recording:
            data.recording = True
            format_file_location(data)
            data.last_time = datetime.now()
        else:
            now = datetime.now()
            delta_secs = (now - data.last_time).total_seconds()
            length = twin.output_video_length
            if delta_secs >= length:
                format_file_location(data)
                data.last_time = now

    elif not data.config.startRecording.is_set() and data.recording:
        logging.debug("Recording is already in progress need to stop it")
        data.recording = False
        data.rec_file_name = None
    return True

def format_file_location (udata):
    pipe_data: PipelineData =  udata
    current_time = datetime.now().isoformat('-', 'seconds')
    new_file_name = pipe_data.config.id.lower() + "-" + current_time
    pipe_data.rec_file_name = new_file_name

def build_pipelines(msg_queue):
    """
    Go through the pipeline configs and build the pipelines one by one.

    This is the main entrypoint for running an AI pipeline.
    """
    global procs, terminated

    if not twin.enable_pipelines:
        logging.info("All AI Pipelines are disabled")
        return

    at_least_one = False
    for config_id, config in twin.pipelines.items():
        logging.info(f"Attempting to create pipeline based on {config_id}...")
        if config.is_valid:
            logging.info(f"Configuration for {config_id} is valid. Creating pipeline.")
        else:
            logging.error(f"Skipping {config_id} because its configuration is not valid.")
            continue

        if config.deepstreamPassthrough == "":
            proc = Process(target=build_and_run, name=config_id, args=(config_id, msg_queue))
        else:
            proc = Process(target=build_and_run_parse_launch, name=config_id, args=(config_id,))

        procs.append(proc)
        proc.start()
        at_least_one = True

    if not at_least_one:
        logging.info("No valid pipelines")
        return

    logging.info(f"Running Pipeline Count: {len(procs)}")

    while not terminated:
        time.sleep(2)

    terminated = False
    for proc in procs:
        proc.join()

    # All existing proc/pipelines have finished. Empty tist to start over
    logging.info(f"NO RUNNING PIPELINES")
    procs.clear()

def terminate_pipelines():
    global procs, terminated, loop_queue, glib_loops
    logging.info(f"TERMINATING EXISTING PROCESSES/PIPELINES: {len(procs)}")

    for proc in procs:
        proc.kill()

    terminated = True

def build_and_run_parse_launch(config_id):
    sources = twin.get_sources(config_id)
    config: PipelineConfig = twin.pipelines[config_id]

    logging.info(f"Pipeline ID: {config_id}")
    logging.info(f"Video Sources: {sources}")

    # Standard GStreamer initialization
    Gst.init(None)
    pipeline = Gst.parse_launch(config.deepstreamPassthrough)

    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # start play back and listen to events
    logging.info("*** Starting pipeline: {}".format(config_id))
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        logging.info("DeepStream: Exception encountered!")

    pipeline.set_state(Gst.State.NULL)
    logging.info("*** Ending pipeline: {}".format(config_id))

def build_and_run(config_id, msg_queue):
    """
    Build and start an ai pipeline based on the given AI Pipeline configuration.
    """
    # Check the number of streams
    sources, sensors = twin.get_sources(config_id)
    number_sources = len(sources)
    config: PipelineConfig = twin.pipelines[config_id]

    logging.info(f"{config_id}: Video Sources: {sources}")

    # This is where we will put our video snippets that we want to upload to the cloud
    if not os.path.exists(VIDEO_UPLOADER_DIRECTORY):
        os.system("mkdir -p {}".format(VIDEO_UPLOADER_DIRECTORY))

    # Standard GStreamer initialization
    Gst.init(None)

    # Create Pipeline element. Pipelines are GStreamer's top-level construct.
    pipeline = Gst.Pipeline()
    if not pipeline:
        logging.error(f"{config_id}: Unable to create Pipeline.")
        return

    # Create a streammux
    streammux = ds_utils.create_gst_element("nvstreammux", "StreamMuxer")
    pipeline.add(streammux)

    # For each video source, mux it together with all the other sources using the streammux
    # The output of this loop should be the start of our Gst Pipeline.
    # Something like this: [ source_bin -> nvconv -> streammux ]
    is_live = False
    for i, uri_name in enumerate(sources):
        if uri_name.lower().startswith("rtsp://"):
            is_live = True

        # Create a source bin. A bin is a group of elements.
        st = sensors[i].subtype
        source_bin = ds_utils.create_source_bin_v4l2(i, uri_name) if st.lower() == "usb" else ds_utils.create_source_bin(i, uri_name)
        if not source_bin:
            logging.error(f"{config_id}: Unable to create source bin.")
            return
        pipeline.add(source_bin)

        # Create an nvconv (video convert) element and add it to the pipeline
        conv = ds_utils.create_gst_element("nvvideoconvert", f"conv_{i}")
        if not conv:
            logging.error(f"{config_id}: Unable to create nvvideoconvert element.")
            return
        pipeline.add(conv)

        ## Set some properties on the nvconv element
        if not is_aarch64():
            conv.set_property("nvbuf-memory-type", int(pyds.NVBUF_MEM_CUDA_UNIFIED))

        if config.cropParameters is not None:
            x0,x1,y0,y1 = config.cropParameters
            conv.set_property('src-crop', "{}:{}:{}:{}".format(x0, y0, x1-x0+1, y1-y0+1))
        else:
            conv.set_property('src-crop',"0:0:99999:99999")

        if config.dewarpParameters is not None:
            dewarp_bin = ds_utils.create_dewarper_bin(i, config.dewarpParameters["config_file"])
            if not dewarp_bin:
                logging.error(f"{config_id}: Unable to create dewarp bin.")
                return
            pipeline.add(dewarp_bin)
            dewarp_bin.link(conv)

            padI = dewarp_bin.get_static_pad("sink")
            if not padI:
                logging.error(f"{config_id}: Unable to create sink pad on dewarp bin.")
                return
        else:
            padI = conv.get_static_pad("sink")
            if not padI:
                logging.error(f"{config_id}: Unable to create sink pad on nvconv element.")
                return

        # Get the source pad from the source bin
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            logging.error(f"{config_id}: Unable to create src pad bin.")
            return

        # Get the sink pad from the streammux element
        sinkpad = streammux.get_request_pad(f"sink_{i}")
        if not sinkpad:
            logging.error(f"{config_id}: Unable to create sink pad bin.")
            return

        # Get the output pad from the conv element
        padO = conv.get_static_pad("src")
        if not padO:
            logging.error(f"{config_id}: Unable to create padO on conv element.")
            return

        # Link up the elements: [ source_bin -> nvconv -> streammux ]
        srcpad.link(padI)
        padO.link(sinkpad)

    # For sending message to IoTHub
    msg_helper = iot_utils.IotMSGHelper(msg_queue=msg_queue, nframes=NFRAMES_TO_SEND_DATA)
    msg_helper.padindex_to_srcname = [sensors[i].name for i in range(len(sources))]
    msg_helper.frame_size = (MUXER_OUTPUT_WIDTH, MUXER_OUTPUT_HEIGHT)
    msg_helper.config_id = config_id
    msg_helper.VIDEO_UPLOADER_DIRECTORY = VIDEO_UPLOADER_DIRECTORY
    msg_helper.regions_of_interest = []
    for s in sensors:
        for roi in s.regions_of_interest:
            cpy_roi = roi.copy()
            cpy_roi["sensor"] = s.name
            msg_helper.regions_of_interest.append(cpy_roi)

    # Creating PGIE
    pgie = None
    pgi_parser = None
    if config.primaryModelConfigPath is not None:
        dd = config.primaryModelConfigPath
        pgie = ds_utils.create_gst_element(dd.gieType, "primary-inference")
        if dd.pyFile is not None:
            logging.info(f"{config_id}: Using custom Python parser.")
            pgi_parser = custom_parsers.create_parser_from_user_pyfile(dd.pyFile)
            if pgi_parser is None:
                logging.error(f"{config_id}: Load custom user parser failed!. Cannot create pipeline.")
                return
        elif dd.parser is not None:
            logging.info(f"{config_id}: Using pre-built special parser {dd.parser}")
            pgi_parser = custom_parsers.get_parser_by_name(dd.parser)
            if pgi_parser is None:
                logging.error(f"{config_id}: No parser found for model '{dd.parser}'. Cannot create pipeline.")
                logging.error(f"{config_id}: Available parsers: {custom_parsers.get_available_parsers()}")
                return

        if pgi_parser is not None:
            pgi_parser.image_size = (MUXER_OUTPUT_WIDTH, MUXER_OUTPUT_HEIGHT)
            pgi_parser.msg_helper = msg_helper
            logging.info(f"{config_id}: Creating parser {pgi_parser.get_name()} for primary model")


        pgie.set_property("config-file-path", dd.configFile)
        pgie_batch_size = pgie.get_property("batch-size")
        if pgie_batch_size != number_sources:
            logging.warning(f"{config_id}: Overriding infer-config batch-size {pgie_batch_size} with number of sources {number_sources}")
            pgie.set_property("batch-size", number_sources)
        pipeline.add(pgie)
    logging.info(f"{config_id}: PGIE created.")

    nvtracker = None
    if config.trackerConfigPath is not None:
        nvtracker =  ds_utils.create_gst_element("nvtracker", "tracker")
        pipeline.add(nvtracker)
        ds_utils.configure_tracker(tracker=nvtracker, config_file=config.trackerConfigPath)
        logging.info(f"{config_id}: Tracker created")
    else:
        logging.info(f"{config_id}: No tracker defined for this pipeline configuration.")

    # Creating SGIEs
    sgie_list = []
    if config.secondaryModelConfigPaths is not None:
        for i, m in enumerate(config.secondaryModelConfigPaths):
            sgie = ds_utils.create_gst_element(GIE_TYPE, "secundary-inference{:02d}".format(i))
            sgie.set_property("config-file-path", m.configFile)
            logging.info(f"{config_id}: Using secondary model with config file {m.configFile}")

            if m.pyFile is not None:
                logging.info(f"{config_id}: Secondary model {m.configFile} using custom Python parser.")
                sgieId, funct = custom_parsers.create_sgie_parser_from_user_pyfile(m.pyFile)
                if sgieId is not None:
                    msg_helper.register_sgie_parser(sgieId, funct)
                else:
                    logging.error(f"{config_id}: Loading custom secondary model Python parser failed!. Cannot create pipeline.")
                    return

            sgie_list.append(sgie)
            pipeline.add(sgie)

    # Creating tiler
    tiler = ds_utils.create_gst_element("nvmultistreamtiler", "nvtiler")
    pipeline.add(tiler)

    # Creating nvvidconv
    nvvidconv = ds_utils.create_gst_element("nvvideoconvert", "convertor")
    pipeline.add(nvvidconv)

    # Only add nvosd if the flag is set to true in the twin config
    nvosd = None
    if config.osdOption:
        nvosd = ds_utils.create_gst_element("nvdsosd", "onscreendisplay")
        nvosd.set_property('process-mode', OSD_PROCESS_MODE)
        nvosd.set_property('display-text', OSD_DISPLAY_TEXT)
        nvosd.set_property('display-mask', 1)
        nvosd.set_property('display-bbox', 1)
        nvosd.set_property('display-text',1)
        pipeline.add(nvosd)

    nvvidconv_postosd = ds_utils.create_gst_element("nvvideoconvert", "convertor_postosd")
    pipeline.add(nvvidconv_postosd)

    if is_aarch64():
        caps = ds_utils.create_gst_element("queue", "filter")
        pipeline.add(caps)

        # Make the encoder x264enc nvv4l2h264enc
        if CODEC == "H264":
            encoder = ds_utils.create_gst_element("x264enc", "encoder")
        if CODEC == "H265":
            encoder = ds_utils.create_gst_element("x265enc", "encoder")
    else:
        # Create a caps filter
        caps = ds_utils.create_gst_element("capsfilter", "filter")
        pipeline.add(caps)
        caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

        # Make the encoder x264enc nvv4l2h264enc
        if CODEC == "H264":
            encoder = ds_utils.create_gst_element("nvv4l2h264enc", "encoder")
        if CODEC == "H265":
            encoder = ds_utils.create_gst_element("nvv4l2h265enc", "encoder")

    pipeline.add(encoder)

    # Make the UDP sink
    updsink_port_num = 5400

    # Setting up StreamMuxer
    if is_live:
        logging.info(f"{config_id}: At least one of the sources is live")
        streammux.set_property('live-source', 1)
    streammux.set_property("width", MUXER_OUTPUT_WIDTH)
    streammux.set_property("height", MUXER_OUTPUT_HEIGHT)
    streammux.set_property("batch-size", number_sources)
    streammux.set_property("batched-push-timeout", MUXER_BATCH_TIMEOUT_USEC)
    streammux.set_property("sync-inputs", MUX_SYNC_INPUTS)
    if config.primaryModelConfigPath is not None:
        streammux.set_property("enable-padding", ds_utils.check_for_padding(config.primaryModelConfigPath.configFile, config.primaryModelConfigPath.gieType))

    # Setting up Tiler
    tiler_rows = int(math.sqrt(number_sources))
    tiler_columns = int(math.ceil((1.0 * number_sources) / tiler_rows))
    tiler.set_property("rows", tiler_rows)
    tiler.set_property("columns", tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)

    # link all elements
    if pgie:
        streammux.link(pgie)

        if nvtracker:
            pgie.link(nvtracker)
            last_ele = nvtracker
        else:
            last_ele = pgie

        for spgie in sgie_list:
            last_ele.link(spgie)
            last_ele = spgie
        last_ele.link(nvvidconv)
    else:
        streammux.link(nvvidconv)

    if not is_aarch64():
        mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
        nvvidconv.set_property("nvbuf-memory-type", mem_type)

    if nvosd:
        nvvidconv.link(nvosd)
        nvosd.link(tiler)
        tiler.link(nvvidconv_postosd)
    else:
        caps_rgba = ds_utils.create_gst_element("capsfilter", "to_rgba")
        pipeline.add(caps_rgba)
        caps_rgba.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA"))
        nvvidconv.link(caps_rgba)
        caps_rgba.link(tiler)
        tiler.link(nvvidconv_postosd)

    # DISPLAY RESULT ON THE SCREEN FOR TEST
    if DISPLAY_ON_SCREEN:
        pre_tee = ds_utils.create_gst_element("tee", "pre_tee")
        pipeline.add(pre_tee)
        squeue = ds_utils.create_gst_element("queue", "squeue")
        pipeline.add(squeue)

        nvvidconv_postosd.link(pre_tee)

        tee_src_pad = pre_tee.get_request_pad('src_%u')

        sink = ds_utils.create_gst_element("nveglglessink", "nvvideo-renderer")
        sink.set_property("async", False)
        sink.set_property("sync", SINK_SYNC)
        sink.set_property("qos", 0)
        pipeline.add(sink)

        if is_aarch64():
            transform = ds_utils.create_gst_element("nvegltransform", "nvegl-transform")
            pipeline.add(transform)
            squeue.link(transform)
            transform.link(sink)
            sink_pad = squeue.get_static_pad('sink')
        else:
            squeue.link(sink)
            sink_pad = squeue.get_static_pad('sink')

        tee_src_pad.link(sink_pad)

        tee_src_pad = pre_tee.get_request_pad('src_%u')
        sink_pad = caps.get_static_pad('sink')
        tee_src_pad.link(sink_pad)
    else:
        nvvidconv_postosd.link(caps)

    caps.link(encoder)
    create_rtsp_out_branch(pipeline, encoder)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Start streaming
    rtsp_port_num = 8554

    server = GstRtspServer.RTSPServer.new()
    server.props.service = "%d" % rtsp_port_num
    server.attach(None)

    factory = GstRtspServer.RTSPMediaFactory.new()
    factory.set_launch(
        '( udpsrc name=pay0 port=%d buffer-size=524288 caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 " )'
        % (updsink_port_num, CODEC)
    )
    factory.set_shared(True)
    server.get_mount_points().add_factory("/{}".format(config.id.lower()), factory)

    logging.info(f"{config_id}: Launched RTSP Streaming at rtsp://localhost:{rtsp_port_num}/{config.id.lower()}")

    # Initiate object to keep track of pipeline data in this process
    pipeline_data = PipelineData(config, pipeline, False, None, 0, last_time=datetime.now())

    # Add probes
    ds_utils.add_probe_callback(element=tiler, pad_name="sink", funct=msg_helper.collect_data_for_iot_hub, u_data=pipeline_data)
    if pgi_parser is not None:
        ds_utils.add_probe_callback(element=pgie, pad_name='src', funct=pgi_parser.pgie_src_pad_buffer_probe)

    ############ DOT OUTPUT ##################################################
    if "GST_DEBUG_DUMP_DOT_DIR" in os.environ:
        fname = "pipeline-debug-graph-file"
        fname_dot = fname + ".dot"
        fname_png = fname + ".png"
        fpath_dot = os.path.join(os.environ["GST_DEBUG_DUMP_DOT_DIR"], fname_dot)
        fpath_png = os.path.join(os.environ["GST_DEBUG_DUMP_DOT_DIR"], fname_png)
        Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, fname)
        if os.path.isfile(fpath_dot):
            try:
                ret = os.system(f"dot -Tpng {fpath_dot} > {fpath_png}")
                if ret == 0:
                    logging.info(f"Pipeline graph written to {fpath_png}")
                else:
                    subprocess.run(["apt-get", "update"])
                    subprocess.run(["apt-get", "install", "-y", "graphviz"])
                    ret = os.system(f"dot -Tpng {fpath_dot} > {fpath_png}")
                    if ret != 0:
                        raise OSError("Can't seem to call 'dot'")
            except Exception as e:
                logging.warning(f"{config_id}: Error writing dot png file: {e}")
        else:
            logging.warning(f"Could not find {fpath_dot}")
    ##########################################################################

    # start play back and listen to events
    logging.info(f"{config_id}: Starting pipeline")
    pipeline.set_state(Gst.State.PLAYING)

    GLib.timeout_add_seconds(1, record_message_handler, pipeline_data)

    try:
        loop.run()
    except Exception as e:
        logging.error(f"{config_id}: Error encountered while running DeepStream pipeline: {e}")

    # save any pending data
    msg_helper.save_pending_data()

    logging.info(f"{config_id}: Cleaning up pipeline.")
    pipeline.set_state(Gst.State.NULL)
