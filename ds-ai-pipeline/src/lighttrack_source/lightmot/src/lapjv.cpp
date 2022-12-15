#include "lapjv.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <algorithm>
#include <numeric>

#define LAPJV_LARGE 1000000

/** Column-reduction and reduction transfer for a dense cost matrix.
 */
int_t _ccrrt_dense(const uint_t n, cost_t *cost[], int_t *free_rows, int_t *x,
                   int_t *y, cost_t *v) {
  int_t n_free_rows;

  for (uint_t i = 0; i < n; i++) {
    x[i] = -1;
    v[i] = LAPJV_LARGE;
    y[i] = 0;
  }
  for (uint_t i = 0; i < n; i++) {
    for (uint_t j = 0; j < n; j++) {
      const cost_t c = cost[i][j];
      if (c < v[j]) {
        v[j] = c;
        y[j] = i;
      }
    }
  }
  boolean *unique = new boolean[n];
  memset(unique, 1, n);
  {
    int_t j = n;
    do {
      j--;
      const int_t i = y[j];
      if (x[i] < 0) {
        x[i] = j;
      } else {
        unique[i] = 0;
        y[j] = -1;
      }
    } while (j > 0);
  }
  n_free_rows = 0;
  for (uint_t i = 0; i < n; i++) {
    if (x[i] < 0) {
      free_rows[n_free_rows++] = i;
    } else if (unique[i]) {
      const int_t j = x[i];
      cost_t min = LAPJV_LARGE;
      for (uint_t j2 = 0; j2 < n; j2++) {
        if (j2 == (uint_t)j) {
          continue;
        }
        const cost_t c = cost[i][j2] - v[j2];
        if (c < min) {
          min = c;
        }
      }
      v[j] -= min;
    }
  }
  delete[] unique;
  return n_free_rows;
}

/** Augmenting row reduction for a dense cost matrix.
 */
int_t _carr_dense(const uint_t n, cost_t *cost[], const uint_t n_free_rows,
                  int_t *free_rows, int_t *x, int_t *y, cost_t *v) {
  uint_t current = 0;
  int_t new_free_rows = 0;
  uint_t rr_cnt = 0;
  while (current < n_free_rows) {
    int_t i0;
    int_t j1, j2;
    cost_t v1, v2, v1_new;
    boolean v1_lowers;

    rr_cnt++;
    const int_t free_i = free_rows[current++];
    j1 = 0;
    v1 = cost[free_i][0] - v[0];
    j2 = -1;
    v2 = LAPJV_LARGE;
    for (uint_t j = 1; j < n; j++) {
      const cost_t c = cost[free_i][j] - v[j];
      if (c < v2) {
        if (c >= v1) {
          v2 = c;
          j2 = j;
        } else {
          v2 = v1;
          v1 = c;
          j2 = j1;
          j1 = j;
        }
      }
    }
    i0 = y[j1];
    v1_new = v[j1] - (v2 - v1);
    v1_lowers = v1_new < v[j1];
    // v2, v1_new, v1_lowers, v[j1] - v1_new);
    if (rr_cnt < current * n) {
      if (v1_lowers) {
        v[j1] = v1_new;
      } else if (i0 >= 0 && j2 >= 0) {
        j1 = j2;
        i0 = y[j2];
      }
      if (i0 >= 0) {
        if (v1_lowers) {
          free_rows[--current] = i0;
        } else {
          free_rows[new_free_rows++] = i0;
        }
      }
    } else {
      // current, n);
      if (i0 >= 0) {
        free_rows[new_free_rows++] = i0;
      }
    }
    x[free_i] = j1;
    y[j1] = free_i;
  }
  return new_free_rows;
}

/** Find columns with minimum d[j] and put them on the SCAN list.
 */
uint_t _find_dense(const uint_t n, uint_t lo, cost_t *d, int_t *cols, int_t *) {
  uint_t hi = lo + 1;
  cost_t mind = d[cols[lo]];
  for (uint_t k = hi; k < n; k++) {
    int_t j = cols[k];
    if (d[j] <= mind) {
      if (d[j] < mind) {
        hi = lo;
        mind = d[j];
      }
      cols[k] = cols[hi];
      cols[hi++] = j;
    }
  }
  return hi;
}

// Scan all columns in TODO starting from arbitrary column in SCAN
// and try to decrease d of the TODO columns using the SCAN column.
int_t _scan_dense(const uint_t n, cost_t *cost[], uint_t *plo, uint_t *phi,
                  cost_t *d, int_t *cols, int_t *pred, int_t *y, cost_t *v) {
  uint_t lo = *plo;
  uint_t hi = *phi;
  cost_t h, cred_ij;

  while (lo != hi) {
    int_t j = cols[lo++];
    const int_t i = y[j];
    const cost_t mind = d[j];
    h = cost[i][j] - v[j] - mind;
    // For all columns in TODO
    for (uint_t k = hi; k < n; k++) {
      j = cols[k];
      cred_ij = cost[i][j] - v[j] - h;
      if (cred_ij < d[j]) {
        d[j] = cred_ij;
        pred[j] = i;
        if (cred_ij == mind) {
          if (y[j] < 0) {
            return j;
          }
          cols[k] = cols[hi];
          cols[hi++] = j;
        }
      }
    }
  }
  *plo = lo;
  *phi = hi;
  return -1;
}

/** Single iteration of modified Dijkstra shortest path algorithm as explained
 * in the JV paper.
 *
 * This is a dense matrix version.
 *
 * \return The closest free column index.
 */
