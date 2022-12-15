# How to update the business logic in Azure DeepStream Accelerator

## Table of contents

* [Introduction](#introduction)
* [Prerequisites](#prerequisites)
* [Message Routing](#message-routing)
* [Example Business Logic Container Code Flow](#example-blc-code-flow)
* [Building the Business Logic Container](#building-the-blc)
* [Deploying the Business Logic Container](#deploying-the-blc)

## Introduction
The Business Logic Container module (BLC) is an important part of this solution.
It includes the elements necessary to act on the inferences provided by the computer vision (CV) model.

Fundamentally, the BLC is yours to build - it's where you will put your application. We provide a default one
here, but you should consider it an example, and you should modify it to do what you want.

The example BLC we provide shows a few things:

1. How to interact with the inferences coming out of the DeepStream pipeline(s).
1. How to tell the Video Uploader when and what to upload.
1. How to interact with regions of interest that are defined in the Player Widget.

Of these, the first two are likely to be in every solution that you make, while the third one
is optional (your application may not need regions of interest).

In our example, based on the simulated manufacturing box defect detection from the [Getting started path](./tutorial-getstarted-path.md),
we define an event to be at least one defective box present in a pre-defined ROI.
When this occurs, the BLC sends a message to the AI pipeline module.
This message causes the relevant video snippet to be sent to the Video Uploader, which then saves the snippets to blob storage.
When boxes are no longer detected in the ROI, a new message is sent that stops the recording of video snippets.
This relatively straightforward example illustrates how all the modules of this solution work together.
The BLC can be modified to do much more.

It can be modified to leverage most any CV model, evaluate much more complicated event conditions, and trigger a wide variety of business related actions.
To update the BLC to meet your business needs you will need to take the following steps:
- Parse model inferences
- Identify ROI intersections (optional)
- Evaluate event conditions
- Implement additional business actions

To better undestand how to leverage the code in this repository,
we will show you where and how these steps are completed for our defective box detection example.

## Prerequisites
- Make sure you have completed all the prerequisites in the [Quickstart article](./quickstart-readme.md).
- Familiarize yourself with your CV model and its output.
- Define your events and decide on your business logic.

## Message Routing

The Azure DeepStream Accelerator solution makes use of IoT Edge Routing, which is a mechanism to send messages
between IoT Edge modules. The messages are routed between end points, which are defined in the deployment
manifest. In the `edgeHub` section of the example deployment manifest template, you can see this section:

```JSON
        "routes": {
          "AIPipelineToHub": "FROM /messages/modules/ai-pipeline/outputs/* INTO $upstream",
          "ControllerToIoTHub": "FROM /messages/modules/controllermodule/outputs/* INTO $upstream",
          "ControllerToAIPipeline": "FROM /messages/modules/controllermodule/outputs/DeepStream INTO BrokeredEndpoint(\"/modules/ai-pipeline/inputs/Controller\")",
          "ControllerToBusinessLogic": "FROM /messages/modules/controllermodule/outputs/DeepStream INTO BrokeredEndpoint(\"/modules/BusinessLogicModule/inputs/inputRegionsOfInterest\")",
          "AIPipelineToBusinessLogic": "FROM /messages/modules/ai-pipeline/outputs/inference INTO BrokeredEndpoint(\"/modules/BusinessLogicModule/inputs/inferenceInput\")",
          "BusinessLogicToAIPipeline": "FROM /messages/modules/BusinessLogicModule/outputs/recordingOutput INTO BrokeredEndpoint(\"/modules/ai-pipeline/inputs/recordingInput\")"
        }
```

Here you can see that the BLC has the following endpoints defined:

* `inputRegionsOfInterest`: This is the endpoint for *receiving* messages from the Player Widget (technically from the Controller module, but that's an implementation detail).
* `inferenceInput`: This is the endpoint for *receiving* messages from the AI Pipeline module.
* `recordingOutput`: This is the endpoint for *sending* messages to the AI Pipeline module (which is how you will tell it to coordinate with the Video Uploader to upload video snippets).


## Example BLC code flow

Let's examine the code in the [example BLC source file](../business-logic-container/main.py).

Looking at the `main()` function:

```Python
def main():
    if not sys.version >= "3.5.3":
        raise Exception(
            "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version)
    print("IoT Hub Client for Python")

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print("IoTHubClient sample stopped by Edge")
        stop_event.set()

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Run the sample
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_sample(client))
    except Exception as e:
        print("Unexpected error %s " % e)
        raise
    finally:
        print("Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()
```

You can see that we create a `client`, which is an `IoTHubModuleClient` object - part of the Azure IoT Edge Python SDK.
The rest of the code in `main()` is mostly boilerplate - setting a termination handler for SIGTERM and running an asyncio loop.

The `create_client()` function is where we define handlers for the types of messages we might get from the other modules
in the Azure DeepStream Accelerator solution.

Specifically, we create the following handlers:

* Module twin patch handler: In case you want to use the BLC's module twin mechanism for configuration.
* Message handler for:
    - An `inputRegionsOfInterest` message, which is received from the Player Widget and which defines ROIs on each camera stream.
    To learn more about sending this message from the Player Widget, see the [relevant article](./how-to-usewebappwidget.md).
    - An `inferenceInput` message, from the AI Pipeline. These messages will be sent to the BLC on each frame of video.

You could also make use of [direct methods](https://docs.microsoft.com/en-us/azure/iot-hub/iot-hub-devguide-direct-methods)
in your BLC, but to keep things simple, we do not show this in the example.

### Module Twin

Here's the example code we use for parsing the module twin updates:

```python
    async def receive_twin_patch_handler(twin_patch):
        if "startRecording" in twin_patch:
            iot_msg = Message(json.dumps(twin_patch))
            await client.send_message_to_output(iot_msg, "recordingOutput")
```

In this simple example, all we do is create an IoT Edge Message (`azure.iot.device.Message` class) out of the JSON contents
we receive from the BLC's twin in the cloud.

Notice that we send the message on the `recordingOutput` endpoint (meaning that the AI Pipeline will pick up the message and act on it).

### Receiving Messages

We define a single handler for all messages that we receive from the other modules and switch based on the `message.input_name`
field, which defines the endpoint we received this message on:

```python
    # Define function for handling received messages
    async def receive_message_handler(message):
        # ......
        # ...... Code snipped here .....
        # ......

        if message.input_name == "inputRegionsOfInterest":
            # Code snipped here too....
            # Handle the messages from Player Widget that deal with updating ROIs
        elif message.input_name == "inferenceInput":
            # Code snipped here too....
            # Handle the messages from AI Pipeline - this is the bulk of what your application should be doing
```

### Parse regions of interest

Keep in mind that ROIs are an optional facet of the Azure DeepStream Accelerator solution - you don't need to handle ROIs
if your use case doesn't require them.

In our sample case, we are interested only in boxes if they are both malformed *and* within a particular region of interest (ROI).

The code in this section of the message handler simply updates our ROIs with whatever we received.

### Parse model inferences
The contents of the inference messages depend on the CV model that produced them.
And the inferences you care most about will depend on your business scenario.
In our exmaple, the `main.py` script imports `Inferences` from [inference_parser.py](../business-logic-container/InferenceParser/inference_parser.py)
and leverages it to transform the model output into more useful formats.
This transformation is conducted on each frame of the video,
with multiple detections, of different classes of objects, possible for each frame.

Depending on your model (and parser), you may need to modify this object and its logic.

Here is the implmentation contained in this repository.

```python
class Inferences:
    def __init__(self, message=None) -> None:
        if message is not None:
            self.parse_inferences(message=message)

    def parse_inferences(self, message):
        inferences_list = message["inferences"]
        self.inference_count = len(inferences_list)
        self.inferences_list = []
        self.pipeline_ids = []
        for i in inferences_list:
            inference = Inference()
            inference.from_json(i)
            self.pipeline_ids.append(inference.id)
            self.inferences_list.append(inference)
```

This class just walks through the list of inferences for the given frame(s) and parses
the JSON into an `Inference` object for each one.

The `Inference` class looks like this (and is found [here](../business-logic-container/InferenceParser/inference_parser.py)):

```Python
class Inference:
    def from_json(self, message):
        self.source_info = message["sourceInfo"]
        self.type = message["type"]
        self.id = message["id"]
        self.detections = []

        for d in message["detections"]:
            if self.type == "detection":
                result = ObjectDetectionResult()
                result.from_json(d)
                self.detections.append(result)
            elif self.type == "classification":
                result = ClassificationResult()
                result.from_json(d)
                self.detections.append(result)
            elif self.type == "segmentation":
                result = SegmentationResult()
                result.from_json(d)
                self.detections.append(result)
            elif self.type == "custom":
                result = CustomResult()
                result.from_json(d)
                self.detections.append(result)
```

You can see that this is just a switch statement (or rather, the Python equivalent) - it creates a particular type of Inference depending
on the `type` field in the JSON. All the different types of inferences are implemented in the same file.

Note that if your model does not adhere to one of the predefined types, you will need to write a `CustomResult` object
yourself to parse the JSON that your model produces from its parser.

For questions on exactly how the JSON looks, see [the technical specification for AI Pipeline outputs](./message-schema.md#ai-pipeline-to-blc).

### Identify ROI intersections
In our example, the transformed model output data is compared to the ROIs to determine if an inference bounding box overlaps with an ROI.
This is done using the `CalculateEvents` function.
Note that every detection that intersects an ROI is included in the `events` list that is returned by the function.
It is not necessary to use all of these events in the next step.

### Evaluate event conditions

Once we capture all the model inferences that intersect an ROI,
we look for events that are relevant to our scenario.

Note that if you choose not to use ROIs in your scenario, you can simply evaluate the
AI inference messages directly to determine if an event has occurred.

Our sample event trigger condition relates to how many defective boxes are detectied inside an ROI.
We want to record the video stream whenever a defective box is detected inside an ROI.
If there are no boxes detected, the signal gate remains closed and no video is recorded.

To accomplish this, we first count all the ROI intersections for the objects we care about, in each pipeline.
The names of the objects we are looking for are contained in `OBJECTS_TO_MONITOR`.
The contents of this list depends on your model output.

We then iterate through the pipelines to determine if the number of objects, defective boxes in our case, in an ROI meet the event condition.
If at least one defective box is detected inside an ROI, an event has occured and a `desired_action` message, to "start_recording", is sent to the AI pipeline module.
This message causes the video snippet to be sent to the Video Uploader, for transfer to cloud storage.
As long as at least one defective box is detected inside an ROI, video will continue to be saved.
When the model detects no defective boxes inside any ROI, the `desired_action` message is changed to "stop_recording".

```Python
    for pipeline_id in obj_inside_rois.keys():
        count = obj_inside_rois[pipeline_id]
        last_count = 0 if pipeline_id not in OBJECTS_INSIDE_ROIS.keys() else OBJECTS_INSIDE_ROIS[pipeline_id]
        if count > 0 and last_count==0:
            print("Sending START Recording Event")
            await trigger_recording_action(client=client, pipeline_name=pipeline_id, desired_action="start_recording")

        if count == 0 and last_count>0:
            print("Sending STOP Recording Event")
            await trigger_recording_action(client=client, pipeline_name=pipeline_id, desired_action="stop_recording")

        OBJECTS_INSIDE_ROIS[pipeline_id] = count
```

Remember, this event logic is specific to the CV model and the business scenario.
To define a different event, you will need to examine your model output and determine what transformed information will be returned by the `Inferences` function.
Once you finalize your event conditions, you can implement a similar signal gate and trigger your desired actions.

### Implement additional business actions

In this example, we simply trigger a video upload.
Now, let's assume we want to save the total box count and time of day to a database,
while keeping the same event condition.

To implement this enhancement, all we need to do is insert additional commands after the video recoding is initiated.
Keep in mind, any new logic and its relative complexity will very much depend on the business scenario.
The desired actions could be almost anything, limited only by the model, edge resources, and the imagination of the developer.

## Building the BLC

If you modify the BLC (which you will typically want to do to, since this is the main way you will add your business logic to Azure DeepStream Accelerator),
you will need to rebuild it. To do so, you currently need to use Docker's CLI, so make sure Docker is installed on your system.

Steps:

1. Go to the [business logic container's directory](../business-logic-container)
1. Make any changes to the source code (including adding your own files and assets).
1. Now build it:
    - x86 devices: `docker build --tag <whatever you want to call it> -f Dockerfile.amd64 .`
    - ARM devices: `docker buildx build --tag <whatever you want to call it> --load --platform linux/arm64 -f Dockerfile.arm .`
1. You will now have a Docker image on your system with whatever tag you gave it.

## Deploying the BLC

Once you have built your Docker image, you will need to push it to a container registry and then update the deployment manifest.

Steps:

1. Tag your image to point it to your container registry: `docker tag <the image you just built> <your registry's URL>/<whatever you want to call the image>:<tag>`.
For example, `docker tag image-I-just-built whatever.azurecr.io/business-logic:best-version-yet`.
1. Now push your image: `docker push <whatever you just tagged it as>`, for example: `docker push whatever.azurecr.io/business-logic:best-version-yet`.
1. If you upload your container to the same place as your AI Pipeline containers, you can skip this step. Otherwise,
you must modify your deployment manifest template ([ARM](../ds-ai-pipeline/arm/deployment.default.template.json) or [x86](../ds-ai-pipeline/x86_64/deployment.default.template.json)).

    You need to update the `registryCredentials` section with another section - one for your new container registry:

            ```JSON
            "registryCredentials": {
                "test-images": {
                    "address": "$CONTAINER_REGISTRY_NAME",
                    "password": "$CONTAINER_REGISTRY_PASSWORD",
                    "username": "$CONTAINER_REGISTRY_USERNAME"
                },
                "your-new-container-registry": {  // Name this whatever you want
                    "address":  "$BLC_REGISTRY_NAME",
                    "password": "$BLC_REGISTRY_PASSWORD",
                    "username": "$BLC_REGISTRY_USERNAME"
                }
            }
            ```
1. Now modify the `.env` file that corresponds to your template to make the following changes:
    * Update the `BUSINESS_LOGIC_IMAGE_URI` to point to the URI for your newly uploaded container.
    * If you added container registry credentials in the previous step, you need to also add these values:
    `BLC_REGISTRY_NAME` (the URL for the registry), `BLC_REGISTRY_PASSWORD` (the password for your registry),
    and `BLC_REGISTRY_USERNAME` (the username for your registry).
1. Now regenerate your deployment manifest by right-clicking the template in VS Code and selecting
"Generate IoT Edge Deployment Manifest".
1. Now deploy the new solution by right-clicking on the generated deployment manifest in VS Code and selecting
"Create Deployment for Single Device".
