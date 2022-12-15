# How to add multiple video streams to your Azure DeepStream Accelerator solution

This solution can support a variety of business scenarios involving multiple cameras and/or multiple pipelines.
You can easily configure the edge device to run different models on the same stream,
or the same model on different streams.

## Prerequisites
Make sure you have completed all the prerequisites in the [Quickstart article](./quickstart-readme.md)

## Video stream configuration

1. Identify your RTSP source
RTSP streams are most often identified using an IP addresss.
Before proceeding, ensure you have the endpoint location information available for use in later steps.
If your streams require authentication, make sure you have the appropriate user names and passwords.

To understand how to map DeepStream pipeline configurations to different video sources,
we need to understand three items in the Controller Module's twin:

1. Sensors
1. Pipeline Configs
1. Streams

### Sensors

Open a deployment manifest template JSON file and search for the `sensors` section.
This section is an array of JSON objects, each of which looks like this:

    ```JSON
    {
        "name": "A unique ID among all the sensor objects",
        "kind": {
            "type": "vision",
            "subtype": "A descriptive subtype, like USB or RTSP"
        },
        "endpoint": "The URI for your video source",
        "regionsOfInterest": [
            "ROIs are covered in the tutorials"
        ]
    }
    ```

Note that the `"endpoint"` value can be any one of these:

* **File found inside the AI Pipeline container** Example: "file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.mp4"
* **File being streamed through RTSP Simulator** Example: "rtsp://rtspsim:554/media/retailshop-15fps.mkv"
* **IP camera** Example: "rtsp://192.168.15.115:554/live.sdp"
* **USB camera** Example: "/dev/video0"

Here is an example of a configured sensor:

    ```JSON
    "sensors": [
        {
            "name": "file-stream-01",
            "kind": {
                "type": "vision",
                "subtype": "FILE"
            },
            "endpoint": "file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.mp4"
        }
    ],
    ```

### Pipeline Configs

DeepStream Pipeline configurations are declared in the `"pipelineConfigs"` array.
Each object in the array is like this:

    ```JSON
    "pipelineConfigs": [
                        {
                            "id": "A unique ID among the pipelineConfigs",
                            "unsecureZipUrl": "URL of a zip file; optional",
                            "primaryModelConfigPath": {
                                "configFile":"CUSTOM_PARSER_EXAMPLES/yolov4/yolov4_nopostprocess.txt",
                                "parser": "yolov4"
                            }
                        }
    ]
    ```

We have covered the model configurations more extensively in other tutorials, such
as the [Pre-supported model path](./tutorial-prebuiltmodel-path.md).


### Streams

Once you have declared your sensors and your AI Pipeline configurations, you now
need to pair them up in whatever way you want.

In the JSON, you can find a `streams` section. This section is an array of JSON objects,
each of which looks like this:

```JSON
{
    "name": "The name from one of the sensors you declared",
    "uname": "User name if needed",
    "password": "Password if needed",
    "configId": "The name of the DeepStream pipeline configuration you want to run on this video source"
}
```

Here is an example:

Note: A username and password are not needed for this stream, so they are left empty.
If your video stream requires these, they can be provided here.

```JSON
        "streams": [
                            {
                                "name": "rtspsim",
                                "uname": "",
                                "password": "",
                                "configId": "PeopleDetection"
                            }
                        ]
```

### Examples

This example shows two video streams, the first a recorded video,
the second an RTSP endpoint.

```JSON
        "sensors": [
                        {
                            "name": "stream-01",
                            "kind": {
                                "type": "vision",
                                "subtype": "File"
                            },
                            "endpoint": "file:///opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.mp4"
                        },
                        {
                            "name": "stream-02",
                            "kind": {
                                "type": "vision",
                                "subtype": "RTSP"
                            },
                            "endpoint": "rtsp://127.0.0.1:8191/test"
                        }
        ]
```

In the example below, we make use of both of the declared sensors from the example above.
In this case, both streams are declared to use the *same* DeepStream pipeline configuration,
but if you have multiple pipeline configurations, you can configure each one to use a different
configuration if you'd like.

```JSON
        "streams": [
                            {
                                "name": "stream-01",
                                "uname": "",
                                "password": "",
                                "configId": "PeopleDetection"
                            },
                            {
                                "name": "stream-02",
                                "uname": "",
                                "password": "",
                                "configId": "PeopleDetection"
                            }
                        ]
```

## Alternative configurations
This example shows a separate source, or sensor, for each stream,
but many alternatives are possible.
- One Stream : Many Models -- If you want to run different models against the same video,
simply create multiple "sensors" using the same RTSP (or other source) endpoint.
- Many Streams : One Model -- Conversely, if you want to evaluate multiple cameras with the same model,
simply assign the same pipeline `configId` to each stream.
This is show in the above example, where `PeopleDetection' is assigned to different streams.
