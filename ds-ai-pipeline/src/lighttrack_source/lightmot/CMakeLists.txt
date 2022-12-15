set(CMAKE_BUILD_TYPE RelWithDebInfo)

cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 14)

set(DS_ROOT_DIR /opt/nvidia/deepstream/deepstream)
set(DS_LIBS_DIR ${DS_ROOT_DIR}/lib)
set(DS_INCLUDES_DIR ${DS_ROOT_DIR}/sources/includes)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
find_package(PkgConfig REQUIRED)
pkg_search_module(GLIB REQUIRED glib-2.0)
find_package(OpenMP)

include_directories(${GLIB_INCLUDE_DIRS})
include_directories(${DS_INCLUDES_DIR})
include_directories(${CMAKE_SOURCE_DIR}/include)
file(GLOB SOURCE_FILES ${CMAKE_SOURCE_DIR}/src/*.cpp)

link_directories(${DS_LIBS_DIR})
add_library(lightmot SHARED ${SOURCE_FILES})
target_link_libraries(lightmot nvds_meta OpenMP::OpenMP_CXX)
