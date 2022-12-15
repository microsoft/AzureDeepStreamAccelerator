#pragma once

#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "data_type.h"
#include "tracklet.h"

class Tracker {
 public:
  Tracker();
  ~Tracker();

  std::vector<pTracklet> Update(const std::vector<NvObject> &nvObjects);
  bool Empty();

 private:
  int frame_id;
  std::vector<pTracklet> _tracked_tracklets, _lost_tracklets,
      _removed_tracklets;
};
