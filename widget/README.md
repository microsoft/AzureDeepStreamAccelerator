To use the widget, you need to config blob storage:

    1. get a storage (not container) level sasurl
    2. get a container level sas token
    3. create a CORS rule:

    Allowed origins = * (or white listed IPs)
    Allowed methods = * 8 (all of them)
    Allowed headers = *
    Exposed headers = *
    Max age = 99999

To use the example app from a browser:

    1. Open the 'widget/example-app/publish' (NOTE: publish not src) folder in Windows Explorer
    2. Right click on the 'index.html' file and click Open.
    3. Fill out the options for the sensor, data and regions of interest.

    The example app will show in your default browser.

To use the example app from Visual Studio Code:

    1. Install the Live Server extension for Visual Studio Code.
    2. Open the 'widget/example-app/publish/index.html' file in Visual Studio Code.
    3. Click GoLive in the bottom right of Visual Studio Code toolbar.

    The example app will launch in the default browser.

    4. Fill out the options for the sensor, data and regions of interest.

To use the example app from a web site:

    1. Copy the contents of the publish folder to a website.
    2. Navigate to that page on the website in a browser.
    3. Fill out the options for the Sensor, Data and Regions of Interest and then click the 'Continue' button.

To build the library and example app:

    1. Install Visual Studio Code.
    2. Install node js LTS.
    3. Open the widget folder in the terminal.
    4. In terminal enter: npm install.
    5. OPTIONAL: Open the 'widget/example-app/src/App.tsx' file and fill out the options for the Data and Region of Interest services.
    6. In terminal enter: npm run build

    The files index.bundle.js and index.html will appear in the 'widget/example-app/publish' folder.

To use the Region of Interest Editor:

    1. Select Point, Line or Shape in the player toolbar (or press 1, 2 or 3) to choose whether to edit by Point, Line or Shape.

    2. Mouse over a Point/Line/Shape to select for editing and the selected Point/Line/Shape will be highlighted in yellow.

    3. To edit by Point:
        a. Click to add a new Point.
        b. Click, hold and drag to move a selected Point.
        c. Press the delete key to delete a selected Point.
        d. Press the insert key to insert a Point after a selected Point.

    4. To edit by Line:
        a. Click, hold and drag to move a selected Line.

    5. To edit by Shape:
        a. Click, hold and drag to move a selected Shape.
