#pragma once
#include <eigen3/Eigen/Core>
#include <eigen3/Eigen/Dense>
#include <utility>

typedef Eigen::Matrix<float, 1, 4, Eigen::RowMajor> BOX_T;
typedef Eigen::Matrix<float, 1, 8, Eigen::RowMajor> KAL_MEAN;
typedef Eigen::Matrix<float, 8, 8, Eigen::RowMajor> KAL_VAR;
using KAL_STATE = std::pair<KAL_MEAN, KAL_VAR>;

class KalmanFilter {
 public:
  KalmanFilter();

  KAL_STATE Init(const BOX_T &box) const;
  KAL_STATE Predict(const KAL_STATE &state) const;
  KAL_STATE Update(const KAL_STATE &state, const BOX_T &box) const;
};
