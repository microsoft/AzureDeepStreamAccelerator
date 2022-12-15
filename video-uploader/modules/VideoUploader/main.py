# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import time
from datetime import datetime, timezone
import uuid
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import IoTHubModuleClient
from azure.storage.blob import BlobClient
from azure.iot.device import Message
from azure.core.exceptions import (
    ClientAuthenticationError,
    HttpResponseError,
    ServiceRequestError,
    ResourceNotFoundError,
    ResourceExistsError,
    AzureError
)
import logging
import pprint
import json
from opentelemetry.sdk._logs import (
    LogEmitterProvider,
    LoggingHandler,
    set_log_emitter_provider,
)
from opentelemetry.sdk._logs.export import BatchLogProcessor
from opentelemetry.sdk.resources import Resource
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter

class threadName(logging.Filter):
    def filter(self, record):
        acceptedThreadMap ={
            'OtelBatchLogProcessor': False
        }
        return acceptedThreadMap.get(record.threadName, True)

log_emitter_provider = LogEmitterProvider(
    resource = Resource.create({
            "service.name": "container-telemetry",
            # "service.instance.id": "instance-12",
    }),
)
set_log_emitter_provider(log_emitter_provider)


logger = logging.getLogger(__name__)

print('Starting Video Uploader')
logger.debug("This is a test debug logging message")
logger.info("This is a test info logging message")
logger.warning("This is a test warning logging message")
logger.error("This is a test error logging message")
logger.critical("This is a test critical logging message")

appInsightsConfigFileName = 'config.json'
appInsightsConnectionStr = None

if os.path.isfile(appInsightsConfigFileName) and os.path.getsize(appInsightsConfigFileName) >= 2:
    appInsightsConfigFile = open(appInsightsConfigFileName, encoding='utf-8-sig')
    appInsightsConfigFileData = json.load(appInsightsConfigFile)
    appInsightsConnectionStr = appInsightsConfigFileData.get('appInsightsConnectionStr')

    if appInsightsConnectionStr:
        exporter = AzureMonitorLogExporter.from_connection_string(appInsightsConnectionStr)
        logMap = {
            'Debug': logging.DEBUG,
            'Information': logging.INFO,
            'Warning': logging.WARNING,
            'Error': logging.ERROR,
            'Critical': logging.CRITICAL
        }
        logLevelVar = logMap.get(appInsightsConfigFileData.get('logLevel'), logging.NOTSET)
        log_emitter_provider.add_log_processor(BatchLogProcessor(exporter))
        handler = LoggingHandler()
        handler.addFilter(threadName())

        # Attach LoggingHandler to root logger
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logLevelVar)
        print('appInsightsConnectionStr found updating logging endpoint')
    else:
       print('appInsightsConnectionStr not found in config.json, will not log to App Insights') 
else:
    print('config.json not found, will not log to App Insights')

# monitor for appInsightsConnectionStr update and restart container if updated to pickup change.
def check_for_appInsightsConnectionStr_update():
    global appInsightsConnectionStr
    newAppInsightsConnectionStr = None
    # print("checking for appInsightsConnectionStr update")
    if os.path.isfile(appInsightsConfigFileName) and os.path.getsize(appInsightsConfigFileName) >= 2:
        appInsightsConfigFile = open(appInsightsConfigFileName, encoding='utf-8-sig')
        appInsightsConfigFileData = json.load(appInsightsConfigFile)
        newAppInsightsConnectionStr = appInsightsConfigFileData.get('appInsightsConnectionStr')

    # print("AppInsightsConnectionStr: {}".format(appInsightsConnectionStr))
    # print("newAppInsightsConnectionStr: {}".format(newAppInsightsConnectionStr))
    
    if newAppInsightsConnectionStr != appInsightsConnectionStr:
        print('appInsightsConnectionStr updated, restarting container to update logger handler')
        os._exit(os.EX_OK)



# for k, v in sorted(os.environ.items()):
#     print(k+':', v)
# print('\n')
# list elements in path environment variable
# [print(item) for item in os.environ['PATH'].split(';')]

# IOTHUB_DEVICE_CONNECTION_STRING = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
IOTHUB_DEVICE_CONNECTION_STRING = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
# print(IOTHUB_DEVICE_CONNECTION_STRING)

# Placeholders for Blob path and file Metadata until we get this data parsed via json
azureSubscription = '00000000-0000-0000-0000-000000000000'
providers = 'Microsoft.AzurePercept' 
resourceGroup = 'ResourceGroup'
accountName = 'Account'
solutionInstance = 'SolutionInstance'
deviceID = os.environ["IOTEDGE_DEVICEID"]
sensor = 'SensorName'
skill = 'SkillName'
label = 'LabelName'
event = 'Change'
eventValue = '2' # add_metadata_headers requires string
regionOfInterest = 'label1'
frameRate = '30'
date = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
error_Message = ''


