from furl import furl
from multiprocessing import Event
import configparser
import json
import logging
import os
import shutil
import subprocess
import threading

# This is what the user should enter into the trackerConfigPath if they want to enable Light Tracker
LIGHT_TRACKER = "light-tracker"
LIGHT_TRACKER_CONFIG_PATH = os.path.abspath(os.path.join("config_examples", "LightTrack.txt"))

class Stream:
    """
    A Stream corresponds to a sensor paired with a pipeline configuration.
    """
    def __init__(self) -> None:
        self.name = ""
        self.uname = ""
        self.password = ""
        self.configId = ""

    def from_json(self, message):
        self.name = message["name"]
        self.uname = message["uname"]
        self.password = message["password"]
        self.configId = message["configId"]

class Sensor:
    """
    A Sensor is a video source.
    """
    def __init__(self) -> None:
        self.name = ""
        self.sensor_type = ""
        self.subtype = ""
        self.endpoint = ""
        self.regions_of_interest = []

    def from_json(self, message):
        self.name = message["name"]
        self.sensor_type = message["kind"]["type"]
        self.subtype = message["kind"]["subtype"]
        self.endpoint = message["endpoint"]
        self.regions_of_interest = message["regionsOfInterest"] if "regionsOfInterest" in message.keys() else []

class ModelConfig:
    """
    A ModelConfig determines the type of AI model and where its configuration file(s) is/are located,
    along with any Python source files.
    """
    def __init__(self, msg) -> None:
        self.configFile = ""
        self.pyFile = None
        self.parser = None
        self.gieType="nvinfer"
        if isinstance(msg, str):
            self.configFile = msg
        elif isinstance(msg, dict):
            self.configFile = msg["configFile"]
            self.pyFile = msg["pyFile"] if "pyFile" in msg.keys() else None
            self.parser = msg["parser"] if "parser" in msg.keys() else None

class PipelineConfig:
    """
    A PipelineConfig is a configuration for a DeepStream pipeline. We use `Stream`s to
    pair these with `Sensor`s.
    """
    def __init__(self) -> None:
        self.id = ""
        self.unsecureZipUrl = None
        self.primaryModelConfigPath = None
        self.secondaryModelConfigPaths = None
        self.trackerConfigPath = None
        self.deepstreamPassthrough = None
        self.dewarpParameters=None
        self.cropParameters=None
        self.osdOption = False
        self.is_valid = True
        self.startRecording = Event()

    @staticmethod
    def _determine_configfile_type(config_file) -> str:
        """
        Determines whether a given config file is a Tao or Triton file.
        Tao config files are ini files and Triton config files are not.
        """
        config = configparser.ConfigParser()
        try:
            parse = config.read(config_file)
            if parse:
                logging.debug(f"{config_file} is a Tao model")
                return "nvinfer"
            else:
                logging.debug(f"{config_file} is a Triton model")
                return "nvinferserver"
        except configparser.MissingSectionHeaderError:
            logging.debug(f"MissingSectionHeader in {config_file}. Defaulting to Triton model type")
            return "nvinferserver"
        except configparser.DuplicateSectionError:
            logging.debug(f"DuplicateSection in {config_file}. Defaulting to Tao model type")
            return "nvinfer"
        except:
            logging.debug(f"Other exception in {config_file}. Defaulting to Tao model type")
            return "nvinfer"

    def setup_parsers_and_inference_type(self):
        if not self.is_valid:
            return

        # primary model
        if self.primaryModelConfigPath is not None:
            self.primaryModelConfigPath.gieType = self._determine_configfile_type(self.primaryModelConfigPath.configFile)

        # secondary models
        if self.secondaryModelConfigPaths is not None:
            for m in self.secondaryModelConfigPaths:
                m.gieType = self._determine_configfile_type(m.configFile)

    def from_json(self, message):
        self.id = message["id"]
        self.unsecureZipUrl = message["unsecureZipUrl"]

        # primary model config
        tmp = message["primaryModelConfigPath"]
        if tmp:
            self.primaryModelConfigPath = ModelConfig(msg=message["primaryModelConfigPath"])

        # secondary models
        tmp = message["secondaryModelConfigPaths"]
        if tmp:
            if isinstance(tmp, str) or isinstance(tmp, dict): tmp = [tmp]
            self.secondaryModelConfigPaths = [ModelConfig(o) for o in tmp]

        # tracker
        tmp = message["trackerConfigPath"]
        if tmp and tmp.lower() == LIGHT_TRACKER.lower():
            logging.info(f"User has requested Light Tracker. Will use {LIGHT_TRACKER_CONFIG_PATH} for the tracker config path.")
            self.trackerConfigPath = LIGHT_TRACKER_CONFIG_PATH
        elif tmp:
            self.trackerConfigPath = tmp

        # deepstreamPassthrough
        self.deepstreamPassthrough = message["deepstreamPassthrough"]

        if message["pipelineOptions"]:
            # dewarp
            dewarpOption = message["pipelineOptions"]["dewarp"]
            if dewarpOption["enable"]:
                self.dewarpParameters={}
                self.dewarpParameters["config_file"] = dewarpOption["config_file"]

            # crop
            cropOption = message["pipelineOptions"]["crop"]
            if cropOption["enable"]:
                x0 = int(cropOption["x0"])
                x1 = int(cropOption["x1"])
                y0 = int(cropOption["y0"])
                y1 = int(cropOption["y1"])
                self.cropParameters=(x0,x1,y0,y1)

            # osd
            self.osdOption = message["pipelineOptions"]["osd"]["enable"]

