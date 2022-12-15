#include <omp.h>
#include <cassert>
#include <utility>

#include "config.h"
#include "lapjv.h"
#include "tracker.h"

Tracker::Tracker() : frame_id(0) {}

Tracker::~Tracker() {}

std::vector<pTracklet> Tracker::Update(const std::vector<NvObject> &objects) {
  ++frame_id;

  // detection bboxes with high score/low score
  std::vector<pTracklet> det_high, det_low;
  for (const NvObject &obj : objects) {
    pTracklet tracklet(new Tracklet(obj));
    if (obj.prob >= TRACK_THRESH)
      det_high.emplace_back(tracklet);
    else
      det_low.emplace_back(tracklet);
  }

  // traversed the tracked tracklet
  std::vector<pTracklet> unconfirmed_list, tracked_list;
  for (auto &t : this->_tracked_tracklets) {
    if (t->IsActivated()) {
      tracked_list.push_back(t);
    } else {
      unconfirmed_list.push_back(t);
    }
  }

  std::vector<pTracklet> pool =
      ConcatTracklets(tracked_list, this->_lost_tracklets);

  for (auto &t : pool) {
    t->Predict();
  }

  // Match bboxes with high score
  // unmatched tracklets and detection bboxes
  std::vector<int> u_track_ids, u_det_ids;
  std::vector<pTracklet> act_list;
  {
    auto dists = GetIoUDistance(pool, det_high);
    auto matches = LinearAssignment(dists, pool.size(), det_high.size(),
                                    MATCH_THRESH, u_track_ids, u_det_ids);
    for (auto &p : matches) {
      auto &tracklet = pool[p.first];
      auto &det = det_high[p.second];
      if (tracklet->state == Tracklet::State::Tracked) {
        tracklet->Update(*det, frame_id);
      } else {
        tracklet->ReActivate(*det, frame_id);
      }
      act_list.push_back(tracklet);
    }
  }

  // match unmatched tracklets and bboxes
  std::vector<pTracklet> u_det(u_det_ids.size());
  for (size_t i = 0; i < u_det_ids.size(); ++i) {
    u_det[i] = det_high[u_det_ids[i]];
  }

  std::vector<pTracklet> u_track;
  for (int i : u_track_ids) {
    if (pool[i]->state == Tracklet::State::Tracked) {
      u_track.push_back(pool[i]);
    }
  }

  auto dists = GetIoUDistance(u_track, det_low);

  std::vector<int> u_track_ids2, u_det_ids2;
  auto matches = LinearAssignment(dists, u_track.size(), det_low.size(),
                                  MATCH_THRESH_LOW, u_track_ids2, u_det_ids2);

  for (auto &p : matches) {
    auto &tracklet = u_track[p.first];
    auto &det = det_low[p.second];
    if (tracklet->state == Tracklet::State::Tracked) {
      tracklet->Update(*det, frame_id);
    } else {
      tracklet->ReActivate(*det, frame_id);
    }
    act_list.push_back(tracklet);
  }

  std::vector<pTracklet> lost_list;
  for (int i : u_track_ids2) {
    pTracklet &p = u_track[i];
    if (p->state != Tracklet::State::Lost) {
      p->state = Tracklet::State::Lost;
      lost_list.push_back(p);
    }
  }

  // deal with unconfirmed tracklets whose locates in its beginning frame
  dists = GetIoUDistance(unconfirmed_list, u_det);
  std::vector<int> u_track_ids3, u_det_ids3;
  matches =
      LinearAssignment(dists, unconfirmed_list.size(), u_det.size(),
                       MATCH_THRESH_UNCONFIRMED, u_track_ids3, u_det_ids3);
  for (auto &p : matches) {
    auto &tracklet = unconfirmed_list[p.first];
    auto &det = u_det[p.second];
    tracklet->Update(*det, frame_id);
    act_list.push_back(tracklet);
  }

  // mark remove for rest unconfirmed tracklet
  std::vector<pTracklet> removed_list;
  for (int i : u_track_ids3) {
    auto &tracklet = unconfirmed_list[i];
    tracklet->state = Tracklet::State::Removed;
    removed_list.push_back(tracklet);
  }

  // for new tracklets
  for (int i : u_det_ids3) {
    auto &tracklet = u_det[i];
    if (tracklet->obj.prob >= HIGH_THRESH) {
      tracklet->Activate(frame_id);
      act_list.push_back(tracklet);
    }
  }

  // mark remove for the timeout tracklets
  for (auto &t : this->_lost_tracklets) {
    if (frame_id - t->frame_id > MAX_TIME_LOST) {
      t->state = Tracklet::State::Removed;
      removed_list.push_back(t);
    }
  }

  // remove the tracklets whose state is not Tracked.
  this->_tracked_tracklets.erase(
      std::remove_if(this->_tracked_tracklets.begin(),
                     this->_tracked_tracklets.end(),
                     [](const pTracklet &t) {
                       return t->state != Tracklet::State::Tracked;
                     }),
      this->_tracked_tracklets.end());

  AppendTracklets(this->_tracked_tracklets, act_list);
  EraseTracklets(this->_lost_tracklets, this->_tracked_tracklets);
  AppendTracklets(this->_lost_tracklets, lost_list);
  EraseTracklets(this->_lost_tracklets, this->_removed_tracklets);
  this->_removed_tracklets = removed_list;
  RemoveDuplicateTracklets(this->_tracked_tracklets, this->_lost_tracklets);

  // outputs
  std::vector<pTracklet> outputs;
  for (auto &t : this->_tracked_tracklets) {
    if (t->IsActivated()) outputs.push_back(t);
  }

  return outputs;
}

bool Tracker::Empty() { return this->_tracked_tracklets.empty(); }
