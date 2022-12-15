import configparser
import logging
import multiprocessing
import re
import subprocess
import sys
sys.path.append('/opt/nvidia/deepstream/deepstream/lib')
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

class RTSPWrapperForV4L2Device(multiprocessing.Process):
    instances_count = 0
    port_numbers = [8100+i*100 for i in range(10)]

    def __init__(self):
        super(RTSPWrapperForV4L2Device, self).__init__()
        self.port_number = self.port_numbers[self.instances_count]
        self.instances_count += 1

    def get_rtsp_uri(self):
        return f"rtsp://127.0.0.1:{self.port_number}/v4l2device"

    def run(self):
        """
        Entry point for the process.
        """
        Gst.init(None)
        mainloop = GLib.MainLoop()
        server = GstRtspServer.RTSPServer()
        server.props.service = f"{self.port_number}"
        mounts = server.get_mount_points()
        factory = GstRtspServer.RTSPMediaFactory()
        factory.set_launch( 'v4l2src device=/dev/video0 ! videoconvert ! video/x-raw,format=I420 ! x264enc tune=zerolatency ! rtph264pay name=pay0')
        mounts.add_factory("/v4l2device", factory)
        server.attach(None)
        mainloop.run()

def cb_newpad(decodebin, decoder_src_pad,data):
    caps = decoder_src_pad.get_current_caps()
    gststruct = caps.get_structure(0)
    gstname = gststruct.get_name()
    source_bin = data
    features = caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    if gstname.find("video") != -1:
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad = source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                logging.error("Failed to link decoder src pad to source bin ghost pad")
        else:
            logging.error(" Error: Decodebin did not pick nvidia decoder plugin")

def decodebin_child_added(child_proxy,Object,name,user_data):
    if name.find("decodebin") != -1:
        Object.connect("child-added",decodebin_child_added,user_data)

def create_source_bin(index, uri):
    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name = "source-bin-%02d" %index
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        logging.error("Unable to create source bin")
        return None

    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin = create_gst_element("uridecodebin", "uri-decode-bin")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri",uri)
    # Connect to the "pad-added" signal of the decodebin which generates a
    # callback once a new pad for raw data has beed created by the decodebin
    uri_decode_bin.connect("pad-added", cb_newpad,nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added,nbin)

    # We need to create a ghost pad for the source bin which will act as a proxy
    # for the video decoder src pad. The ghost pad will not have a target right
    # now. Once the decode bin creates the video decoder and generates the
    # cb_newpad callback, we will set the ghost pad target to the video decoder
    # src pad.
    Gst.Bin.add(nbin,uri_decode_bin)
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
    if not bin_pad:
        logging.error("Failed to add ghost pad in source bin")
        return None
    return nbin

def get_usbparams(uri):
    # run the following command: f"v4l2-ctl --all --device={uri}"
    proc = subprocess.run(["v4l2-ctl", "--all", f"--device={uri}"], capture_output=True)
    if proc.returncode != 0:
        logging.error(f"Could not open v4l2-ctl on device {uri}. STDERR: {proc.stderr.decode()}")
        return None

    format = None
    try:
        # Grep through the output for format
        supported_formats = set([
            "YUYV", "RGB16", "BGR", "RGB",
            "ABGR", "xBGR", "RGBA", "RGBx",
            "GRAY8", "GRAY16_LE", "GRAY16_BE",
            "YVU9", "YV12", "YUY2", "YVYU",
            "UYVY", "Y42B", "Y41B", "YUV9",
            "NV12_64Z32", "NV12_8L128",
            "NV12_10BE_8L128", "NV24",
            "NV12_16L32S", "NV61", "NV16",
            "NV21", "NV12", "I420", "ARGB",
            "xRGB", "BGRA", "BGRx", "BGR15", "RGB15"
        ])
        reported_formats = [line.strip().lstrip("Pixel Format").lstrip().lstrip(":").lstrip().split("'")[1] for line in proc.stdout.decode().splitlines() if line.strip().startswith("Pixel Format")]
        for reported_format in reported_formats:
            if reported_format in supported_formats:
                # YUYV is called YUY2 in gstreamer
                if reported_format == "YUYV":
                    format = "YUY2"
                    break
                else:
                    format = reported_format
                    break
    except Exception as e:
        logging.error(f"Error when trying to parse the reported formats of the USB device: {e}")

    if format is None:
        logging.error(f"Could not determine format for USB device at {uri}. USB device reports the following formats: {reported_formats}")
        return None
    else:
        logging.info(f"Determined format for USB device {uri} to be {format}")

    # Grep through the output for width and height
    width = None
    height = None
    for line in proc.stdout.decode().splitlines():
        if line.strip().startswith("Width/Height"):
            try:
                _, wh = line.split(":")
                width, height = wh.split("/")
                width = int(width)
                height = int(height)
            except Exception:
                logging.warning(f"Could not parse '{line}' for width and height.")

    if width is None or height is None:
        logging.error(f"Could not determine width and height for USB device at {uri}.")
        return None

    return f"width={width},height={height},format={format}"