class Twin:
    """
    Singleton class for the Controller Module twin, which contains all the configuration
    for this IoT module.
    """
    # constant
    MODELS_FOLDER = "/root/models"
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        raise RuntimeError('Call get_instance() instead')

    def _init_all(self):
        # updated flag is set when the twin values are updated
        self.updated = False
        self.pipeline_count = 0
        self.stream_count = 0
        self.sensor_count = 0
        self.pipelines = {}
        self.streams = {}
        self.sensors = {}
        self.enable_pipelines = True
        # default output video length is 30 seconds
        self.output_video_length = 30

    @classmethod
    def get_instance(cls):
        """ Static access method. """
        if cls._instance is None:
            logging.info("Creating new instance of Twin()")
            with cls._lock:
                # another thread could have created the instance
                # before we acquired the lock. So check that the
                # instance is still nonexistent.
                if cls._instance is None:
                    cls._instance = cls.__new__(cls)
                    cls._instance._init_all()
        return cls._instance

    def parse_pipeline_configs(self, azda_skill):
        """
        Parses the pipeline configs from the skill
        """
        already_checked = {}
        configs = azda_skill["deepStream"]["pipelineConfigs"]
        self.pipeline_count = len(configs)
        self.pipelines.clear()

        logging.debug(f"Number of pipelines to be built: {self.pipeline_count}")
        if self.pipeline_count < 1:
            logging.error("No pipelines defined in configuration. There must be at least one pipeline defined")
        else:
            # Parse the pipelines
            for i in range(self.pipeline_count):
                config = PipelineConfig()
                config.from_json(configs[i])
                self.pipelines[config.id] = config

                if config.unsecureZipUrl != "":
                    valid = self._unsecure_update(plconfig=config)
                    config.is_valid = valid
                    already_checked[config.id] = valid
                config.setup_parsers_and_inference_type()
        return already_checked

    @staticmethod
    def run_cmd(*args):
        """
        Run a system command with the given command and return the return code of the completed process, or raise
        an exception from the process.
        """
        try:
            result = subprocess.run([arg for arg in args])
        except subprocess.CalledProcessError as e:
            logging.error(f"Got an exception when trying to run external command {e.cmd}")
            logging.error(f"Got status code: {e.returncode}")
            raise
        return result.returncode

    @staticmethod
    def _cleanup_downloads(*fpaths):
        """
        Attempts to cleanup after a(n attempted) model download.
        """
        for fpath in fpaths:
            try:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                elif os.path.isdir(fpath):
                    shutil.rmtree(fpath)
                logging.debug(f"Removed {fpath}.")
            except FileNotFoundError:
                logging.warning(f"When cleaning up after model download, could not delete {fpath}, as it does not exist.")
            except Exception as e:
                logging.error(f"Could not remove {fpath} while attempting to clean up model download: {e}")
                raise

    @staticmethod
    def get_folder_content(folder):
        result = []
        for root, _, files in os.walk(folder):
            for fname in files:
                apath = os.path.join(root, fname)
                rpath = os.path.relpath(apath, start=folder)
                result.append(rpath)
        return result

    def _unsecure_update(self, plconfig: PipelineConfig):
        """
        Attempts to download the model from an unsecure route and load it.
        """
        unsecure_zip_url = plconfig.unsecureZipUrl
        destination_model_path = "/root/model.zip"

        # Use wget to download the model
        try:
            retcode = self.run_cmd("wget", "--no-check-certificate", "-O", destination_model_path, unsecure_zip_url)
        except Exception as e:
            logging.error(f"Got an exception when trying to run wget: {e}")
            logging.error("Aborting model update.")
            self._cleanup_downloads(destination_model_path)
            return False

        # Check return code on wget
        if retcode != 0:
            logging.error(f"Got a non-zero return code: {retcode}. Failed to download the .zip file from {unsecure_zip_url}")
            self._cleanup_downloads(destination_model_path)
            return False

        return self._update_using_downloaded_model(destination_model_path, plconfig)

    def _update_using_downloaded_model(self, model_path: str, plconfig: PipelineConfig):
        """
        Extract and validate the zip file's contents.
        """
        # Make sure we have the right folder
        if not os.path.isdir(self.MODELS_FOLDER):
            os.makedirs(self.MODELS_FOLDER)

        # unzip the folder
        extracted_folder = os.path.join(self.MODELS_FOLDER, "downloaded")
        try:
            retcode = self.run_cmd("unzip", "-o", model_path, "-d", extracted_folder)
        except Exception as e:
            logging.error(f"Got an exception when trying to run the unzip command: {e}")
            logging.error("Aborting model update.")
            self._cleanup_downloads(model_path)
            return False

        # Check the return code on unzip
        if retcode not in [0, 1]:
            logging.error(f"Got an unexpected return code from unzip: {retcode}. Could not unzip the file at {model_path}. Model update failed.")
            self._cleanup_downloads(model_path, extracted_folder)
            return False
        elif retcode == 1:
            logging.warning(f"Got error code 1 when running unzip. This is not necessarily a fatal error. Check the logs to be sure.")

        logging.debug(f"Unzipped the folder and placed it at {extracted_folder}")

        # Sanity check
        if not os.path.exists(extracted_folder):
            logging.error(f"Something must have gone wrong with unzipping because there is no directory at {extracted_folder}. Model update failed.")
            self._cleanup_downloads(model_path, extracted_folder)
            return False

        dpaths = os.listdir(extracted_folder)

        # Remove any Mac OSX hidden folders that sometimes get caught up in zip files
        dpaths_lower = set([fpath.lower() for fpath in dpaths])
        removeable_items = ["__MACOSX", ".DS_Store"]
        for item in removeable_items:
            if item.lower() in dpaths_lower:
                os.removedirs(item)

        # Check the format of the extracted folder. There should be exactly one subfolder.
        # If there's one subfolder, move it to /tmp/models
        if not dpaths:
            logging.error("The unzipped model folder is empty. Aborting model update.")
            self._cleanup_downloads(model_path, extracted_folder)
            return False
        elif len(dpaths) > 1:
            logging.error(f"Expected exactly one subfolder in the zip file. Got {len(dpaths)} items inside instead.")
            logging.error(f"Contents of the zip file: {dpaths}")
            logging.error("Cannot continue. Aborting model update.")
            self._cleanup_downloads(model_path, extracted_folder)
            return False
        else:
            assert len(dpaths) == 1, f"Somehow there are {len(dpaths)} items in the zip file. There should only be one."
            tmp_model_dpath = os.path.join(extracted_folder, dpaths[0])
            model_dpath = os.path.join(self.MODELS_FOLDER, dpaths[0])
            if os.path.exists(model_dpath):
                # Remove the old version
                logging.debug(f"Removing old model {model_dpath}")
                shutil.rmtree(model_dpath)

            logging.debug(f"Moving extracted model to {model_dpath}")
            shutil.move(tmp_model_dpath, model_dpath)

        # Sanity check that the model directory exists
        if not os.path.exists(model_dpath):
            logging.error(f"Could not find the unzipped folder at {model_dpath}")
            self._cleanup_downloads(model_path, extracted_folder)
            return False

        # check "primaryModelConfigPath"
        if plconfig.primaryModelConfigPath is not None:
            # configFile
            tmp = plconfig.primaryModelConfigPath.configFile
            file_path = os.path.join(model_dpath, tmp)
            if not os.path.exists(file_path):
                logging.error(f"Given primary model config file {tmp}, but it does not seem to be present in the downloaded zip file after unzipping.")
                logging.error(f"Contents of the zipped folder: {self.get_folder_content(model_dpath)}")
                logging.error("Aborting model update.")
                self._cleanup_downloads(model_path, extracted_folder, model_dpath)
                return False
            # make sure that the file can be accessible from DS script
            plconfig.primaryModelConfigPath.configFile = file_path

            # pyFile
            tmp = plconfig.primaryModelConfigPath.pyFile

            file_path=None
            if tmp is not None:
                file_path = os.path.join(model_dpath, tmp)
            if file_path is not None and not os.path.exists(file_path):
                logging.error(f"Given primary model parser file {tmp}, but it does not seem to be present in the downloaded zip file after unzipping.")
                logging.error(f"Contents of the zipped folder: {self.get_folder_content(model_dpath)}")
                logging.error("Aborting model update.")
                self._cleanup_downloads(model_path, extracted_folder, model_dpath)
                return False

            # make sure that the file can be accessible from DS script
            plconfig.primaryModelConfigPath.pyFile = file_path

        # Check "trackerConfigPath"
        if plconfig.trackerConfigPath == LIGHT_TRACKER_CONFIG_PATH:
            # We've already assigned out plconfig.trackerConfigPath correctly.
            # We aren't using a tracker from the zip file - it's built in.
            pass
        elif plconfig.trackerConfigPath is not None:
            # Check if the tracker file path that was given actually exists inside the zip file
            file_path = os.path.join(model_dpath, plconfig.trackerConfigPath)
            if not os.path.exists(file_path):
                logging.error(f"Given a tracker config file path of {plconfig.trackerConfigPath}, but it does not seem to be present in the downloaded zip file after unzipping.")
                logging.error(f"Contents of the zipped folder: {self.get_folder_content(model_dpath)}")
                logging.error("Aborting model update.")
                self._cleanup_downloads(model_path, extracted_folder, model_dpath)
                return False
            # make sure that the file can be accessible from DS script
            plconfig.trackerConfigPath = file_path

        # check "secondaryModelConfigPaths"
        need_to_abort = False
        if plconfig.secondaryModelConfigPaths is not None:
            for i, m in enumerate(plconfig.secondaryModelConfigPaths):
                # config
                tmp = m.configFile
                file_path = os.path.join(model_dpath, tmp)
                if not os.path.exists(file_path):
                    logging.error(f"Given secondary model config file {tmp}, but it does not seem to be present in the downloaded zip file after unzipping.")
                    need_to_abort = True
                else:
                    plconfig.secondaryModelConfigPaths[i].configFile = file_path

                # pyFile
                tmp = m.pyFile
                file_path = None
                if tmp is not None:
                    file_path = os.path.join(model_dpath, tmp)
                if file_path is not None and not os.path.exists(file_path):
                    logging.error(f"Given secondary model parser file {tmp}, but it does not seem to be present in the downloaded zip file after unzipping.")
                    need_to_abort = True
                else:
                    # make sure that the file can be accessible from DS script
                    plconfig.secondaryModelConfigPaths[i].pyFile = file_path

            if need_to_abort:
                logging.error(f"Contents of the zipped folder: {self.get_folder_content(model_dpath)}")
                logging.error("Aborting model update.")
                self._cleanup_downloads(model_path, extracted_folder, model_dpath)
                return False

        # Clean up after ourselves
        self._cleanup_downloads(model_path, extracted_folder)
        return True

    def parse_streams(self, azda_skill):
        streams = azda_skill["deepStream"]["streams"]

        self.stream_count = len(streams)
        self.streams.clear()
        logging.debug(f"Number of streams: {self.stream_count}")
        if self.stream_count < 1:
            logging.error(f"No streams are defined.")
        else:
            # Parse the streams
            for i in range(self.stream_count):
                stream = Stream()
                stream.from_json(streams[i])
                self.streams[stream.name] = stream

    def parse_sensors(self, azda_skill):
        sensors = azda_skill["sensors"]
        self.sensor_count = len(sensors)
        self.sensors.clear()

        logging.debug(f"Number of sensors: {self.sensor_count}")
        if self.sensor_count < 1:
            logging.error(f"No sensors defined.")
        else:
            # Parse the sensors element
            for i in range(self.sensor_count):
                sensor = Sensor()
                sensor.from_json(sensors[i])
                self.sensors[sensor.name] = sensor

    def parse_twin_message(self, azda_skill: str):
        msg = json.loads(azda_skill)
        self.enable_pipelines = msg["deepStream"]["enable"]
        if self.enable_pipelines:
            pl_check = self.parse_pipeline_configs(azda_skill=msg)
            self.parse_streams(azda_skill=msg)
            self.parse_sensors(azda_skill=msg)
            self.check_all(pl_already_checked=pl_check)

    def get_sources(self, pl_config_id):
        """
        Create a list of sources from twin streams and sensors
        for a particular pipeline config
        """
        source_list = []
        sensor_list = []
        for stream_key, stream_value in self.streams.items():
            # Find corresponding sensor
            if stream_value.configId == pl_config_id:
                if stream_key in self.sensors:
                    sensor_value = self.sensors[stream_key]

                    sensor_list.append( sensor_value )

                    if stream_value.uname == "":
                        source_list.append(sensor_value.endpoint)
                    else:
                        f = furl(sensor_value.endpoint)
                        f.username = stream_value.uname
                        f.password = stream_value.password
                        source_list.append(f.url)
                else:
                    logging.error(f"Stream '{stream_key}' does not have a corresponding sensor")

        return source_list, sensor_list

    @staticmethod
    def check_pipeline_config(config : PipelineConfig):
        is_ok = True
        if config.primaryModelConfigPath is not None:
            tmp = config.primaryModelConfigPath.configFile
            if not os.path.exists(tmp):
                logging.error(f"Primary model config file '{tmp}' doesn't exist")
                is_ok = False
            tmp = config.primaryModelConfigPath.pyFile
            if tmp is not None and not os.path.exists(tmp):
                logging.error(f"Primary model parser file '{tmp}' doesn't exist")
                is_ok = False

            if config.secondaryModelConfigPaths is not None:
                for m in config.secondaryModelConfigPaths:
                    if not os.path.exists(m.configFile):
                        logging.error(f"Secondary model config file '{tmp}' doesn't exist")
                        is_ok = False
                    if m.pyFile is not None and not os.path.exists(m.pyFile):
                        logging.error(f"Secondary model parser file '{tmp}' doesn't exist")
                        is_ok = False

            if config.trackerConfigPath is not None:
                if config.trackerConfigPath.lower() != LIGHT_TRACKER and not os.path.exists(config.trackerConfigPath):
                    logging.error(f"Tracker config file '{config.trackerConfigPath}' doesn't exist")
                    is_ok = False
        else:
            if config.secondaryModelConfigPaths is not None:
                logging.error("Configuring a secondary model before a primary one has been defined.")
                is_ok = False

            if config.trackerConfigPath is not None:
                logging.error("Configuring a tracker before a primary model has been defined.")
                is_ok = False

        if config.dewarpParameters is not None:
            fname = config.dewarpParameters["config_file"]
            if not os.path.exists(fname):
                logging.error(f"Dewarp config file {fname} doesn't exist.")
                is_ok = False
        return is_ok

    def check_all(self, pl_already_checked):
        for pl_config in self.pipelines.keys():
            valid_streams_count = 0
            for stream_key, stream_value in self.streams.items():
                if stream_value.configId == pl_config:
                    if stream_key in self.sensors.keys():
                        # TODO(rbt): check if endpoint url is working, maybe using OpenCV
                        valid_streams_count += 1
                    else:
                        logging.error(f"Stream {stream_value.name} doesn't have a sensor config")

            if pl_config in pl_already_checked.keys():
                is_ok = pl_already_checked[pl_config]
            else:
                is_ok = self.check_pipeline_config(config=self.pipelines[pl_config])

            valid = valid_streams_count > 0 and is_ok
            if valid_streams_count == 0:
                logging.error(f"There are no input sources for pipeline: {pl_config}")

            self.pipelines[pl_config].is_valid = valid

        # other errors
        for stream_key, stream_value in self.streams.items():
            if stream_value.configId not in self.pipelines.keys():
                logging.error(f"Stream {stream_key} is not associated with any pipeline")
                if stream_key not in self.sensors.keys():
                    logging.error(f"Stream {stream_key} doesn't have Sensor config")

if __name__ == '__main__':
    pass
