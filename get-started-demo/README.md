
# End-to-end Manufacturing Use Case with DeepStream and TAO Toolkit

This example will illustrate how to build your own custom model using Nvidia's TAO toolkit and to integrate the model with DeepStream. The exapmle uses a MaskRCNN model provided in the TAO toolkit for performing transfer learning.

![Use Case Example](docs/images/defect-detection.gif)

This example has been adapted from the Mask RCNN documentation provided by Nvidia. Please refer to the below documentation if attempting to train a custom model using your own data. 

[TAO Toolkit MaskRCNN Documentation](https://docs.nvidia.com/tao/tao-toolkit/text/instance_segmentation/mask_rcnn.html)


# Solution Flow
1. Capture images of desired defects to track (we have already done this for you. The labeled images will be downloaded in the Jupyter notebook)
2. Upload and label images using Azure Machine Learning labeling service. For more information on this process, please reference the below documentation. For simplicity, we have labeled the dataset for this example in advance (you can find details on the process we followed [here](docs/azureml-labeling.md)). 
    - [Creating Image Labeling Projects](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-create-image-labeling-projects)
    - [Labeling Images For Your Project](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-label-data)
    - [Exporting Labeled Datasets](https://docs.microsoft.com/en-us/azure/machine-learning/how-to-create-image-labeling-projects#export-the-labels)
3. Export labels from the Azure ML labeling service
4. Run the `Manufacturing Use Case Hands On Lab.ipynb` Jupyter notebook experience. 


# Prerequisites

In order to run this example you will need to have the dependencies installed for both the TAO Toolkit as well as the DeepStream SDK. Links to the getting started guides with details on these prerequisites are provided below.
- [NVIDIA TAO toolkit](https://docs.nvidia.com/tao/tao-toolkit/text/tao_toolkit_quick_start_guide.html)
- [NVIDIA DeepStream SDK Developer Guide](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html#dgpu-setup-for-ubuntu)

> **NOTE:** Nvidia maintains the latest hardware and software requirements here for getting started. Please follow the guide until the beginning of the `Download Jupyter Notebooks and Resources` section as we will use the notebook contained in this repository. 

> **NOTE:** Be sure to create the `launcher` conda environment specified in the document


# Setting up Jupyter Notebook Server

Activate your conda environment and install the jupyter dependencies for running the lab. This can be achieved with the commands listed below.

```bash
conda activate launcher
pip3 install jupyter
```

# Start the Hands on Lab

With your conda environment activated, run the below command to start your notebook server. Open the server in your browser and navigate to the `Manufacturing Use Case Hands On Lab.ipynb` notebook.

> Note: If you are connecting to the machine used for training via SSH, you will need to configur a local port forward for your SSH session. This will allow you to navigate to `localhost:8888` to access your jupyter notebook server.

```bash
jupyter notebook --ip 0.0.0.0 --allow-root --port 8888
```