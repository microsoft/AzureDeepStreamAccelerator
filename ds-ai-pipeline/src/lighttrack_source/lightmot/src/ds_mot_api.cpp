#include <nvds_version.h>
#include "mot_context.h"

NvMOTStatus NvMOT_Query(uint16_t customConfigFilePathSize,
                        char *pCustomConfigFilePath, NvMOTQuery *pQuery) {
  UNUSED(customConfigFilePathSize);
  UNUSED(pCustomConfigFilePath);

  // set basic config
  pQuery->computeConfig = NVMOTCOMP_CPU;
  pQuery->numTransforms = 0;
  pQuery->colorFormats[0] = NVBUF_COLOR_FORMAT_NV12;

#ifdef __aarch64__
  pQuery->memType = NVBUF_MEM_DEFAULT;
#else
  pQuery->memType = NVBUF_MEM_CUDA_DEVICE;
#endif

#if NVDS_VERSION_MAJOR >= 6
  pQuery->batchMode = NvMOTBatchMode_NonBatch;
#else
  pQuery->supportBatchProcessing = false;
#endif

  return NvMOTStatus_OK;
}

NvMOTStatus NvMOT_Init(NvMOTConfig *pConfigIn,
                       NvMOTContextHandle *pContextHandle,
                       NvMOTConfigResponse *pConfigResponse) {
  if (!pContextHandle) {
    NvMOT_DeInit(*pContextHandle);
  }

  *pContextHandle = new NvMOTContext(*pConfigIn, *pConfigResponse);

  return NvMOTStatus_OK;
}

void NvMOT_DeInit(NvMOTContextHandle contextHandle) { delete contextHandle; }

NvMOTStatus NvMOT_Process(NvMOTContextHandle contextHandle,
                          NvMOTProcessParams *pParams,
                          NvMOTTrackedObjBatch *pTrackedObjectsBatch) {
  contextHandle->processFrame(pParams, pTrackedObjectsBatch);
  return NvMOTStatus_OK;
}

NvMOTStatus NvMOT_ProcessPast(NvMOTContextHandle contextHandle,
                              NvMOTProcessParams *pParams,
                              NvDsPastFrameObjBatch *pPastFrameObjBatch) {
  contextHandle->processFramePast(pParams, pPastFrameObjBatch);
  return NvMOTStatus_OK;
}

#if NVDS_VERSION_MAJOR >= 6
#define NvMOT_RemoveStreams_RETURN_TYPE NvMOTStatus
#else
#define NvMOT_RemoveStreams_RETURN_TYPE void
#endif
NvMOT_RemoveStreams_RETURN_TYPE NvMOT_RemoveStreams(
    NvMOTContextHandle contextHandle, NvMOTStreamId streamIdMask) {
  UNUSED(contextHandle, streamIdMask);
#if NVDS_VERSION_MAJOR >= 6
  return NvMOTStatus_OK;
#endif
}