def create_dewarper_bin(index, config):
    bin_name = "dewarp-bin-%02d" %index
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        logging.error("Unable to create dewarp bin")
        return None

    # Create an nvconv for dewarping
    dconv = create_gst_element("nvvideoconvert", f"dconv_{index}")
    if not dconv:
        logging.error(f"Unable to create nvvideoconvert element for dewarp. Internal GStreamer error.")
        return None

    # Create a caps filter element for dewarping
    dcaps = create_gst_element("capsfilter", f"dfilter_{index}")
    if not dcaps:
        logging.error(f"Unable to create capsfilter element for dewarp. Internal GStreamer error.")
        return None

    # Set the caps
    dcaps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA"))

    # Create the actual dewarper element
    dewarp = create_gst_element("nvdewarper", f"dewarp_{index}")
    if not dewarp:
        logging.error(f"Unable to create nvdewarper element. Internal GStreamer error.")
        return None

    # Set the properties on the dewarper - particularly point to its configuration file
    dewarp.set_property("config-file", config)
    dewarp.set_property("source_id", index)

    # Add everything to the bin
    Gst.Bin.add(nbin, dconv)
    Gst.Bin.add(nbin, dcaps)
    Gst.Bin.add(nbin, dewarp)

    # Link everything together to make a dewarping chain.
    dconv.link(dcaps)
    dcaps.link(dewarp)

    # Forward some pads from the internal elements to the bin so we can access them
    pad = dewarp.get_static_pad("src")
    ghostpad = Gst.GhostPad.new("src", pad)
    bin_pad = nbin.add_pad(ghostpad)
    if not bin_pad:
        logging.error("Failed to add src ghost pad in dewarp bin.")
        return None

    otherpad = dconv.get_static_pad("sink")
    otherghostpad = Gst.GhostPad.new("sink", otherpad)
    other_bin_pad = nbin.add_pad(otherghostpad)
    if not other_bin_pad:
        logging.error("Failed to add sink ghost pad in dewarp bin.")
        return None

    return nbin

