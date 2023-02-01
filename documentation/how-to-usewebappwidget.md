# How to use the Azure DeepStream Accelerator Player web app

The Player Widget is a web app that allows you to play back recorded videos and define regions of interest (ROIs) for the differnet video streams deployed as part of this solution.
It communicates the ROI locations to the Business Logic module, so that the module can determine if detected objects appear within an ROI.

Note: This web app does not allow for viewing "live-stream" videos from the edge device.

## Prerequisites

If you intend to modify the webapp, you will need the following prerequisites:
  - [Node.js](https://nodejs.org/en/download/)

Additionally, please make sure you have completed all the prerequisites in the [Quickstart article](./quickstart-readme.md)

## How to use the web app
1. You need to configure blob storage
    - Get a storage (not container) level SASURL under Storage account -> Security + Networking -> Shared access signature blade. Then click on container in the allowed resource type, set the expiration start and end times and then Generate SAS and Connection string.
    - Get a container level SAS token under Storage account -> Containers blade. Then Select the container and click on ... to generate the SAS token.
    - Create a CORS rule under Storage account Settings blade -> Resource sharing (CORS)

         Allowed origins = * (or white listed IPs)
         Allowed methods = * 8 (all of them)
         Allowed headers = *
         Exposed headers = *
         Max age = 99999

2. To use the web app from a browser:
    - Open the 'widget/example-app/publish' (NOTE: publish not src) folder in Windows Explorer
    - Right click on the 'index.html' file and click Open.
    - The web app will show in your default browser
    - Fill out the options for the sensor (name), data (Blob Storage SAS Url, Blob Storage Container SAS token & Blob Storage container name) and regions of interest (IoTHub Connection String, IoTHub Device Name and IoTHub Module Name for Controller Module)

3. To use the web app from Visual Studio Code:
    - Install the Live Server extension for Visual Studio Code.
    - Open the 'widget/example-app/publish/index.html' file in Visual Studio Code.
    - Click GoLive in the bottom right of Visual Studio Code toolbar.
    - The example app will launch in the default browser.
    - Fill out the options for the sensor (name), data (Blob Storage SAS Url, Blob Storage Container SAS token & Blob Storage container name) and regions of    interest (IoTHub Connection String, IoTHub Device Name and IoTHub Module Name for Controller Module)

4. To use the web app from a web site:
    - Copy the contents of the publish folder to a website.
    - Navigate to that page on the website in a browser.
    - Fill out the options for the sensor (name), data (Blob Storage SAS Url, Blob Storage Container SAS token & Blob Storage container name) and regions of    interest (IoTHub Connection String, IoTHub Device Name, IoTHub Module Name for Controller Module)

5. To build the library and web app:
    - Install Visual Studio Code.
    - Install node js LTS.
    - Open the widget folder in the terminal.
    - In terminal enter: npm install.
    - OPTIONAL: Open the 'widget/example-app/src/App.jsx' file and fill out the options for the data and Region of Interest services.
    - In terminal enter: npm run build
        - The files index.bundle.js and index.html will appear in the 'widget/example-app/publish' folder.

## How to initialize your ROIs

This web app works with pre-recorded videos, so setting up video stream ROIs first time might be challenge for a system that relies on ROIs to determine recordable events.
To simplfy this task, we have included configuration parameters in IoT module deployment manifest that allow the user to manually control video recording.
These are set to `true` in the referene template, which will cause video snippets to be saved to the cloud as soon as the AI pipeline is activated.
This will provide a sample of video files that can be used to define the initial ROIs.
Once you have defined your ROIs and updated the edge device, you can manually set them to `false`,
or allow your business logic determine if recording video is still approprate based on model detections and business rules.

Here is the section of the `azure-iot-module-twin.json` that contains these parameters.
There is one for each pipeline, or `configId`.

        "BusinessLogicModule": {
            "properties.desired": {
                "startRecording": [
                {
                    "configId": "PeopleDetection",
                    "state": true
                },
                {
                    "configId": "LicensePlateCascade",
                    "state": true
                }



## How to define or update an ROI

1. Select a video
When the web app launches, it will be in playback mode.
This is indicated by the pair of vertical lines or bars below the right side of the video.
This icon indicates where to click to switch to the ROI editor.
You'll see when you click on this icon a video camera icon appears,
to show you how to get back to the video player.

Stay in video playback mode, for now.

Use the calendar icon to navigate, based on time and date of recording, to the video you want to use to set your ROIs.
Select your video and it will start playing in the window.
You will see "play" and "pause" icons. These buttons allow you to contol the playback.
There are also "forward" and "back" arrows that allow you to move between videos.

You will also see icons in the lower left corner, a rectangle and a group of shapes(circle, square, triangle).
The rectangle allows you to toggle the detection bounding boxes on/off, on the video screen.
The group of shapes allows you to do the same for ROIs.

2. Create an ROI

Click the vertical editing bars to switch to ROI editor mode.

Use the "plus" sign to create a new ROI.
Rename the "Label" field to a name meaningful to you and change the color, if you wish.

You can draw ROIs directly on the video image using point, line, or polygon controls.


3. Save and update your ROI
When you have the ROI drawn as you like, simply click the save icon, below the list of ROIs.
Saving the ROI also sends an update to the Business Logic module.
You should see a pop-up message that reads, "Regions of Interest Updated."
Click "Okay" and continue.

You can define multiple ROIs for the same sensor or switch to a different sensor.
There is no technical limit to the number of ROIs you can define.
