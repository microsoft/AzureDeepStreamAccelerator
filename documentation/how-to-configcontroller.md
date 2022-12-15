# How to: Configure the Controller Module

This article serves as a technical reference for the configuration settings of the Controller Module,
which is the main point of configuration for the whole system.

# Table of Contents

* [Controller Module Configuration Specification](#controller-module)
* [Zip File Structure](#zip-file-structure)

## Controller Module

The Controller Module is the single point of configuration for the Azure DeepStream Accelerator workload from IoT Hub.
This module is responsible for configuring the other modules in the system, and should be the only module that
a user needs to configure themselves.

Below is the official specification of the Controller Module.

There are also many example configurations that you can find in the `ds-ai-pipeline/src/ai-pipeline-tests` folder.

```JSON
{
    // Other stuff that doesn't matter to us
    // ...
    "properties": {
        // Other stuff that doesn't matter to us
        // ...
        "twinProperties": {
            "desired": {
                "azdaConfiguration": {
                    "platform": "DeepStream", // MUST be DeepStream
                    "components": {
                        "logLevel": "one of { 'debug' 'information' 'warning' 'error' }",
                        "regionsOfInterest": [
                            {
                                "label": "name for this ROI",
                                "color": "3 byte hex code for RGB",
                                "sensor": "camera name - corresponds to one of the defined sensors in 'sensors' field",
                                "coordinates": [
                                    [ "x", "y" ],
                                    [ "x", "y" ],
                                    "etc."
                                ]
                            }
                        ],
                        "sensors": [
                            {
                                "name": "^\\[aA-zZ\\d-_]{4}$",
                                "kind": {
                                    "type": "one of { 'vision' 'audio' 'scalar' 'vector' } only 'vision' is currently supported",
                                    "subtype": "a descriptive subtype such as RTSP or USB - this can be any string, it is simply for logging"
                                },
                                "endpoint": "uri for where to find this sensor"
                            }
                        ],
                        "deepStream": {
                            "enable": "boolean",
                            "pipelineConfigs": [
                                {
                                    "id": "unique ID for this configuration",
                                    "unsecureZipUrl": "url that points to a .zip file containing model(s) and config(s)",
                                    "primaryModelConfigPath": {
                                        "configFile": "path to the primary model configuration, either inside the .zip file or inside the container already",
                                        "pyFile": "optional path to a Python file which will be used for parsing the outputs of this model"
                                    },
                                    "secondaryModelConfigPaths": [
                                        {
                                            "configFile": "path to a secondary model configuration, either inside the .zip file or inside the container already",
                                            "pyFile": "optional path to a Python file which will be used for parsing the outputs of this model"
                                        }
                                    ],
                                    "trackerConfigPath": "path to an optional tracker configuration file OR 'light-tracker' to use the built-in Light Tracker",
                                    "deepstreamPassthrough": "pipeline description",
                                    "pipelineOptions": {
                                        "dewarp": {
                                            "enable": "boolean",
                                            "config_file": "path to the NVIDIA dewarping plugin's configuration file"
                                        },
                                        "crop": {
                                            "enable": "boolean",
                                            "x0": "integer",
                                            "x1": "integer",
                                            "y0": "integer",
                                            "y1": "integer"
                                        },
                                        "osd": {
                                            "enable": "boolean"
                                        }
                                    }
                                }
                            ],
                            "streams": [
                                {
                                    "name": "must be one of the 'sensors' names",
                                    "uname": "user name for RTSP stream if it takes one",
                                    "password": "password for RTSP stream if it takes one",
                                    "configId": "id from 'pipelineConfigs' to use for this stream"
                                }
                            ]
                        },
                        "businessLogicConfig": {
                            // Opaque blob from user to be used by business logic container
                        }
                    }
                }
            }
        }
    }
}
```

Below is the complete description of the various keys and their allowed values.

* **logLevel**:
    - *Type*: String
    - *Required*: Yes
    - *Explanation*: Specifies the logging verbosity for all modules in the system.
    - *Allowed Values*: "trace", "debug", "information", "warning", "error", or "critical"
* **regionsOfInterest"**:
    - *Type*: Array of Objects
    - *Required*: Array may be empty.
    - *Explanation*: A list of ROIs defined in the Player Widget. These ROIs are ignored by
        the components (other than the Widget), and are meant to be used by the business logic container.
    - *Allowed Values*:
        * *label*: (Filled in by widget) A required String, which should be a unique name for this ROI.
        * *color*: (Filled in by widget) A 3 byte hex code for RGB. Used by the widget to display the ROI.
        * *sensor*: (Filed in by widget) A required String. Which sensor (camera) this ROI corresponds to. Must match one of the sensors defined in the 'sensors' section.
        * *coordinates*: (Filled in by widget) List of vertex pairs used by the Widget to display the ROI.
* **sensors**:
    - *Type*: Array of Objects
    - *Required*: Array should have at least one item in it
    - *Explanation*: The list of cameras to be used in the Azure DeepStream Accelerator System.
    - *Allowed Values*:
        * *name*: A required String. Each one should be unique within the sensors array. The String must match the following regex: "^\\[aA-zZ\\d-_]{4}$"
        * *kind*: An Object with the following two fields:
            * *type*: Currently only 'vision' is allowed.
            * *subtype*: Any descriptive String. This is meant for logging purposes.
        * *endpoint*: A required String which specifies the URI for this camera.
            * RTSP Cameras: IP cameras with a URI.
                - Example: `"endpoint": "rtsp://192.168.1.15:8080/stream1"`
            * RTSP Simulator: The [RTSP Simulator Module](../rtsp-simulator/README.md) deployed with the default experience
              can be used to simulate an RTSP stream, such as might be delivered by an IP camera.
                - Example: `"endpoint": "rtsp://rtspsim:554/media/cafeteria1.mkv"`
            * File (inside the ai-pipeline container): When using the CLI tool to build a custom ai-pipeline node, you may package up video
              files if you want.
                - Example: `"endpoint": "file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.mp4"`
            * USB Camera: A USB camera plugged into the physical machine that is running the Azure DeepStream Accelerator workload. Note that the ai-pipeline
              must be able to read USB devices passed in from the host OS. This requires special instructions in the deployment manifest.
                - Example: `"endpoint": "/dev/video0"`
* **deepStream/enable**:
    - *Type*: Boolean.
    - *Required*: Yes.
    - *Explanation*: If `false`, the ai-pipeline module stops monitoring incoming streams, thereby disabling the Azure DeepStream Accelerator system.
* **deepStream/pipelineConfigs**:
    - *Type*: Array of Objects.
    - *Required*: The array should not be empty.
    - *Explanation*: Each Object in this array specifies a possible DeepStream pipeline configuration. These configurations are then referenced
      in the configuration under the "streams" section to pair each camera with one of the possible DeepStream pipelines.
    - *Allowed Values*:
        * *id*: A required String, which must be a unique ID.
        * *unsecureZipUrl*: An optional String. If given (non-empty), it should point to a .zip file that can be downloaded using wget without authentication.
          You may place anything inside this .zip file. Anywhere a file path is specified in this configuration can point to one of the files found in the
          .zip file (without any prefix to the path). For example, if you have a folder called "MyCustomThings" inside the .zip file, and a tracker config
          file inside that folder, you could point to that tracker configuration file with: `"trackerConfigPath": "MyCustomThings/mytrackerfile.whatever"`
        * *primaryModelConfigPath*: An Object.
            - *configFile*: Path to the primary model configuration file. This file must be a DeepStream configuration file. If you want your model to
              utilize [TAO](https://developer.nvidia.com/tao-toolkit), your configuration file should follow [this specification](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvinfer.html#gst-nvinfer-file-configuration-specifications)
              while if your model should use [Triton Server](https://developer.nvidia.com/nvidia-triton-inference-server), your file should follow
              [this specification](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvinferserver.html#gst-nvinferserver-file-configuration-specifications).
              If you aren't sure which one you should use, then you should use Triton Server.
            - *pyFile*: Optional String. If given, should be a path to a Python source file, which we will use for parsing the outputs of the given model.
              If not given, DeepStream must be able to parse the model's output either because the model parser is built in to DeepStream or you specify a .so file
              and parsing function for C/C++ parsers (as specified in the NVIDIA config file documentation).
        * *secondaryModelConfigPaths*: An array of model configuration objects. Each one is the same as a primary configuration object, but the
          order of listing specifies the order in the pipeline.
        * *trackerConfigPath*: An optional String. If given (non-empty), should be a DeepStream tracker configuration file or the term "light-tracker",
          in which case we will use [Light Tracker](https://github.com/researchmm/LightTrack).
        * *deepstreamPassthrough*: An optional String. If given (non-empty), should be a description of a custom DeepStream pipeline in [GStreamer
          parse and launch syntax](https://gstreamer.freedesktop.org/documentation/tools/gst-launch.html?gi-language=python). If given,
          we will use this pipeline configuration and ignore all other configuration options listed here. This is for advanced users who understand
          exactly what they want their pipeline to do and want to take advantage of the IoT integration that Azure DeepStream Accelerator provides, without
          letting it manage their DeepStream pipeline.
        * *pipelineOptions*:
            - *Type*: An Object.
            - *Explanation*: There are some frequently used DeepStream plugins that we break out for additional configuration here.
            - *Allowed Values*:
                * *dewarp*:
                    - *enable*: Boolean. Turn this feature on or off.
                    - *config_file*: String. If enabled, this feature requires a configuration file to operate. The configuration file
                      should follow [this specification](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvdewarper.html#configuration-file-parameters). Dewarping occurs *before* the AI models are fed the image.
                * *crop*:
                    - *enable*: Boolean. Turn this feature on or off.
                    - *x0*: If enabled, each of x0, x1, y0, and y1 should be an integer which specifies the region to crop to. Cropping occurs *before* the AI
                      models are fed the image.
                * *osd*:
                    - *enable*: Boolean. Turn this feature on or off.
                    - *Explanation*: This feature is currently implemented incorrectly, and will be changed in a later release.
                      The current behavior is that you must enable this in order for inference overlays to be burned into videos uploaded
                      to the cloud.
                      The correct behavior (to be implemented later) is that videos uploaded to the cloud should always come in two forms: raw and inference
                      overlays, and the OSD plugin feature should operate as NVIDIA's On Screen Display plugin if a monitor is attached to the host system.
* **deepStream/streams**:
    - *Type*: Array of Objects.
    - *Required*: The array should not be empty.
    - *Explanation*: Each stream Object should pair one of the specified cameras with one of the specified DeepStream pipeline configurations.
    - *Allowed Values*:
        * *name*: Required String, which must be one of the declared sensor's names.
        * *uname*: If the RTSP stream requires a username, this is where you will put that.
        * *password*: If the RTSP stream requires a password, this is where you will put that.
        * *configId*: Required String, which must be one of the declared pipelineConfig's "id"s. This is the DeepStream pipeline that we will use
            for this camera.

## Zip File Structure

Your AI workload should consist of:

* [A configuration file](#configuration-files)
* [An optional tracker file](#tracker-configuration-files)
* Any supporting files that you need ([such as source code for parsing model outputs](#custom-ai-model-parsing))
* [The model or model files themselves](#model-files)

### Folder Creation

Once you have all of the files, you need to zip them up into a .zip file according to the following examples.

#### Single Model

In the case of a single model, you should follow this example:

```
wherever/
    |
    | - model/
        |
        | - configuration_file.txt
        | - tracker_file.txt
        | - model_file.whatever
        | - possibly_other_files
```

In this case, you would zip 'model' - right click on the model directory itself (not the individual files inside it) and zip it.

The other files would be referenced in your configuration_file.txt, according to [the configuration file specification](#configuration-files).

#### Multiple Models

In the case of a model cascade, you should use this example:

```
wherever/
    |
    | - model/
        |
        | - modelA/
            |
            | - configuration_file_for_model_A.txt
            | - model_file_A.whatever
            | - possibly_other_files
        |
        | - modelB/
            |
            | - configuration_file_for_model_B.txt
            | - model_file_B.whatever
            | - possibly_other_files
        |
        | - modelC/
            |
            | - configuration_file_for_model_C.txt
            | - model_file_C.whatever
            | - possibly_other_files
```

And in this case, as before, you would zip up 'model' - not the individual subfolders.

The actual names you use for the files and folders does not matter, only the structure (and of course,
if any of the files refers to the others).

### Configuration Files

We directly pass through any configuration files to the DeepStream config parser in Triton Server or TAO.
Refer to
[NVIDIA DeepStream configuration file specification](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvinfer.html)
for the details of what to include in the configuration file.

### Tracker Configuration Files

Currently, we use whatever DeepStream supports for frame-to-frame item tracking algorithms.
[Please see the DeepStream tracker spec](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvtracker.html) for details.

Additionally, we support [Microsoft Research's Light Tracker](https://github.com/researchmm/LightTrack), which you can make use of by using "light-tracker" for the config file path.

Note that a tracker configuration file is optional - you do not need to provide one, in which case, we do not enable any tracking.

### Supported Model Formats

We currently support any model format supported by DeepStream's TAO and Triton Server. Please see the
[NVIDIA DeepStream configuration file specification](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvinfer.html)
for details.

See the [Bring Your Own Model tutorial](./tutorial-byom-path.md) for how to enable a custom model with a custom model parser.