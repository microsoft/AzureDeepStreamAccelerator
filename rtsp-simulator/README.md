# RTSP Simulator

RTSP Simulator is an IoT Edge module that can be incorporated into your deployment to provide a convenient means of testing.

This is the source code for RTSP Simulator, in case you want to modify it, but we release a default image from HERE(TODO),
which should serve most users' purposes.

## Using it

To use RTSP Simulator in your deployment, just incorporate it into the deployment manifest (it's already in the default one)
and then use any of its pre-packaged videos as a test in place of an actual camera by specifying:

```JSON
    "endpoint": "rtsp://rtspsim:554/media/<VIDEO-FILE-NAME-INCLUDING-SUFFIX>"
```

in the deployment manifest.