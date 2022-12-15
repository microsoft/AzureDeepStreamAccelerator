#pragma once

#include <nvdstracker.h>
#include "tracker.h"

class NvMOTContext {
 public:
  NvMOTContext(const NvMOTConfig &configIn,
               NvMOTConfigResponse &configResponse);

  ~NvMOTContext(){};

  NvMOTStatus processFrame(const NvMOTProcessParams *params,
                           NvMOTTrackedObjBatch *pTrackedObjectsBatch);

  NvMOTStatus processFramePast(const NvMOTProcessParams *params,
                               NvDsPastFrameObjBatch *pPastFrameObjectsBatch);

  NvMOTStatus removeStream(const NvMOTStreamId streamIdMask);

 private:
  Tracker tracker;
};
