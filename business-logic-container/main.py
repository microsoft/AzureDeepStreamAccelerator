# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import  Message
from InferenceParser import Inferences, Inference
from TwinParser import Twin
import asyncio
import logging
import json
import sys
import signal
import threading

OBJECTS_TO_MONITOR=["person", "defect"]
OBJECTS_INSIDE_ROIS={}

# parse the twin received from the controller
twin = Twin.get_instance()

# Event indicating client stop
stop_event = threading.Event()

async def trigger_recording_action(client, pipeline_name, desired_action):
    """
    Packages and sends a message for use
    by the ai-pipeline container to start
    or stop recording
    """
    if desired_action == "start_recording":
        start_recording = True
    elif desired_action == "stop_recording":
        start_recording = False

    data =  {
        "startRecording": [
            {
            "configId": pipeline_name,
            "state": start_recording
            }
        ]
    }
    iot_msg = Message(json.dumps(data))
    await client.send_message_to_output(iot_msg, "recordingOutput")

async def check_inference_for_roi_match(inf: Inference, obj_inside_rois):
    """
    Checks all detections inside the inference to see if any of them are:

    * An object we are interested in
    * AND inside an ROI we have defined
    """
    match inf.type:
        case "detection":
            inference_id = inf.id
            sensor_name = inf.source_info["id"]

            if sensor_name not in twin.sensors.keys():
                logging.debug(f"Detected {inference_id} on sensor {sensor_name}, but we are not tracking this sensor, so ignoring.")
                return

            # For each ROI defined on this sensor,
            # check all detections in the inference for presence inside the ROI.
            obj_inside_rois[inference_id] = 0
            for roi in twin.sensors[sensor_name].regions_of_interest:
                for det in inf.detections:
                    if det.label.lower() in OBJECTS_TO_MONITOR and roi.contains( det.get_bbox_center() ):
                        logging.info(f"Detected {det.label} inside {roi}.")
                        obj_inside_rois[inference_id] += 1
                    elif det.label.lower() in OBJECTS_TO_MONITOR:
                        logging.debug(f"Detected {det.label}, but it is not in {roi}.")
                    elif det.label.lower() not in OBJECTS_TO_MONITOR:
                        logging.debug(f"Detected {det.label}, which is not one of the objects we are monitoring. Discarding.")
        case _:
            logging.warning(f"Got an inference of type {inf.type}, which I do not understand.")

def create_client():
    """
    Create an IoTHubModuleClient and attach handlers to it for messages we receive.
    """
    client = IoTHubModuleClient.create_from_edge_environment()

    async def receive_message_handler(message):
        """
        Handler function for all messages the BLC receives.
        """
        global OBJECTS_INSIDE_ROIS, OBJECTS_TO_MONITOR

        logging.debug(f"Message received: {message.data}; Properties: {message.custom_properties}")

        # Decode the bitstream into JSON
        message_text = message.data.decode('utf-8')
        message_json = json.loads(message_text)

        # Check the endpoint of the message and respond appropriately.
        match message.input_name:
            case "inputRegionsOfInterest":
                logging.info("Received message on 'inputRegionsOfInterest' endpoint. Updating ROIs.")

                ada_skill = message_json
                twin.parse_sensors(ada_skill)

                # Reset this global variable because ROIs have changed.
                OBJECTS_INSIDE_ROIS={}
            case "inferenceInput":
                logging.info("Received message on 'inferenceInput' endpoint.")

                inferences = Inferences(message=message_json)

                # Update the number of detections for each ROI on each pipeline.
                obj_inside_rois={ key : 0 for key in list(set(inferences.pipeline_ids)) }
                for inf in inferences.inferences_list:
                    await check_inference_for_roi_match(inf, obj_inside_rois)

                for pipeline_id in obj_inside_rois.keys():
                    count = obj_inside_rois[pipeline_id]
                    last_count = 0 if pipeline_id not in OBJECTS_INSIDE_ROIS.keys() else OBJECTS_INSIDE_ROIS[pipeline_id]
                    if count > 0 and last_count == 0:
                        logging.info("Detected an object of interest inside a region of interest and we are not already recording. Sending START signal.")
                        await trigger_recording_action(client=client, pipeline_name=pipeline_id, desired_action="start_recording")
                    elif count == 0 and last_count > 0:
                        logging.info("Did not detect anything of interest in any ROIs and we are currently recording. Sending STOP signal.")
                        await trigger_recording_action(client=client, pipeline_name=pipeline_id, desired_action="stop_recording")

                    OBJECTS_INSIDE_ROIS[pipeline_id] = count

    async def receive_twin_patch_handler(twin_patch):
        """
        Handler for module twin, in case we want to define any configurations
        by that mechanism.
        """
        logging.info(f"Twin Patch received: {twin_patch}")

        # In this example, we allow a 'start recording' event to be triggered manually by including it in
        # this container's module twin configuration.
        if "startRecording" in twin_patch:
            iot_msg = Message(json.dumps(twin_patch))
            await client.send_message_to_output(iot_msg, "recordingOutput")

    try:
        # Set handler on the client
        client.on_message_received = receive_message_handler
        client.on_twin_desired_properties_patch_received = receive_twin_patch_handler
    except Exception as e:
        # Cleanup if failure occurs
        logging.error(f"We could not set up the IoT message handlers for some reason: {e}")
        client.shutdown()
        raise

    return client

async def run_sample(client):
    # Customize this coroutine to do whatever tasks the module initiates
    while True:
        await asyncio.sleep(1000)

def main():
    # Set logging parameters
    logformat = '[%(asctime)-15s] [%(name)s] [%(levelname)s]: %(message)s'
    loghandlers = [logging.StreamHandler(sys.stdout)]
    logging.basicConfig(level=logging.INFO, format=logformat, force=True, handlers=loghandlers)

    # Here we create an IoT client, which will do most of the work for us in handlers we define.
    client = create_client()

    # Define a handler to cleanup when module is terminated by Edge
    def module_termination_handler(signal, frame):
        logging.info("IoTHubClient sample stopped by Edge")
        stop_event.set()

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Run the sample
    loop = asyncio.get_event_loop()
    try:
        # Here we run any main-loop logic we might need.
        loop.run_until_complete(run_sample(client))
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        logging.info("Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()

if __name__ == "__main__":
    main()
