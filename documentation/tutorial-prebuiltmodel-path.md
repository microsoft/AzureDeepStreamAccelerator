# Tutorial: Azure DeepStream Accelerator - Pre-built model path

In this tutorial, you’ll learn how to use [Azure DeepStream Accelerator’s](../README.md#azure-deepstream-accelerator-overview) pre-built model path to build and upload a container that includes a computer vision (CV) model using your own video stream and one of the pre-built models we support. You’ll learn how to configure a Real Time Streaming Protocol (RTSP) video stream so that you can use it with your Edge artificial intelligence (AI) solution and customize event detection by updating the region of interest (ROI).

This tutorial guides you through the seven major steps to create an Edge AI solution using Azure DeepStream Accelerator’s pre-built model path:

- Step 1: Confirm your Edge modules are running
- Step 2: Identify your RTSP source
- Step 3: Prepare and upload your container
- Step 4: Update the deployment manifest
- Step 5: Deploy your updates to your Edge device
- Step 6: Modify the regions of interest
- Step 7: Use the Player web app to verify your results

## Prerequisites

Before beginning this tutorial, make sure you have:

- Completed all the prerequisites in [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md).
- A pre-trained computer vision (CV) model from a model zoo. This model should be any one of the pre-built AI Models from the [Nvidia](https://catalog.ngc.nvidia.com/) and [ONNX](https://github.com/onnx/models) Model Zoo.
- A live RTSP stream.
- A container registry account.


## Step 1. Confirm your Edge modules are running

Use Visual Studio (VS) Code to confirm the modules you deployed in the [Prerequisite checklist for Azure DeepStream Accelerator ](./quickstart-readme.md) are running.are running. You can do this by checking the module status in the Azure IoT Hub section of the left navigation in VS Code.

![check_modules_running](./media/check_modules_running.png)

## Step 2. Identify your RTSP source

You can identify RTSP streams by their IP address, like ```rtsp://xxx.xx.x.xxx```.

- Before proceeding, ensure you have the endpoint location information available for use in later steps.
- If your stream requires authentication, make sure you have the appropriate credentials.


## Step 3. Prepare and upload your container

In this step, there are two ways to package and deploy an AI model configuration using the Azure DeepStream Accelerator pre-built model path. There are reasons to choose one of the two options which we outline below:

1. **Package the model(s)** and supporting files into a zip file, upload it to a web server, then download it to the running solution. This is the method used in the [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md).

    Packing the model is a quick and convenient way to deploy the AI skills to the device. Note that when you download the .zip file to your running solution, you must host it at an unsecured endpoint. This allows anybody with the URL to download the zip file, causing a security risk. This may be fine for development or for early testing but not for production.

    If you want to use this option, make sure that you have a .zip file (see the [zip file structure specification](./how-to-configcontroller.md#zip-file-structure).

2. **Rebuild the AI-Pipeline container** with the model(s) and associated files inside it, then push the container to a container registry, and redeploy using this container instead of the one you used in the [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md).

    Rebuilding the AI-Pipeline container is a secure way of packaging and deploying the AI skills to the device as this does not require one to host the ai model files to a website.

    To use the model update mechanism to build and upload the AI-Pipeline container you have running on your device, it must be capable of handling the model you specify. For example, if you followed the approach used in the [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md), your AI-Pipeline container won’t have the Triton Server enabled. This means that if you want to bring a model that requires Triton Server (see the [Model compatibility matrix](./how-to-usecommandlinetool.md#model-compatability-matrix)), you can't use this model update mechanism until you've updated your container with one that has Triton Server enabled.

    Azure DeepStream Accelerator includes a command line interface (CLI) tool to simplify your container build and upload process. If you want to use a container, follow the steps in the [How to use the command line interface tool in Azure DeepStream Accelerator](./how-to-usecommandlinetool.md) article to build and upload your model.

## Step 4. Update the deployment manifest

In this step you’ll learn how to update the deployment manifest file. You’ll be using the same file you created in the [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md) article.

There are two option to update the deployment manifest file: you can either modify the deployment manifest template and regenerate the actual deployment manifest or modify the deployment manifest directly. If you modify the deployment manifest directly, be careful not to accidentally overwrite the file if you regenerate it later.

- To modify the template for an x86 device, download the template file, and then modify the values in the template file.
- To modify the template for an ARM device, download the appropriate file and follow the steps in the next section.

### 1. Update the model location

To update the model location, modify the following sections in the deployment manifest file:

1. To host the model in a web server or an unsecure location, update the ```Controller Module``` section in the manifest file (or template). Include the ```unsecureZipUrl``` as one of the DeepStream ```pipelineConfigs``` values.

2. If you have at least one AI model, update ```primaryModelConfigPath``` to point to your DeepStream configuration file.

    If you have more than one model, you must also update secondaryModelConfigPaths.

3. To use object tracking, update ```trackerConfigPath```. (You’ll do this later in this tutorial.)


        ```JSON
                "pipelineConfigs": [
                    {
                    "id": "PeopleDetection",
                    "unsecureZipUrl": "", <----- HERE
                    "primaryModelConfigPath": "dstest3_pgie_config.txt",
                    "secondaryModelConfigPaths": "",
                    "trackerConfigPath": "",
                    "deepstreamPassthrough": "",
                    "pipelineOptions": {
                        "dewarp": {
                        "enable": false
                        },
                        "crop": {
                        "enable": false
                        },
                        "osd": {
                        "enable": true
                        }
                    }
                    }
                ]
        ```


### 2. Update the container credentials

To rebuild the AI-Pipeline container and host it in a registry, provide the registry credentials and the container uniform resource identifier (URI) by modifying the ```.env``` file with the following values:

- **CONTAINER_REGISTRY_NAME**: Your container registry's URL (for example, ```blah.azurecr.io```)
- **CONTAINER_REGISTRY_PASSWORD**: The password for your container registry.
- **CONTAINER_REGISTRY_USERNAME**: The username for your container registry.
- **DS_AI_PIPELINE_IMAGE_URI**: The image URI for your container (for example, ```blah.azurecr.io/ai-pipeline:32faa47-arm64```)

### 3. Update the model configuration path variables

Azure DeepStream Accelerator is configured through the module twin mechanism of the Controller Module. If you want to update pipeline configurations, set up your cameras to work with your pipelines, or choose which cameras will use which pipeline configurations. You must update the module twin for the Controller Module.

To learn more about the technical details of the configuration, visit [How to configure the Controller Module](./how-to-configcontroller.md).

#### To update the model configuration path variables

1. Open the deployment manifest template file and go to the ```azdaConfiguration``` section.

2. Find the ```pipelineConfigs``` list.

   This list is a JSON array of objects, each of which provides a specific configuration for a DeepStream pipeline. Populating this array with configuration objects enables you to specify which pipeline configurations each camera should use.

3. Make the following changes:

   1. For ```id```, give your pipeline a unique and meaningful name.

   1. For ```primaryModelConfigPath```, provide the path to the DeepStream model's configuration.

   1. If you have more than one model to deploy to this pipeline (in a cascade) fill in ```secondaryModelConfigPaths```.

   1. If you want to use a tracker with your model, fill in ```trackerConfigPath```.

4. If you’re bringing your model through a zip file, visit the zip file specification for details on how to do this. Otherwise, you can provide an absolute path to the file. (This is the path you used with the add command in the CLI Tool).

5. For most pre-supported models, you don’t have to provide details about the model's parser. However, if you’re using one of the following four models:

   - bodypose2d
   - ssd_mobilenet_v1
   - tiny-yolov3
   - yolov4

You  must update the pipeline configuration with an additional piece of information. Instead of specifying a single string for a path, provide an object like this:


    ```JSON
    {
        "configFile": "path to your DeepStream configuration file",
        "parser": "bodypose2d ssd_mobilenet_v1 tiny-yolov3 or yolov4"
    }
    ```

Here is an example of how to configure the model path and the parser for one of these four models.

    ```JSON
            "pipelineConfigs": [
                                {
                                    "id": "ManufacturingDefectDetection",
                                    "unsecureZipUrl": "",
                                    "primaryModelConfigPath": {
                                        "configFile":"CUSTOM_PARSER_EXAMPLES/yolov4/yolov4_nopostprocess.txt",
                                        "parser": "yolov4"
                                    }
                                }
            ]
    ```

Additionally, we provide support for Microsoft Research's *Light Detector* model, [which can be found here](https://azsusw2.blob.core.windows.net/hopeng-lighttrack-azp/checkpoints/lightdet_tiny_v1.zip). To use this model,
use "/opt/nvidia/deepstream/deepstream-6.1/sources/deepstream_python_apps/apps/ai-pipeline/lib/liblightdet.so" as the .so file for the parser
in your model configuration.

### 4. Update the video source

In the [Prerequisite checklist for Azure DeepStream Accelerator](./quickstart-readme.md) article, you updated the video source using the RTSP simulation module to convert the .mp4 file into an RTSP stream.

In this step, we’ll replace the video stream with your own video source. If you prefer to continue using the [RTSP Simulator](../rtsp-simulator/README.md), skip this step.

1. Go to the ```sensors``` section of the manifest template.

   This section is an array of objects, where each object describes a camera or file.

   - For more information about the Controller Module's twin configuration and the multiple video sources document, visit [How to configure the Controller Module](./how-to-configcontroller.md).

   - For more information about the camera and pipeline configuration relationship, see the [technical configuration specification](./how-to-configcontroller.md).

2. If you'd prefer, you can continue to use the predefined sensor and add a new one, or you can replace it. Whichever option you  choose, make sure that there is a sensor with the following values:

    ```JSON
              {
                "name": "stream-02", <--- Name this camera or video file whatever you want
                "kind": {
                  "type": "vision",
                  "subtype": "RTSP" <---- Specify "RTSP" or "File" or whatever you want it's just for logging
                },
                "endpoint": "rtsp://rtspsim:554/media/retailshop-15fps.mkv", <--- Replace with your URI
                "regionsOfInterest": [      <-- We'll cover regions of interest later
                  {
                      "color": "#ff0000",
                      "label": "ROI # 1",
                      "coordinates": [
                          [
                              0.2,
                              0.2
                          ],
                          [
                              0.55,
                              0.2
                          ],
                          [
                              0.55,
                              0.55
                          ],
                          [
                              0.2,
                              0.55
                          ]
                      ]
                  }
                ]
              }
    ```

3. In this step, you’ll specify that the camera that you defined can access the AI pipeline that you defined earlier in this tutorial.

   1. If the RTSP stream is password protected, include these credentials in the ```streams``` section of DeepStream ```pipelineConfigs```.

   1. Locate the ```streams``` section of the JSON.

      The ```streams``` section is an array filled with objects that pair your camera with the pipeline you want to use on that camera stream.


    ```JSON
                    {
                    "name": "stream-02", <--- Or whatever you named your camera above
                    "uname": "testuser", <--- If your camera needs a username, fill this appropriately
                    "password": "testpassword", <---- If your camera needs a password, fill this appropriately
                    "configId": "PeopleDetection" <---- Select the configuration ID that you specified above
                    }
    ```

## Step 5. Deploy your updates to your Edge device

In this step, you’ll regenerate the deployment manifest and reset the deployment to the updated manifest.

1. To regenerate the deployment manifest, right-click the template in VS Code and select **Generate IoT Edge Deployment Manifest**.

2. To reset the deployment to the updated manifest, right-click the deployment manifest (not the template) in VS Code and select **Create deployment for single device**.

Another option to configure your system when you don't need to redeploy a container is to use Controller's module twin directly:

- For more information about module twins, visit [Understand and use module twins in IoT Hub](https://docs.microsoft.com/azure/iot-hub/iot-hub-devguide-module-twins).

- For more information about deploying Edge modules, visit [Deploy Azure IoT Edge modules from Visual Studio Code](https://docs.microsoft.com/azure/iot-edge/how-to-deploy-modules-vscode?view=iotedge-2020-11).

### To update your Edge device

- Open the deployment JSON in VS Code and right-click the window. Then select **Update Module Twin**.

  ![update-module-twin](./media/update-module-twin.png)

### Step 6. Modify the regions of interest

In this step you’ll learn how to use the Player web app to modify the ROIs.
The Player web app allows you to play back recorded videos and define regions of interest (ROIs) for the different video streams that are deployed as part of this solution. It shares the ROI locations with the Business Logic module, enabling the module to  determine if detected objects appear within the ROIs. The Player video player doesn’t allow you to view live-stream videos directly from an Edge device.

### To modify the ROIs

1. Install and configure the Player web app. For more information, visit [How to use the Player web app](./how-to-usewebappwidget.md).

2. Launch the Player and navigate to the video you want to view.

3. View your video stream in the web app.

4. Modify the ROIs as required.

5. Save the updated ROIs.

   When you save the new ROIs, the Business Logic model is automatically updated.

## Step 7. Use the Player web app to verify your results

In this step you’ll learn how to use the Player web app to view simulated videos and model inferences and verify your results.

1.	Launch the Player and navigate to the video you want to view.

2.	View your video stream in the web app.

Congratulations! You have successfully created an Edge AI solution using Azure DeepStream Accelerator using the pre-built model path.

## Create a real-world Edge AI solution

For an example where you can use what you’ve learned to create a real-world Edge AI solution with the Body Pose 2D TAO model from the NVIDIA Model Zoo,  visit [Tutorial: Bring your own model (BYOM) to Azure DeepStream Accelerator](./tutorial-byom-path.md).


## Clean up resources

If you’re not going to continue to use your Azure resources, you may choose to delete them. To learn more about deleting Azure resources, visit [Azure Resource Manager resource group and resource deletion](https://docs.microsoft.com/azure/azure-resource-manager/management/delete-resource-group?tabs=azure-portal).

> [!NOTE]
> When you delete a resource group:<br>- All the resources in that group are deleted.<br>- It’s irreversible.<br><br>If you want to save some of the resources, delete the unwanted resources individually.

## Next steps

Now that you have completed the Azure DeepStream Accelerator Pre-built Model Path tutorial, we recommend the following tutorial:

- [Tutorial: Azure DeepStream Accelerator - Bring your own model path (BYOM) model path](./tutorial-byom-path.md)

To learn how to enhance your Edge AI solution, we recommend the following articles:

- [How to add multiple video streams to your Azure DeepStream Accelerator solution](./how-to-addmultiplevideos.md)
- [How to configure the Controller Module](./how-to-configcontroller.md)
- [How to dewarp video streams for your Azure DeepStream Accelerator solution](./how-to-dewarpvideo.md)
- [How to update the business logic in Azure DeepStream Accelerator](./how-to-modifybusinesslogic.md)
- [How to use the Player web app](./how-to-usewebappwidget.md)
- [How to migrate from a DeepStream only computer vision solution to Azure DeepStream Accelerator](./how-to-migratefromdeepstream.md)

If you encounter issues when you are creating an Edge AI solution using Azure DeepStream Accelerator, visit:

- [Troubleshoot: Azure DeepStream Accelerator - Known issues](./documentation/troubleshooting.md)
