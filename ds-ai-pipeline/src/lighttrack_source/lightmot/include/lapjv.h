#pragma once

#include <utility>
#include <vector>
#include "data_type.h"

void lapjv(const Vec2<float> &cost, std::vector<int> &rowsol,
           std::vector<int> &colsol, cost_t cost_limit);

std::vector<std::pair<int, int>> LinearAssignment(
    Vec2<float> costs, int a_size, int b_size, float thresh,
    std::vector<int> &unmatched_a, std::vector<int> &unmatched_b);
