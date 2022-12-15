#pragma once

#include <nvdstracker.h>
#include <array>
#include <cstddef>
#include <utility>
#include <vector>

typedef signed int int_t;
typedef unsigned int uint_t;
typedef float cost_t;
typedef char boolean;

template <typename T>
using Vec2 = std::vector<std::vector<T>>;

struct NvObject {
  float x, y, width, height;
  int label;
  float prob;
  NvMOTObjToTrack *objectToTrack;
  inline float Area() const { return width * height; }
  inline float Left() const { return x; }
  inline float Top() const { return y; }
  inline float Right() const { return x + width; }
  inline float Bottom() const { return y + height; }
  inline float CX() const { return x + width / 2; }
  inline float CY() const { return y + height / 2; }
  inline float Aspect() const { return width / height; }
};