async def blob_upload_request(device_client, blob_name, file, sensorId = None):
    # need to create semaphore so we never have more then 10 outstanding uploads at a time when multithreading is added 
    storage_info = await device_client.get_storage_info_for_blob(blob_name)
    result = {"status_code": -1, "status_description": "N/A"}

    # Using the Storage Blob V12 API, perform the blob upload.
    try:
        # print('sensorId in upload_request: {}'.format(sensorId))
        upload_result = await store_blob(storage_info, file, sensorId = sensorId)
        print("upload result: {}".format(upload_result))
        # for att in dir(upload_result[1]):
        #    print(f'{att} : {getattr(upload_result[1],att)}\n')

        if hasattr(upload_result[1], "error_code"):
            result = {
                "status_code": upload_result[1].error_code,
                "status_description": "Storage Blob Upload Error",
            }
        else:
            result = {"status_code": 200, "status_description": ""}
            #remove uploaded file from Cache
            os.remove(file)

    except ResourceExistsError as ex:
        if ex.status_code:
            result = {"status_code": ex.status_code, "status_description": ex.reason}
        else:
            print("Failed with Exception: {}", ex)
            result = {"status_code": 400, "status_description": ex.message}

    print("parsed upload result: {}".format(result))
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(result)

    if result["status_code"] == 200:
        await device_client.notify_blob_upload_status(
            storage_info["correlationId"],
            True,
            result["status_code"],
            result["status_description"]
        )
    else:
        await device_client.notify_blob_upload_status(
            storage_info["correlationId"],
            False,
            result["status_code"],
            result["status_description"],
        )



async def store_blob(blob_info, file_name, sensorId = None):
    global error_Message
    try:
        sas_url = "https://{}/{}/{}{}".format(
            blob_info["hostName"],
            blob_info["containerName"],
            blob_info["blobName"],
            blob_info["sasToken"]
        )

        account_url = blob_info["hostName"]
        container_name = blob_info["containerName"]
        blob_name = blob_info["blobName"]

        if os.getenv("BLOB_STORAGE_ACCOUNT_KEY"):
            credential = os.getenv("BLOB_STORAGE_ACCOUNT_KEY")
        else:
            credential = blob_info["sasToken"]


        print("\nUploading file: {} to Azure Storage as blob: {} in container {}\n".format(file_name, blob_info["blobName"], blob_info["containerName"]))
        # print correlationId in case we crash and need to manually close out the upload
        # on the IoT Hub so we don't have wait for the 1 hour TTL to expire
        print("correlationId: {}".format(blob_info["correlationId"]))
        print("SAS URL: {}".format(sas_url))

        sensorMetaData = "/subscriptions/{}/resourceGroups/{}/providers/{}/accounts/{}/devices/{}/sensors/{}".format(
            azureSubscription,
            resourceGroup,
            providers, 
            accountName,
            deviceID,
            sensor
        )

        solutionInstanceMetaData = "/subscriptions/{}/resourceGroups/{}/providers/{}/accounts/{}/solutionInstances/{}".format(
            azureSubscription,
            resourceGroup,
            providers, 
            accountName,
            solutionInstance
        )

        # print('sensorId in Store_Blob: {}'.format(sensorId))
        if sensorId:
            metaData = {
                'sensorId': sensorId
            }
        else:
            metaData = {
                'event': event,
                'eventvalue': eventValue,
                'regionofinterest': regionOfInterest,
                'sensor': sensorMetaData,
                'solutioninstance': solutionInstanceMetaData
                }
        if error_Message:
            metaData.update(Error_Message = error_Message)
            error_Message = ''

        # [conditions-and-known-issues] https://docs.microsoft.com/en-us/azure/storage/blobs/storage-manage-find-blobs?tabs=azure-portal#conditions-and-known-issues
        # Blob index tags are only supported on General Purpose v2 storage accounts.
        # Blob index tags only support string data types and querying returns results with lexicographical ordering. For numbers, zero pad the number. For dates and times, store as an ISO 8601 compliant format.
        # https://en.wikipedia.org/wiki/ISO_8601 example Date: '2022-06-27T13:12:30Z'
        # Blob index tags require additional permissions [Bug for the python SDK] https://github.com/Azure/azure-iot-sdk-python/issues/1026 as work around using storage account shared key

        indexTagData = {
            'Date': date,
            'Sensor' : sensor
        }

        pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(metaData)
        #sas_url
        # Upload the specified file
        with BlobClient(account_url, container_name, blob_name, credential = credential) as blob_client:
            with open(file_name, "rb") as f:
                result = blob_client.upload_blob(f, overwrite=True)
            try:
                blob_client.set_blob_tags(tags=indexTagData)
            except HttpResponseError as ex:
                if ex.error_code == 'BlobTagsNotSupportedForAccountType':
                    # Blob index tags are only supported on General Purpose v2 storage accounts.
                    print('BlobTagsNotSupportedForAccountType, uploading without index tags')
                    metaData.update(Error_Message = 'Blob index tags are only supported on General Purpose v2 storage accounts.')
                    blob_client.set_blob_metadata(metadata=metaData)
                elif ex.error_code == 'AuthorizationPermissionMismatch':
                    # Blob index tags are only supported on General Purpose v2 storage accounts.
                    print('AuthorizationPermissionMismatch, uploading without index tags')
                    metaData.update(Error_Message = 'AuthorizationPermissionMismatch, Blob index tags are a subresource to the blob data. A user with permissions or a SAS token to read or write blobs may not have access to the blob index tags.')
                    blob_client.set_blob_metadata(metadata=metaData)
                else:
                    print('Trying to reraise exception')
                    raise Exception(ex)
            else:
                blob_client.set_blob_metadata(metadata=metaData)
            return (True, result)

    except FileNotFoundError as ex:
        # catch file not found and add an HTTP status code to return in notification to IoT Hub
        ex.status_code = 404
        return (False, ex)

    except AzureError as ex:
        # catch Azure errors that might result from the upload operation
        return (False, ex)


