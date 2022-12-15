#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <numeric>
#include <vector>

#include "nvdsinfer.h"
#include "nvdsinfer_custom_impl.h"

static float NMS_THRESH = 0.45;
static float BBOX_CONF_THRESH = 0.1;
static float MIN_ASPECT_RATIO_THRESH = -1.0;
static float MAX_ASPECT_RATIO_THRESH = -1.0;
static int MIN_BOX_AREA = 10;

static int INPUT_W = 416;
static int INPUT_H = 416;
static int NUM_CLASSES = 80;
static int CLIP_BORDER = -1;

static const char *INPUT_BLOB_NAME = "input_0";
static const char *OUTPUT_BLOB_NAME = "output_0";

struct BBox {
  // left, top, width, height
  float x, y, width, height;
  inline float Area() const { return width * height; }
};

struct Proposal {
  BBox bbox;
  int label;
  float prob;
};

using GridStride = std::array<int, 3>;
static std::vector<GridStride> GRID_STRIDES;

void PreComputeGridStride(const std::vector<int> &strides) {
  GRID_STRIDES.clear();

  for (int s : strides) {
    const int num_grid_w = INPUT_W / s;
    const int num_grid_h = INPUT_H / s;
    for (int gy = 0; gy < num_grid_h; ++gy) {
      for (int gx = 0; gx < num_grid_w; ++gx) {
        GRID_STRIDES.emplace_back(GridStride{gx, gy, s});
      }
    }
  }
}

class __INIT_CLASS {
 public:
  __INIT_CLASS() {
    const std::vector<int> strides = {8, 16, 32};
    PreComputeGridStride(strides);
  }
};
static __INIT_CLASS __cls;

std::vector<Proposal> GenerateProposals(const float *prob,
                                        const int num_anchors) {
  std::vector<Proposal> proposals;
  int grid_x, grid_y, stride;

  for (int i = 0; i < num_anchors; ++i) {
    const GridStride &gs = GRID_STRIDES[i];
    grid_x = gs[0];
    grid_y = gs[1];
    stride = gs[2];

    // [cx, cy, w, h, objectness, box_cls_score] * NUM_CLASSES
    const int p = i * (NUM_CLASSES + 5);
    float objness = prob[p + 4];  // sigmoid score in [0, 1]
    if (objness <= BBOX_CONF_THRESH) continue;

    float cx = (prob[p + 0] + grid_x) * stride;
    float cy = (prob[p + 1] + grid_y) * stride;
    float w = exp(prob[p + 2]) * stride;
    float h = exp(prob[p + 3]) * stride;
    float left = cx - w * 0.5;
    float top = cy - h * 0.5;

    const float aspect = w / h;

    if (MIN_ASPECT_RATIO_THRESH > 0 && aspect < MIN_ASPECT_RATIO_THRESH)
      continue;
    if (MAX_ASPECT_RATIO_THRESH > 0 && aspect > MAX_ASPECT_RATIO_THRESH)
      continue;
    const float area = w * h;
    if (MIN_BOX_AREA > 0 && area < MIN_BOX_AREA) continue;

    // traverse all classes
    for (int c = 0; c < NUM_CLASSES; ++c) {
      float cls_score = prob[p + 5 + c];
      float box_prob = objness * cls_score;
      // larger than threshold
      if (box_prob > BBOX_CONF_THRESH) {
        proposals.emplace_back(Proposal{BBox{left, top, w, h}, c, box_prob});
      }
    }
  }
  return proposals;
}

void SortProposals(std::vector<Proposal> &proposals) {
  if (proposals.empty()) return;

  const int n = proposals.size();
  std::vector<decltype(Proposal::prob)> probs(n);
  // indexes: from 0 to n - 1
  std::vector<int> indexes(n);
  std::iota(indexes.begin(), indexes.end(), 0);

  for (int i = 0; i < n; ++i) {
    probs[i] = proposals[i].prob;
  }

  // sort by descent
  std::sort(indexes.begin(), indexes.end(),
            [&](int a, int b) { return probs[a] > probs[b]; });

  std::vector<Proposal> results(n);
  for (int i = 0; i < n; ++i) {
    results[i] = proposals[indexes[i]];
  }

  proposals = std::move(results);
}

std::vector<int> GetNMSKeepIDs(const std::vector<Proposal> &proposals) {
  const int n = proposals.size();
  std::vector<float> areas(n);
  for (int i = 0; i < n; ++i) {
    areas[i] = proposals[i].bbox.Area();
  }
  std::vector<int> keep_ids;
  for (int i = 0; i < n; ++i) {
    const BBox &a = proposals[i].bbox;

    bool keep = true;
    for (int j : keep_ids) {
      const BBox &b = proposals[j].bbox;

      // intersection
      float x0 = std::max(a.x, b.x), y0 = std::max(a.y, b.y);
      float x1 = std::min(a.x + a.width, b.x + b.width);
      float y1 = std::min(a.y + a.height, b.y + b.height);
      float iw = x1 - x0;
      float ih = y1 - y0;
      if (iw <= 0 || ih <= 0) {
        continue;
      }

      float inter_area = iw * ih;
      float union_area = areas[i] + areas[j] - inter_area;
      float iou = inter_area / union_area;
      if (iou > NMS_THRESH) {
        keep = false;
        break;
      }
    }
    if (keep) {
      keep_ids.push_back(i);
    }
  }
  return keep_ids;
}

bool DecodeOutputs(const float *prob, const int num_anchors,
                   std::vector<NvDsInferParseObjectInfo> &objectList) {
  if (int(GRID_STRIDES.size()) != num_anchors) {
    std::cerr << "Warning: The current resolution does match with the model. "
                 "Please change the value in the code."
              << std::endl;
    return false;
  }

  std::vector<Proposal> proposals = GenerateProposals(prob, num_anchors);
  SortProposals(proposals);
  std::vector<int> keep_ids = GetNMSKeepIDs(proposals);

  // copy results into objectList
  const int n = keep_ids.size();
  objectList.resize(n);
  for (int i = 0; i < n; ++i) {
    NvDsInferParseObjectInfo &obj = objectList[i];
    const Proposal &p = proposals[keep_ids[i]];
    obj.classId = p.label;
    obj.left = p.bbox.x;
    obj.top = p.bbox.y;
    obj.width = p.bbox.width;
    obj.height = p.bbox.height;
    obj.detectionConfidence = p.prob;
  }

  return true;
}

extern "C" bool NvDsInferParseCustomLightDet(
    const std::vector<NvDsInferLayerInfo> &outputLayersInfo,
    const NvDsInferNetworkInfo &networkInfo,
    const NvDsInferParseDetectionParams &detectionParams,
    std::vector<NvDsInferParseObjectInfo> &objectList) {
  const auto output_shape = outputLayersInfo[0].inferDims;
  const int num_anchors = output_shape.d[0];
  const float *prob = (float *)outputLayersInfo[0].buffer;

  return DecodeOutputs(prob, num_anchors, objectList);
}

CHECK_CUSTOM_PARSE_FUNC_PROTOTYPE(NvDsInferParseCustomLightDet);
