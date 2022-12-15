#pragma once

#include <nvdstracker.h>
#include <array>
#include <memory>
#include <unordered_map>
#include "defines.h"
#include "kalman_filter.h"

class Tracklet {
 public:
  Tracklet(const NvObject &nv_obj);
  bool IsActivated() const;
  void Activate(int frame_id);
  void ReActivate(const Tracklet &new_track, int frame_id);
  void Update(const Tracklet &new_track, int frame_id);
  void Predict();
  ~Tracklet();

 public:
  int track_id;
  int age;
  int frame_id, start_frame;
  bool activated;
  NvObject obj;
  enum class State { New = 0, Tracked, Lost, Removed };
  State state;
  KAL_STATE kal_state;

 private:
  void UpdateKFPos();
  void UpdateObj(const NvObject &new_obj);
  static int GetNextTrackID();

 private:
  std::unordered_map<int, float> cls_scores;
  float max_cls_score = 0;
  int best_label;
};

using pTracklet = std::shared_ptr<Tracklet>;

Vec2<float> GetIoUDistance(std::vector<pTracklet> &a_tracklets,
                           std::vector<pTracklet> &b_tracklets);

void AppendTracklets(std::vector<pTracklet> &a,
                     const std::vector<pTracklet> &b);
std::vector<pTracklet> ConcatTracklets(const std::vector<pTracklet> &a,
                                       const std::vector<pTracklet> &b);
void EraseTracklets(std::vector<pTracklet> &a, const std::vector<pTracklet> &b);
void RemoveDuplicateTracklets(std::vector<pTracklet> &a,
                              std::vector<pTracklet> &b);