int_t find_path_dense(const uint_t n, cost_t *cost[], const int_t start_i,
                      int_t *y, cost_t *v, int_t *pred) {
  uint_t lo = 0, hi = 0;
  int_t final_j = -1;
  uint_t n_ready = 0;
  int_t *cols = new int_t[n];
  cost_t *d = new cost_t[n];

  for (uint_t i = 0; i < n; i++) {
    cols[i] = i;
    pred[i] = start_i;
    d[i] = cost[start_i][i] - v[i];
  }
  while (final_j == -1) {
    // No columns left on the SCAN list.
    if (lo == hi) {
      n_ready = lo;
      hi = _find_dense(n, lo, d, cols, y);
      for (uint_t k = lo; k < hi; k++) {
        const int_t j = cols[k];
        if (y[j] < 0) {
          final_j = j;
        }
      }
    }
    if (final_j == -1) {
      final_j = _scan_dense(n, cost, &lo, &hi, d, cols, pred, y, v);
    }
  }

  {
    const cost_t mind = d[cols[lo]];
    for (uint_t k = 0; k < n_ready; k++) {
      const int_t j = cols[k];
      v[j] += d[j] - mind;
    }
  }

  delete[] cols;
  delete[] d;

  return final_j;
}

/** Augment for a dense cost matrix.
 */
int_t _ca_dense(const uint_t n, cost_t *cost[], const uint_t n_free_rows,
                int_t *free_rows, int_t *x, int_t *y, cost_t *v) {
  int_t *pred = new int_t[n];

  for (int_t *pfree_i = free_rows; pfree_i < free_rows + n_free_rows;
       pfree_i++) {
    int_t i = -1, j;
    uint_t k = 0;

    j = find_path_dense(n, cost, *pfree_i, y, v, pred);
    while (i != *pfree_i) {
      i = pred[j];
      y[j] = i;
      std::swap(j, x[i]);
      k++;
    }
  }
  delete[] pred;
  return 0;
}

/** Solve dense sparse LAP.
 */
int lapjv_internal(const uint_t n, cost_t *cost[], int_t *x, int_t *y) {
  int ret;
  int_t *free_rows = new int_t[n];
  cost_t *v = new cost_t[n];

  ret = _ccrrt_dense(n, cost, free_rows, x, y, v);
  int i = 0;
  while (ret > 0 && i < 2) {
    ret = _carr_dense(n, cost, ret, free_rows, x, y, v);
    i++;
  }
  if (ret > 0) {
    ret = _ca_dense(n, cost, ret, free_rows, x, y, v);
  }
  delete[] v;
  delete[] free_rows;
  return ret;
}

void lapjv(const Vec2<float> &cost, std::vector<int> &rowsol,
           std::vector<int> &colsol, cost_t cost_limit) {
  const size_t n_rows = cost.size();
  if (n_rows == 0) return;
  const size_t n_cols = cost[0].size();
  if (n_cols == 0) return;

  const size_t n = n_rows + n_cols;
  float fill_value = cost_limit / 2.0;
  if (cost_limit == LONG_MAX) {
    float fill_value = -1;
    for (size_t i = 0; i < n_rows; ++i) {
      for (auto v : cost[i]) {
        if (v > fill_value) fill_value = v;
      }
    }
    fill_value += 1;
  }

  cost_t **cost_ptr;
  cost_ptr = new cost_t *[n];
  for (size_t i = 0; i < n; ++i) {
    cost_ptr[i] = new cost_t[n];
    // fill_value
    std::fill(cost_ptr[i], cost_ptr[i] + n, fill_value);
  }

  for (size_t i = n_rows; i < n; ++i) {
    std::fill(cost_ptr[i] + n_cols, cost_ptr[i] + n, 0);
  }
  for (size_t i = 0; i < n_rows; ++i) {
    std::copy(cost[i].data(), cost[i].data() + n_cols, cost_ptr[i]);
  }

  rowsol.resize(n);
  colsol.resize(n);

  int ret = lapjv_internal(n, cost_ptr, rowsol.data(), colsol.data());
  if (ret != 0) {
    exit(0);
  }

  rowsol.resize(n_rows);
  colsol.resize(n_cols);
  for (size_t i = 0; i < n_rows; ++i) {
    if (rowsol[i] >= int(n_cols)) rowsol[i] = -1;
  }
  for (size_t i = 0; i < n_cols; ++i) {
    if (colsol[i] >= int(n_rows)) colsol[i] = -1;
  }

  for (size_t i = 0; i < n; ++i) {
    delete[] cost_ptr[i];
  }
  delete[] cost_ptr;
}

std::vector<std::pair<int, int>> LinearAssignment(
    Vec2<float> costs, int a_size, int b_size, float thresh,
    std::vector<int> &unmatched_a, std::vector<int> &unmatched_b) {
  if (costs.empty() || costs[0].empty()) {
    unmatched_a.resize(a_size);
    std::iota(unmatched_a.begin(), unmatched_a.end(), 0);
    unmatched_b.resize(b_size);
    std::iota(unmatched_b.begin(), unmatched_b.end(), 0);
    return {};
  }
  const size_t R = costs.size();
  const size_t C = costs[0].size();

  std::vector<int> rowsol;
  std::vector<int> colsol;
  lapjv(costs, rowsol, colsol, thresh);

  std::vector<std::pair<int, int>> matches;
  for (size_t i = 0; i < rowsol.size(); ++i) {
    if (rowsol[i] >= 0) {
      matches.emplace_back(i, rowsol[i]);
    } else {
      unmatched_a.push_back(i);
    }
  }

  for (size_t i = 0; i < colsol.size(); ++i) {
    if (colsol[i] < 0) {
      unmatched_b.push_back(i);
    }
  }
  return matches;
}
