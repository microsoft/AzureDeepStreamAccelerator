import argparse
import asyncio
import json
import logging
import os
import rtsp_out
import signal
import sys
import threading
import time
from azure.iot.device.aio import IoTHubModuleClient
from multiprocessing import Queue
from TwinParser import Twin
from opentelemetry.sdk._logs import (
    LogEmitterProvider,
    LoggingHandler,
    set_log_emitter_provider,
)
from opentelemetry.sdk._logs.export import BatchLogProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter

# global counters
twin = Twin.get_instance()

# Event indicating client stop
stop_event = threading.Event()

class ThreadName(logging.Filter):
    def filter(self, record):
        acceptedThreadMap = {
            # Turn off the below thread's logging
            'OtelBatchLogProcessor': False
        }
        return acceptedThreadMap.get(record.threadName, True)

def set_log_level(message_json):
    """
    Attempt to set the log level based on the controller module's message.
    """
    # Set the log level from the module twin
    if "logLevel" in message_json and type(message_json['logLevel']) == str:
        leveldict = {
            "DEBUG": logging.DEBUG,
            "INFORMATION": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        if message_json['logLevel'].upper() in leveldict.keys():
            level = leveldict[message_json['logLevel'].upper()]
            logging.info(f"Updating log level to {message_json['logLevel'].upper()}")
            logging.getLogger().setLevel(level)
        else:
            logging.error(f"Given a loglevel that is not supported. First 10 characters given: {message_json['logLevel'][:10]}. Supported values are {[k for k in leveldict.keys()]}")
    elif "logLevel" in message_json:
        logging.error(f"logLevel should be a string but given a {type(message_json['logLevel'])} instead.")

def set_new_pipeline(message_json, message):
    """
    Attempt to set a new pipeline based on the controller module's message.
    """
    if "deepStream" in message_json:
        logging.info("Updating pipeline configurations.")
        twin.parse_twin_message(message.data.decode('utf-8-sig'))
        twin.updated = True
        logging.info("Terminating pipelines to restart with new configuration.")
        rtsp_out.terminate_pipelines()

def set_start_recording(message_json, message_text):
    """
    Start recording if given the right stuff in the JSON from the BLC module.
    """
    if "startRecording" in message_json:
        logging.debug(f"Received a message on the recordingInput endpoint: {message_json}")
        # Set the start recording event for all the running pipelines
        for pipeline in message_json['startRecording']:
            if pipeline['configId'] in twin.pipelines:
                if pipeline['state']:
                    logging.info(f"Received recording message for {pipeline['configId']}. Setting pipeline state to RECORD.")
                    twin.pipelines[pipeline['configId']].startRecording.set()
                else:
                    logging.info(f"Received recording message for {pipeline['configId']}. Setting pipeline state to NOT RECORDING.")
                    twin.pipelines[pipeline['configId']].startRecording.clear()
            else:
                logging.warning(f"Invalid pipeline configId received on recordingInput endpoint. Received: {pipeline['configId']}")
    else:
        logging.warning("Received a message on the recordingInput endpoint, but it does not contain 'startRecording'. Discarding.")


def create_client():
    """
    Create the IoT Client.
    """
    client = IoTHubModuleClient.create_from_edge_environment()

    # Define function for handling received messages
    async def receive_message_handler(message):
        if message.input_name == "Controller":
            logging.info("Received message from Controller module")
            # We have received a message from Controller.
            message_text = message.data.decode('utf-8-sig')
            message_json = json.loads(message_text)
            set_log_level(message_json)
            set_new_pipeline(message_json, message)
        elif message.input_name == "recordingInput":
            message_text = message.data.decode('utf-8')
            message_json = json.loads(message_text)
            set_start_recording(message_json, message_text)

    # Define function for handling received twin patches
    async def receive_twin_patch_handler(twin_patch):
        logging.info(f"Twin Patch received")
        logging.info(f"{twin_patch}")
        if "outputVideoLength" in twin_patch:
            length = twin_patch["outputVideoLength"]
            logging.info(f"Updating max video length from {twin.output_video_length} to {length} seconds.")
            twin.output_video_length = length

    try:
        # Set handler on the client
        client.on_message_received = receive_message_handler
        client.on_twin_desired_properties_patch_received = receive_twin_patch_handler
    except Exception as e:
        # Cleanup if failure occurs
        logging.error(f"An unexpected error occurred while trying to set handlers on IoT client: {e}")
        client.shutdown()
        raise

    logging.info (f"IoT Client Created")
    return client

def run_ai_pipeline(msg_queue):
    """
    Main entrypoint for AI pipeline thread.
    """
    while True:
        if twin.updated:
            twin.updated = False
            rtsp_out.build_pipelines(msg_queue)
        else:
            time.sleep(1)

async def send_messages_to_iot_hub(client, msg_queue):
    """
    Waits around for messages to upload to IoT Hub.
    """
    while True:
        # Block until we get a message
        msg = msg_queue.get()
        json_msg = json.dumps(msg)
        try:
            logging.debug("Sending message to inference output:", msg)
            await client.send_message_to_output(json_msg, "inference")
        except Exception as e:
            logging.exception(f"Unexpected error {e}")
            raise

def main():
    if not sys.version >= "3.5.3":
        raise Exception(f"This program requires python 3.5.3+. Current version of Python: {sys.version}")

    # Get application arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loglevel', '-l', choices=('debug', 'info', 'warning', 'error'), default='info', help="The logging level.")
    parser.add_argument('--logfile', '-f', type=str, default=None, help="If given, we log to the given file.")
    args = parser.parse_args()

    # Check if loglevel is present in environment for override
    loglevel = os.environ.get('AI_PIPELINE_LOG_LEVEL', args.loglevel).upper()
    if not hasattr(logging, loglevel):
        print(f"Loglevel cannot be set to {loglevel}. Choices are 'DEBUG', 'INFO', 'WARNING', 'ERROR'. Setting to default 'INFO' level.")
        loglevel = "INFO"

    # Set logging parameters
    logformat = '[%(asctime)-15s] [%(name)s] [%(levelname)s]: %(message)s'
    loghandlers = [logging.StreamHandler(sys.stdout)]
    if args.logfile is not None:
        loghandlers.append(logging.FileHandler(args.logfile))
    logging.basicConfig(level=getattr(logging, loglevel), format=logformat, force=True, handlers=loghandlers)

    # Azure Monitor Logger
    if "APPLICATIONINSIGHTS_CONNECTION_STRING" in os.environ:
        conn_str = os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]
        logging.info(f"Sending logs to Azure Monitor.")
        log_emitter_provider = LogEmitterProvider()
        set_log_emitter_provider(log_emitter_provider)
        try:
            exporter = AzureMonitorLogExporter.from_connection_string(conn_str)

            log_emitter_provider.add_log_processor(BatchLogProcessor(exporter))
            handler = LoggingHandler()
            handler.addFilter(ThreadName())

            # Attach LoggingHandler to root logger
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(getattr(logging, args.loglevel.upper()))
        except ValueError as e:
            logging.error(f"Exception occured with Azure Monitor setup: {e}")
    else:
        logging.info("Set APPLICATIONINSIGHTS_CONNECTION_STRING env var to enable sending logs to Azure Monitor.")

    # Set all loggers to the appropriate log level - azure loggers are too verbose; set them to WARNING
    for name in logging.root.manager.loggerDict:
        if "azure" in name:
            logging.getLogger(name).setLevel("WARNING")

    msg_queue = Queue()

    # Create an IoT Edge Client object with handlers for messages.
    client = create_client()

    # Create an AI Pipeline thread.
    pipe_thread = threading.Thread(target=run_ai_pipeline, name="AI Pipeline", args=(msg_queue,))
    pipe_thread.start()

    # Define a handler to cleanup when module is terminated by Edge
    def module_termination_handler(signal, frame):
        logging.info ("IoTHubClient stopped by Edge")
        stop_event.set()

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_messages_to_iot_hub(client, msg_queue))
    except Exception as e:
        logging.exception(f"Unexpected error {e}")
        raise
    finally:
        logging.info(f"Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()
        pipe_thread.join()

if __name__ == "__main__":
    main()
