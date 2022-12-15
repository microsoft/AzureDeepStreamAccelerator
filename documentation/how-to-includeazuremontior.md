# How to include Azure Monitor to improve observability

## Table of Contents

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Set up Azure Monitor](#set-up-azure-monitor)
- [Set up Log Analytics](#set-up-azure-log-analytics)
- [Configure Log Analytics](#configure-azure-log-analytics)
- [Visualize your Data](#visualize-your-data)
- [Example](#example)

## Introduction

Azure Monitor can help improve the availability and performance of your solution.
This service and associated tools can provide you with near real-time visibility into your edge modules.
In particular, Log Analytics can help you keep track of resource and application performance.
These services can be integrated with a variety of data visualization tools.

## Prerequisites

Make sure you have completed all the prerequisites in the [Quickstart article](./quickstart-readme.md)

## Set up Azure Monitor

Follow these steps to setup [Azure Monitor](https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/monitor-azure-resource)

You will need to include the `APPLICATIONSINSIGHTS_CONNECTIONSTRING` in your deployment manifest file.


        "ai-pipeline": {
                    "version": "1.0",
                    "startupOrder": 1,
                    "env": {
                    "APPLICATIONINSIGHTS_CONNECTION_STRING": {
                        "value": "${APPLICATIONINSIGHTS_CONNECTION_STRING}"
                    }

Update your edge device with this information before proceeding.

## Set up Azure Log Analytics

Follow these steps to setup your [Azure Log Analytics workspace](https://docs.microsoft.com/en-us/azure/azure-monitor/essentials/tutorial-resource-logs)

## Configure Azure Log Analytics

This article provides useful information about how to [query your logs](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-tutorial) using Azure Log Analytics.

## Visualize your data

Review this article to learn how to [create dashboards](https://docs.microsoft.com/en-us/azure/azure-monitor/visualize/tutorial-logs-dashboards) that visualize your Azure Log Analytics data.

## Example

Follow along with this example to get started with Azure Log Analytics.

1. [Follow these steps](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/quick-create-workspace?tabs=azure-portal)
to create a new Log Analytics workspace.
1. [Follow these steps](https://docs.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource) to create
an Application Insights resource.
    - Make sure to choose your newly created Log Analytics workspace when creating the resource.
    - Copy your connection string.
1. Update your .env file with the connection string:

    ```txt
    APPLICATIONINSIGHTS_CONNECTION_STRING="YOUR STRING HERE"
    ```

1. Regenerate your deployment manifest from the template (in VS Code, right click on the template and select "Generate IoT Edge Deployment Manifest").
1. Deploy (in VS Code, right click on the deployment manifest and select "Create Deployment for Single Device").

## Next steps
Return to your experience path to see how Azure Monitor and Log Analytics provide you with useful information about your solution.