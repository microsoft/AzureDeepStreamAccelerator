# How to migrate from a DeepStream only computer vision solution to DeepStream with Azure DeepStream Accelerator
This article will guide you in migrating an existing DeepStream solution.

## Prerequisites
Review these articles to familiarize yourself with the solution:
- [Overview](../README.md)
- [Quickstart](./quickstart-readme.md)
- [Bring your own model path](./tutorial-byom-path.md)

You will also need an existing DeepStream solution.

## Export existing gstreamer pipeline configurations (optional)

If you are using Graph composer, you can use the provided tools to [export the configuration](https://docs.nvidia.com/metropolis/deepstream/dev-guide/graphtools-docs/docs/text/GraphComposer_Composer.html#open-and-save-application-graphs).

This information will be a valuable reference while you consider your migration choices.

## Conduct a migration assesment

Before begining your migration to Azure DeepStream Accelerator,
you should compare your current implementation to the different features and experience paths that are available in this solution.
You can refer to the main [README](../README.md) to learn more about the different paths.

Consider the following points in your assesment.

1. Edge devices.
You need a device that can run IoT Edge and which has an NVIDIA GPU.
If you are using Triton server or TensorRT, these can solutions can be migrated.

1. Computer vision model.
Check to see if your implementation uses one of our [Pre-built models](./tutorial-prebuiltmodel-path.md),
for which we have included a Python-based parser.
If you want to use one of these models, the Pre-built model path may be right for you.

1. AI pipeline features.
This solution supports a many different video processing and AI features.
You can deploy a model for primary inference and any number of secondary inferences, as well as object tracking.
Video enhancements such as image cropping, dewarping, and on-screen display of bounding boxes are all available.

    These features are available in both the Pre-built model and [Bring your own model path](./tutorial-byom-path.md).

1. Additional features and requirements
If your model is not one of our Pre-built models or you require features that are not mentioned here,
the [Bring your own model path](./tutorial-byom-path.md) may be right for you.
This solution includes a [CLI tool](./how-to-usecommandlinetool.md) that simplifies your container build process,
while also providing a high degree of flexibility on what model and pipeline features you deploy to the edge.



## Next steps
- Determine which experience path is best for your workload
- Follow the tutorial for that path
    - [Pre-built model](./tutorial-prebuiltmodel-path.md)
    - [Bring your own mode](./tutorial-byom-path.md)
