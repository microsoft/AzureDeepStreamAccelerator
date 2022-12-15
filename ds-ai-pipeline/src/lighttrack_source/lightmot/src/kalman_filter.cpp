#include "kalman_filter.h"
#include <eigen3/Eigen/Cholesky>

constexpr int NDIM = 4;
bool KALMAN_FILTER_INITED = false;

Eigen::Matrix<float, NDIM * 2, NDIM * 2, Eigen::RowMajor> MOTION_MAT;
Eigen::Matrix<float, NDIM * 2, NDIM * 2, Eigen::RowMajor> MOTION_MAT_T;

Eigen::Matrix<float, NDIM, NDIM * 2, Eigen::RowMajor> UPDATE_MAT;
Eigen::Matrix<float, NDIM * 2, NDIM, Eigen::RowMajor> UPDATE_MAT_T;

float STD_WEIGHT_POS;
float STD_WEIGHT_VEL;

KalmanFilter::KalmanFilter() {
  if (!KALMAN_FILTER_INITED) {
    KALMAN_FILTER_INITED = true;

    MOTION_MAT = Eigen::MatrixXf::Identity(NDIM * 2, NDIM * 2);
    for (int i = 0; i < NDIM; ++i) {
      MOTION_MAT(i, NDIM + i) = 1.0;
    }
    MOTION_MAT_T = MOTION_MAT.transpose();

    UPDATE_MAT = Eigen::MatrixXf::Identity(NDIM, NDIM * 2);
    UPDATE_MAT_T = UPDATE_MAT.transpose();

    STD_WEIGHT_POS = 1.0 / 20;
    STD_WEIGHT_VEL = 1.0 / 160;
  }
}

KAL_STATE KalmanFilter::Init(const BOX_T &box) const {
  BOX_T pos = box;
  BOX_T vel;
  for (int i = 0; i < NDIM; ++i) vel(i) = 0;

  KAL_MEAN mean;
  for (int i = 0; i < NDIM * 2; ++i) {
    mean(i) = i < 4 ? pos(i) : vel(i - 4);
  }

  KAL_MEAN std;
  // since the bbox may be cropped in image edge
  const float e = std::max(box[3], box[2] * box[3]);

  std(0) = 2 * STD_WEIGHT_POS * e;
  std(1) = 2 * STD_WEIGHT_POS * e;
  std(2) = 1e-2;
  std(3) = 2 * STD_WEIGHT_POS * e;

  std(4) = 10 * STD_WEIGHT_VEL * e;
  std(5) = 10 * STD_WEIGHT_VEL * e;
  std(6) = 1e-5;
  std(7) = 10 * STD_WEIGHT_VEL * e;

  KAL_VAR var = KAL_MEAN(std.array().square()).asDiagonal();
  return {mean, var};
}

KAL_STATE KalmanFilter::Predict(const KAL_STATE &state) const {
  const KAL_MEAN &mean = state.first;
  const KAL_VAR &var = state.second;
  BOX_T std_pos;
  std_pos << STD_WEIGHT_POS * mean(3), STD_WEIGHT_POS * mean(3), 1e-2,
      STD_WEIGHT_POS * mean(3);
  BOX_T std_vel;
  std_vel << STD_WEIGHT_VEL * mean(3), STD_WEIGHT_VEL * mean(3), 1e-5,
      STD_WEIGHT_VEL * mean(3);

  KAL_MEAN var_mat;
  var_mat.block<1, 4>(0, 0) = std_pos;
  var_mat.block<1, 4>(0, 4) = std_vel;

  KAL_VAR motion_var = KAL_MEAN(var_mat.array().square()).asDiagonal();
  KAL_MEAN new_mean = MOTION_MAT * mean.transpose();
  KAL_VAR new_var = MOTION_MAT * var * (MOTION_MAT_T);
  new_var += motion_var;

  return {new_mean, new_var};
}

KAL_STATE KalmanFilter::Update(const KAL_STATE &state, const BOX_T &box) const {
  const KAL_MEAN &mean = state.first;
  const KAL_VAR &var = state.second;
  // project
  Eigen::Matrix<float, 1, NDIM, Eigen::RowMajor> proj_mean =
      UPDATE_MAT * mean.transpose();
  Eigen::Matrix<float, NDIM, NDIM, Eigen::RowMajor> proj_var =
      UPDATE_MAT * var * UPDATE_MAT_T;
  {
    BOX_T std;
    std << STD_WEIGHT_POS * mean(3), STD_WEIGHT_POS * mean(3), 1e-1,
        STD_WEIGHT_POS * mean(3);
    Eigen::Matrix<float, NDIM, NDIM> diag = std.asDiagonal();
    diag = diag.array().square().matrix();
    proj_var += diag;
  }

  Eigen::Matrix<float, NDIM, NDIM * 2> M = (var * UPDATE_MAT_T).transpose();
  Eigen::Matrix<float, NDIM, NDIM * 2> gain = proj_var.llt().solve(M);
  Eigen::Matrix<float, NDIM * 2, NDIM> gain_T = gain.transpose();

  Eigen::Matrix<float, 1, NDIM> innovation = box - proj_mean;

  KAL_MEAN new_mean = (mean.array() + (innovation * gain).array()).matrix();
  KAL_VAR new_var = var - gain_T * proj_var * gain;
  return {new_mean, new_var};
}
