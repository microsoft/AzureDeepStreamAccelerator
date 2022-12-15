set(CMAKE_BUILD_TYPE RelWithDebInfo)

cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 14)

set(DS_ROOT_DIR /opt/nvidia/deepstream/deepstream)
set(DS_LIBS_DIR ${DS_ROOT_DIR}/lib)
set(DS_INCLUDES_DIR ${DS_ROOT_DIR}/sources/includes)

set(CUDA_INCLUDES_DIR /usr/local/cuda/include)

include_directories(${DS_INCLUDES_DIR})
include_directories(${CUDA_INCLUDES_DIR})

link_directories(${DS_LIBS_DIR})
add_library(lightdet SHARED ./lightdet.cpp)
target_link_libraries(lightdet)
