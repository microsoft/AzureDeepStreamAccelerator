#include <fstream>
#include <iostream>
#include <unordered_set>

#include "config.h"
#include "mot_context.h"
#include "tracker.h"
using namespace std;

NvMOTContext::NvMOTContext(const NvMOTConfig &configIn,
                           NvMOTConfigResponse &configResponse) {
  UNUSED(configIn, configResponse);
  configResponse.summaryStatus = NvMOTConfigStatus_OK;
}

NvMOTStatus NvMOTContext::processFrame(
    const NvMOTProcessParams *params,
    NvMOTTrackedObjBatch *pTrackedObjectsBatch) {
  if (!params || params->numFrames <= 0) return NvMOTStatus_OK;

  NvMOTTrackedObjList *trackedObjList = &pTrackedObjectsBatch->list[0];
  NvMOTFrame *frame = &params->frameList[0];

  std::vector<NvObject> nvObjects(frame->objectsIn.numFilled);
  std::unordered_set<NvMOTObjToTrack *> current_objs;

  for (size_t i = 0; i < frame->objectsIn.numFilled; ++i) {
    NvMOTObjToTrack *objectToTrack = &frame->objectsIn.list[i];

    NvObject &obj = nvObjects[i];
    obj.x = objectToTrack->bbox.x;
    obj.y = objectToTrack->bbox.y;
    obj.width = objectToTrack->bbox.width;
    obj.height = objectToTrack->bbox.height;
    obj.label = objectToTrack->classId;
    obj.prob = objectToTrack->confidence;
    obj.objectToTrack = objectToTrack;

    current_objs.insert(objectToTrack);
  }

  std::vector<pTracklet> outputs = tracker.Update(nvObjects);
  const size_t num_tracklets = outputs.size();
  NvMOTTrackedObj *p_tracked_objs = new NvMOTTrackedObj[num_tracklets];
  size_t fid = 0;
  for (size_t i = 0; i < num_tracklets; ++i) {
    Tracklet &tracklet = *outputs[i];
    NvObject &obj = tracklet.obj;
    array<float, 4> ltwh{obj.x, obj.y, obj.width, obj.height};
    if (USING_DET_BBOX) {
      auto p = obj.objectToTrack;
      if (p && current_objs.count(p))
        ltwh = array<float, 4>{p->bbox.x, p->bbox.y, p->bbox.width,
                               p->bbox.height};
    }
    // remove outer bbox
    if (ltwh[0] >= INPUT_W - 1 || ltwh[1] >= INPUT_H - 1 ||
        ltwh[0] + ltwh[2] <= 0 || ltwh[1] + ltwh[3] <= 0)
      continue;
    if (ltwh[2] >= INPUT_W || ltwh[3] >= INPUT_H) continue;
    NvMOTTrackedObj &trackedObj = p_tracked_objs[fid++];
    NvMOTRect motRect{ltwh[0], ltwh[1], ltwh[2], ltwh[3]};
    trackedObj.classId = obj.label;
    // hack object_id(64 bits) to store the class id
    // if the highest bit is 1:
    //   cls_and_obj_id = (1 << 63) | ((cls_id) << 32) | obj_id
    trackedObj.trackingId = ((uint64_t)1 << 63) |
                            (((uint64_t)obj.label) << 32) |
                            (uint64_t)tracklet.track_id;
    trackedObj.bbox = motRect;
    trackedObj.confidence = 1;
    trackedObj.age = (uint32_t)tracklet.age;
    if (current_objs.count(obj.objectToTrack) > 0) {
      trackedObj.associatedObjectIn = obj.objectToTrack;
      obj.objectToTrack->confidence = 1;
      trackedObj.associatedObjectIn->doTracking = true;
      // note that trackedObj.classId must be equal to objectToTrack->classId
      // otherwise, the bbox is not visible.
      trackedObj.classId = obj.objectToTrack->classId;
    } else {
      trackedObj.associatedObjectIn = nullptr;
    }
  }

  trackedObjList->streamID = frame->streamID;
  trackedObjList->frameNum = frame->frameNum;
  trackedObjList->valid = true;

  trackedObjList->list = p_tracked_objs;
  trackedObjList->numFilled = fid;
  trackedObjList->numAllocated = num_tracklets;

  return NvMOTStatus_OK;
}

NvMOTStatus NvMOTContext::processFramePast(
    const NvMOTProcessParams *params,
    NvDsPastFrameObjBatch *pPastFrameObjectsBatch) {
  UNUSED(params, pPastFrameObjectsBatch);
  return NvMOTStatus_OK;
}

NvMOTStatus NvMOTContext::removeStream(const NvMOTStreamId streamIdMask) {
  UNUSED(streamIdMask);
  return NvMOTStatus_OK;
}
