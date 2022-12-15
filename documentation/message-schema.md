# Message Schema

This document describes the technical details of the JSON messages that are sent to and from the Business Logic Container.

## AI Pipeline to BLC

```JSON
{
    "events": [
        {
            "id": "b013c2059577418caa826844223bb50b",  // Event ID - not sure what this is: SA defines it but does not explain it
            "type": "personCountEvent", // User defined event type
            "zone": "lobbycamera",      // Name of the region of interest
            "sensor": "name of the camera that has this zone defined on it",
            "userDefinedData": {
                // User defines this - it is opaque to us
            }
        }
    ],
    "regionsOfInterest": [ // Zero or more regions of interest
        {
            "label": "name for this ROI",
            "color": "3 byte hex code for RGB",
            "sensor": "camera name",
            "coordinates": [
                [x, y],
                [x, y],
                etc.
            ]
        }
    ],
    "detections": [ // Zero or more detections
        {
            "sourceInfo": {
                "id": "the name of the camera whose output generated this event",
                "timestamp": "2020-08-24T06:06:57.224Z",  // UTC
                "width": 608,  // Int: Video frame width
                "height": 342, // Int: Video frame height
                "frameId": "1400" // Int: The ID of the frame
            },
            "type": "one of { 'detection', 'classification', 'segmentation', 'custom' }",
            "id": "unique ID per detection",
            "inference":  // One of the following objects
                // IF type == 'detection':
                {
                    // DeepStream NvDsObjectMeta, serialized into JSON
                    "classId": 8, // Int: index of the object class
                    "confidence": 0.92, // Float
                    "label": "string version of class-id (e.g., 'boat')",
                    "rect": [10, 15, 100, 200] // Bounding box shape int : (left, top, width, height) - object.left = outputX1;  object.top = outputY1;  object.width = outputX2 - outputX1; object.height = outputY2 - outputY1;
                },

                // IF type == 'classification':
                {
                    // DeepStream NvDsClassifierMeta, serialized into JSON
                    "classId": 8, // Int: Index of the object class
                    "confidence": 0.92, // Float
                    "label": "string version of class-id (e.g., 'boat')"
                },

                // IF type == 'segmentation':
                {
                    // DeepStream NvDsInferSegmentationMeta, serialized into JSON
                    "nClasses": 8, // Int: Number of classes detected
                    "height": 416, // Int: Height of the segmentation output class map
                    "width": 416,  // Int: Width of the segmentation output class map
                    "classMap": [0, 0, 0, 0, 2, 0, 2, 2, 2, 7, etc.], // Array of width * height class IDs. Output for pixel (x, y) will be at index (y * width + x). -> Need to compress somehow
                    "labels": ["boat", "dinosaur", "cookies", etc.] // Label for each of the N classes
                },

                // IF type == 'custom':
                {
                    // Arbitrary JSON object provided by user's custom parser
                    // (DeepStream NvDsInferTensorMeta -> NvDsUserMeta)
                }
        }
    ]
}
```

## BLC to AI Pipeline

```JSON
{
    "events": [
        {
            "id": "b013c2059577418caa826844223bb50b",
            "type": "personCountEvent",
            "zone": "lobbycamera",
            "userDefinedData": {
                // User defines this - it is opaque to us
            },
            "frameId": "1400", // Int: The ID of the frame.
            "camera": "the name of the camera whose output generated this event",
            "timestamp": "2020-08-24T06:06:57.224Z" // UTC
        }
    ]
}
```