async def main():
    module_client = IoTHubModuleClient.create_from_edge_environment()
    module_client.connect()
    conn_str = IOTHUB_DEVICE_CONNECTION_STRING
    device_client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    cache = '/app/VideoUploaderCache'

    # clean cache on startup
    for f in os.listdir(cache):
        os.remove(os.path.join(cache, f))

    # File watch list in Cache
    cacheFileList = {}
    ioBufferFlushToDiskTimer = datetime.now()
    checkForStreamingFileUPdates = False
    while(True):
        global regionOfInterest, sensor, event, eventValue, skill, label, date, error_Message

        if (datetime.now() - ioBufferFlushToDiskTimer).total_seconds() > 20:
            checkForStreamingFileUPdates = True
            print("Checking for streaming File updates: {}".format((datetime.now() - ioBufferFlushToDiskTimer).total_seconds()))

        # check for update to check for appInsightsConnectionStr
        if checkForStreamingFileUPdates:
            check_for_appInsightsConnectionStr_update()

        # iterate over files in Cache
        for filename in os.listdir(cache):

            file = os.path.join(cache, filename)
            
            # Check for Hi-Res snapshot PNG
            if os.path.isfile(file) and file.endswith(".png"):
                png_blob_path = None
                png_storage_info = None
                png_tags = None
                png_sensorId_tag = None
                # check for config file
                # pngConfigJsonFileNames are 101 char for Tennant requests and 36 char for Global requests not counting the png timestamp
                if len(filename) > 100:
                    pngConfigJsonFileName = filename[:101] + '_config.json'
                else:
                    pngConfigJsonFileName = filename[:36] + '_config.json'            
                print('Found Hi-Res SnapShot: {}'.format(filename))
                print('Looking for pngConfigJsonFileName: {}'.format(pngConfigJsonFileName))
                pngConfigJsonFileName = os.path.join(cache, pngConfigJsonFileName)
                if not os.path.isfile(pngConfigJsonFileName):
                    print("No config file found for png, waiting one second for delayed cache write")
                    time.sleep(1)
                if os.path.isfile(pngConfigJsonFileName) and os.path.getsize(pngConfigJsonFileName) >= 2:
                    pngConfigJsonFile = open(pngConfigJsonFileName, encoding='utf-8-sig')
                    pngConfigJsonFileData = json.load(pngConfigJsonFile)
                    png_blob_path = pngConfigJsonFileData.get('AssetName')
                    png_storage_info = pngConfigJsonFileData.get('StorageInfo')
                    if png_storage_info:
                        png_tags = png_storage_info.get('Tags')
                        if png_tags:
                            png_sensorId_tag = png_tags.get('sensorId')
                else:
                    print("No config file found for png")

                if png_blob_path:
                    # print('sensorId in main: {}'.format(png_sensorId_tag))
                    await blob_upload_request(device_client, png_blob_path, file, sensorId = png_sensorId_tag)
                    await blob_upload_request(device_client, png_blob_path + '_config.json', pngConfigJsonFileName, sensorId = png_sensorId_tag)
                else:
                    # attempt upload of file
                    # get the Storage SAS information from IoT Hub, it auto prepends the device name to the blob path returned.
                    blob_path = ( resourceGroup + '/'
                                + accountName  + '/'
                                + solutionInstance + '/'
                                + sensor + '/'
                                + skill + '/' 
                                + label + '/')
                            
                    blob_png_name = blob_path + os.path.basename(file)
                    await blob_upload_request(device_client, blob_png_name, file)

            # checking if it is a mp4 file
            hasInferenceJson = False
            liveAIVideo = False  # different parsing for Live AI 
            if os.path.isfile(file) and file.endswith(".mp4"):
                if file not in cacheFileList:
                    #new file add file to watch list
                    file_size = os.path.getsize(file)
                    print('New file adding to watch list')
                    print('Found mp4 file in cache: {} {}'.format(file, file_size))
                    cacheFileList[file] = file_size
                elif checkForStreamingFileUPdates:
                    file_size = os.path.getsize(file)
                    print('mp4 file in cache: {} {}'.format(file, file_size))
                    print('in watch list, checking file size growth')
                    print('old size is {} new file size is {}'.format(cacheFileList[file], file_size))
                    
                    if file_size > cacheFileList[file]:
                        print('file still growing, keep monitoring for changes')
                        # update current size
                        cacheFileList[file] = file_size
                    elif file_size < 20480:
                        print('file is less then 20kb, keep monitoring for changes')
                    else:
                        print('file size is static and larger than 20kb assuming ready for upload')
                        # check for assoicated P4D inference json with mp4 file
                        inferenceFile = file.replace(".mp4", ".json")
                        if os.path.isfile(inferenceFile) and os.path.getsize(inferenceFile) >= 2:
                            print("found mp4 inference file {}".format(inferenceFile))
                            hasInferenceJson = True
                            # parse json and update tags
                            inferenceData = json.load(open(inferenceFile))
                            inferenceDataIoTMessage = json.dumps(inferenceData)
                            # send inference to App Insights if configured
                            logger.info(inferenceDataIoTMessage)
                            # limit IoT message size to first 200,000 characters to fit IoT hub limit of 256KB 
                            msg = Message(inferenceDataIoTMessage[:200000])
                            msg.content_encoding = "utf-8"
                            msg.content_type = "application/json"
                            # print("Sending IoT Hub message: {}".format(msg))
                            module_client.send_message(msg)
                            print("IoT Hub Message successfully sent")
                            # Assumes a valid json schema
                            if len(inferenceData['regionsOfInterest']) > 0:
                                regionOfInterest = inferenceData['regionsOfInterest'][0]['label']
                                sensor = inferenceData['regionsOfInterest'][0]['sensor']
                            else:
                                error_Message = 'did not find any RoIs in the inference file {}'.format(inferenceFile)

                            if len(inferenceData['events']) > 0:
                                event = inferenceData['events'][0]['type']
                                eventValue = json.dumps(inferenceData['events'][0]['userDefinedData'])
                            else:
                                error_Message = 'did not find any events in the inference file {}'.format(inferenceFile)

                            if len(inferenceData['inferences']) > 0:
                                skill = inferenceData['inferences'][0]['type']
                                date = inferenceData['inferences'][0]['sourceInfo']['timestamp']
                                if len(inferenceData['inferences'][0]['detections']) > 0:
                                    inferenceDataLabel = inferenceData['inferences'][0]['detections'][0].get('label')
                                    if inferenceDataLabel:
                                        label = inferenceDataLabel
                                    else:
                                        error_Message = 'first inference detection has no label in the inference file {}'.format(inferenceFile)
                                else:
                                   error_Message = 'did not find any detections in first inference in the inference file {}'.format(inferenceFile) 
                            else:
                                error_Message = 'did not find any inferences in the inference file {}'.format(inferenceFile)
                        else:
                            print("did not find mp4 inference file {}".format(inferenceFile))
                            date = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                            error_Message = 'did not find mp4 inference file {}'.format(inferenceFile)

                        # attempt upload of file
                        # get the Storage SAS information from IoT Hub, it auto prepends the device name to the blob path returned.
                        blob_path = ( resourceGroup + '/'
                                    + accountName  + '/'
                                    + solutionInstance + '/'
                                    + sensor + '/'
                                    + skill + '/' 
                                    + label + '/')
                        
                        blob_mp4_name = blob_path + os.path.basename(file)
                        blob_json_name = blob_path + os.path.basename(inferenceFile)

                        await blob_upload_request(device_client, blob_mp4_name, file)

                        if hasInferenceJson:
                            await blob_upload_request(device_client, blob_json_name, inferenceFile)

                        #remove uploaded mp4 file from watch list
                        print('removing file from watch list after upload')
                        cacheFileList.pop(file)


        # Reset IO buffer flush to disk timer and flag if needed
        if checkForStreamingFileUPdates:
            ioBufferFlushToDiskTimer = datetime.now()
            checkForStreamingFileUPdates = False

    # Finally, shut down the client
    await device_client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())