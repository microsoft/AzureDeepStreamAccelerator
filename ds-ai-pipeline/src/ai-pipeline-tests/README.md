# Test Cases

This folder has a list of test cases for the AI-Pipeline container.

## Directions

In general, each test case is comprised of a JSON file which must be filled in with appropriate values (anywhere a string "REPLACE-" exists).
Then the JSON should be used as the module twin for the Controller module in a test deployment of the DeepStream experience.

Any test labeled ***-failure- should fail with helpful error messages logged to the container logging system.
Any test not labeld with ***-failure- should pass without error messages.

## List

* 000-basic.json: Sanity check that anything works at all.
* 001-basic-multi-stream.json: Check that we can use the same AI pipeline configuration on two different streams.
* 002-basic-multi-stream-usb.json: Check that we can use the same AI pipeline configuration on four different streams, one is a file, one is USB, and two are direct RTSP. They all come in as RTSP, but come through the USB converter or the RTSP simulator.
* 003-basic-cascade.json: Test that a model cascade runs without error.
* 004-basic-tracker.json: Test that a DeepStream tracker works as part of the pipeline.
* 005-model-update.json: Test that over the air model updating works (unsecure) in combination with a model packaged up in the container.
* 006-osd.json: Test that the On Screen Display plugin can be successfully added to a basic pipeline.
* 007-custom-parser-cascade.json: JSON that can be used with the manufacturing end-to-end use case.
* 008-crop.json: Test to see if cropping works.
* 009-dewarp.json: Test to see if dewarping works.
* 010-crop-and-dewarp.json: Test to make sure both cropping and dewarping work together. Dewarping should happen, then the dewarped image should be cropped.
* 011-ds-passthrough-basic.json: The simplest DS pipeline passthrough test case. Make sure that a well-formed basic DS pipeline in parse-launch syntax can be passed through and run without errors.
* 012-ds-passthrough-advanced.json: A more advanced version of the above test case.
* 013-multi-camera-multi-model.json: Test a whole bunch of configurations being used on a whole bunch of different streams, including several streams using the same configuration.
* 014-disable.json: Test that we can disable the whole pipeline from the configuration.
* 015-failure-case-model-not-found-001.json: Test what happens when the primary model configuration file cannot be found. A useful error message should be output and the failure should be graceful (the container should not crash).
* 016-failure-case-model-not-found-002.json: Test what happens when a secondary model configuration file cannot be found, while the primary model configuration is correct. A useful error message should be output and the failure should be graceful.
* 017-failure-case-invalid-configuration.json: Test what happens when a camera stream attempts to use a configuration that does not exist. A useful error message should be output and the failure should be graceful. In this case, the stream that is correctly configured should operate as expected; only the incorrectly configured one should fail.
* 018-failure-case-camera-not-found.json: Test what happens when a camera cannot be found at a specified end point. A useful error message should be output and the failure should be graceful. In this case, the stream that successfully connects to a camera should work as expected; only the one that relies on a camera that could not connect should fail.
* 019-failure-case-invalid-camera-config.json: Test what happens when a stream object in the JSON is not configured to point to a valid camera configuration. A useful error message should be output and the failure shoudl be graceful. In this case, only the invalid stream should fail; the other stream should work as expected.