def create_source_bin_v4l2(index, uri):
    bin_name = "source-bin-%02d" %index
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        logging.error("Unable to create source bin")
        return None

    usb_cam_source = create_gst_element("v4l2src", "usb-cam-source")
    usb_cam_source.set_property("device", uri)
    usb_cam_source.connect("pad-added", cb_newpad, nbin)

    caps_v4l2src = create_gst_element("capsfilter", "v4l2src_caps")
    vidconvsrc = create_gst_element("videoconvert", "convertor_src1")
    nvvidconvsrc = create_gst_element("nvvideoconvert", "convertor_src2")
    caps_vidconvsrc = create_gst_element("capsfilter", "nvmm_caps")

    caps_vidconvsrc.set_property('caps', Gst.Caps.from_string("video/x-raw(memory:NVMM),format=I420"))

    usbparams = get_usbparams(uri)
    if usbparams is None:
        logging.warning(f"Could not get parameters for the USB device at {uri}. Supplying default caps for v4l2src. USB camera may not work.")
        caps_v4l2src.set_property('caps', Gst.Caps.from_string(f"video/x-raw, framerate=30/1"))
    else:
        logging.info(f"Got the following caps for the USB device at {uri}: {usbparams}")
        caps_v4l2src.set_property('caps', Gst.Caps.from_string(f"video/x-raw, framerate=30/1, {usbparams}"))

    Gst.Bin.add(nbin,usb_cam_source)
    Gst.Bin.add(nbin, caps_v4l2src)
    Gst.Bin.add(nbin, vidconvsrc)
    Gst.Bin.add(nbin,nvvidconvsrc)
    Gst.Bin.add(nbin,caps_vidconvsrc)

    # [ USB Cam Src -> caps v4l -> nvvidconv -> caps nvvidconv ]
    usb_cam_source.link(caps_v4l2src)
    caps_v4l2src.link(vidconvsrc)
    vidconvsrc.link(nvvidconvsrc)
    nvvidconvsrc.link(caps_vidconvsrc)

    pad = caps_vidconvsrc.get_static_pad("src")
    ghostpad = Gst.GhostPad.new("src",pad)
    bin_pad = nbin.add_pad(ghostpad)
    if not bin_pad:
        logging.error("Failed to add ghost pad in source bin")
        return None
    return nbin

def configure_tracker(tracker, config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    config.sections()

    for key in config['tracker']:
        if   key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        elif key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        elif key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        elif key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        elif key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        elif key == 'enable-batch-process' :
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)

def create_gst_element(ename, obj_name):
    result = Gst.ElementFactory.make(ename, obj_name)
    if not result:
        logging.error(f"Unable to create {ename}")
        raise RuntimeError(f"Cannot create {ename}")
    return result

def add_probe_callback(element, pad_name, funct, u_data=0):
    pad = element.get_static_pad(pad_name)
    if not pad:
        logging.error("Unable to get src pad")
        raise RuntimeError("Unable to get src pad")
    else:
        pad.add_probe(Gst.PadProbeType.BUFFER, funct, u_data)

def check_for_padding(config_fpath: str, gie_type: str):
    """
    Check if the given config file has padding enabled.
    """
    if gie_type == "nvinferserver":
        # Unfortunately, there doesn't seem to be a good way to parse prototxt files easily.
        # Just look for "symmetric-padding" and use regex to the best of our ability.
        # This item should be found in 'infer_config': 'preprocess'
        config = open(config_fpath).read()
        # Strip out all the commented lines
        config_no_comments = []
        for line in config.splitlines():
            if not line.lstrip().startswith("#"):
                config_no_comments.append(line)
        config_no_comments = "\n".join(config_no_comments)
        result = re.search("^[\s]*symmetric-padding:[\s]*[0,1]", config_no_comments, flags=re.MULTILINE)
        if result is not None:
            start, end = result.span()
            matched_portion = result.string[start:end]
            next_result = re.search("0|1", matched_portion)
            start, end = next_result.span()
            return bool(int(next_result.string[start:end]))
        else:
            return False
    else:
        config = configparser.ConfigParser(strict=False)
        try:
            parsed = config.read(config_fpath)
        except UnicodeDecodeError as e:
            logging.error(f"Reading configuration file {config_fpath} failed with the following error: {e}; assuming no padding.")
            return False
        except FileNotFoundError:
            logging.error(f"Could not find the configuration file at {config_fpath}; assuming no padding.")
            return False
        except configparser.MissingSectionHeaderError:
            # This is probably a Triton Inference Server configuration file
            logging.error(f"Syntax for config file {config_fpath} seems to indicate a Triton Inference Server config file, but we have already deduced it differently. Assuming no padding.")
            return False

        if 'property' in config and 'symmetric-padding' in config['property']:
            return bool(int(config['property']['symmetric-padding']))
        else:
            return False
