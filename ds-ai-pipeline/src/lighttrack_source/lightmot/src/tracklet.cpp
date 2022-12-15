#include "tracklet.h"
#include <unordered_set>
#include "config.h"

const KalmanFilter KALMAN_FILTER;

BOX_T GetXYAH(const NvObject &obj) {
  BOX_T xyah;
  xyah[0] = obj.CX();
  xyah[1] = obj.CY();
  xyah[2] = obj.Aspect();
  xyah[3] = obj.height;
  return xyah;
}

Vec2<float> GetIoUDistance(std::vector<pTracklet> &a_tracklets,
                           std::vector<pTracklet> &b_tracklets) {
  // dists = 1.0 - iou
  const size_t a_size = a_tracklets.size();
  const size_t b_size = b_tracklets.size();
  if (a_size == 0 || b_size == 0) return {};

  std::vector<float> b_areas(b_size);
  for (int b = 0; b < b_size; ++b) {
    b_areas[b] = b_tracklets[b]->obj.Area();
  }

  // the maximum distance is 1.0
  Vec2<float> dists(a_size, std::vector<float>(b_size, 1.0));
#pragma omp parallel for num_threads(NUM_OMP_THREADS)
  for (int a = 0; a < a_size; ++a) {
    const auto &a_obj = a_tracklets[a]->obj;
    const float area_a = a_obj.Area();
    auto &v_dists = dists[a];
    for (int b = 0; b < b_size; ++b) {
      const auto &b_obj = b_tracklets[b]->obj;

      const float ih = std::min(a_obj.Bottom(), b_obj.Bottom()) -
                       std::max(a_obj.Top(), b_obj.Top()) + 1;
      if (ih > 0) {
        const float iw = std::min(a_obj.Right(), b_obj.Right()) -
                         std::max(a_obj.Left(), b_obj.Left()) + 1;
        if (iw > 0) {
          const float up = iw * ih;
          const float down = area_a + b_areas[b] - up;
          v_dists[b] = 1.0 - up / down;
        }
      }
    }
  }
  return dists;
}

Tracklet::Tracklet(const NvObject &nv_obj) {
  UpdateObj(nv_obj);
  activated = false;
  state = State::New;
}

Tracklet::~Tracklet() {}

bool Tracklet::IsActivated() const { return activated; }

void Tracklet::Activate(int frame_id) {
  track_id = GetNextTrackID();
  kal_state = KALMAN_FILTER.Init(GetXYAH(obj));
  state = State::Tracked;
  age = 0;

  // for bboxes in the first frame (frame_id == 1)
  if (frame_id == 1) {
    activated = true;
  }

  this->frame_id = frame_id;
  this->start_frame = frame_id;
}

void Tracklet::ReActivate(const Tracklet &new_track, int frame_id) {
  UpdateObj(new_track.obj);

  kal_state = KALMAN_FILTER.Update(kal_state, GetXYAH(obj));

  UpdateKFPos();

  age = 0;
  state = State::Tracked;
  activated = true;
  this->frame_id = frame_id;
}

void Tracklet::Update(const Tracklet &new_track, int frame_id) {
  this->frame_id = frame_id;
  ++age;

  UpdateObj(new_track.obj);

  // when a bbox is cropped by image edge, we reset kalman filter
  const int EDGE = 64;
  bool reset_kf =
      (obj.Left() < EDGE || obj.Top() < EDGE || obj.Right() >= INPUT_W - EDGE ||
       obj.Bottom() >= INPUT_H - EDGE);

  auto xyah = GetXYAH(obj);

  if (!reset_kf) {
    kal_state = KALMAN_FILTER.Update(kal_state, xyah);
    auto &kal_mean = kal_state.first;

    float kf_area = kal_mean[3] * (kal_mean[3] * kal_mean[2]);
    float new_area = obj.Area();
    const float area_rate =
        std::min(kf_area, new_area) / std::max(kf_area, new_area);
    if (area_rate < 0.8) {
      reset_kf = true;
    }
  }

  if (reset_kf) {
    // Reset KalmanFilter
    kal_state = KALMAN_FILTER.Init(xyah);
  }

  UpdateKFPos();
  state = State::Tracked;
  activated = true;
}

void Tracklet::UpdateKFPos() {
  // CX, CY, A, H
  const auto &kal_mean = kal_state.first;
  obj.height = kal_mean[3];
  obj.width = obj.height * kal_mean[2];
  obj.y = kal_mean[1] - obj.height / 2;
  obj.x = kal_mean[0] - obj.width / 2;
}

#include <iostream>
void Tracklet::UpdateObj(const NvObject &new_obj) {
  obj = new_obj;
  // update label
  const float score = (cls_scores[new_obj.label] += new_obj.prob);
  if (score > max_cls_score) {
    best_label = new_obj.label;
    max_cls_score = score;
  }
  obj.label = best_label;
}

int Tracklet::GetNextTrackID() {
  static int NEXT_TRACK_ID = 0;
  // start at 1
  return ++NEXT_TRACK_ID;
}

void Tracklet::Predict() {
  if (state != State::Tracked) {
    // do not change aspect
    kal_state.first[7] = 0;
  }
  kal_state = KALMAN_FILTER.Predict(kal_state);
}

void AppendTracklets(std::vector<pTracklet> &a,
                     const std::vector<pTracklet> &b) {
  std::unordered_set<int> exists;
  for (const auto &e : a) {
    exists.insert(e->track_id);
  }
  for (const auto &e : b) {
    if (exists.insert(e->track_id).second) {
      a.push_back(e);
    }
  }
}

std::vector<pTracklet> ConcatTracklets(const std::vector<pTracklet> &a,
                                       const std::vector<pTracklet> &b) {
  std::unordered_set<int> exists;
  std::vector<pTracklet> res;

  for (const auto &e : a) {
    exists.insert(e->track_id);
    res.push_back(e);
  }
  for (const auto &e : b) {
    if (exists.insert(e->track_id).second) {
      res.push_back(e);
    }
  }
  return res;
}

void EraseTracklets(std::vector<pTracklet> &a,
                    const std::vector<pTracklet> &b) {
  std::unordered_set<int> exists;
  for (const auto &e : b) {
    exists.insert(e->track_id);
  }
  a.erase(std::remove_if(a.begin(), a.end(),
                         [&](const pTracklet &t) -> bool {
                           return exists.count(t->track_id);
                         }),
          a.end());
}

void RemoveDuplicateTracklets(std::vector<pTracklet> &a,
                              std::vector<pTracklet> &b) {
  const size_t a_size = a.size(), b_size = b.size();
  std::vector<int> a_times(a_size), b_times(b_size);
  for (size_t i = 0; i < a_size; ++i)
    a_times[i] = a[i]->frame_id - a[i]->start_frame;
  for (size_t i = 0; i < b_size; ++i)
    b_times[i] = b[i]->frame_id - b[i]->start_frame;

  auto dist = GetIoUDistance(a, b);

  for (int i = 0; i < a_size; ++i) {
    for (int j = 0; j < b_size; ++j) {
      if (dist[i][j] < 0.15) {
        if (a_times[i] > b_times[j]) {
          b[j].reset();
        } else {
          a[i].reset();
        }
      }
    }
  }

  a.erase(std::remove_if(a.begin(), a.end(),
                         [](const pTracklet &t) { return t.get() == nullptr; }),
          a.end());
  b.erase(std::remove_if(b.begin(), b.end(),
                         [](const pTracklet &t) { return t.get() == nullptr; }),
          b.end());
}
