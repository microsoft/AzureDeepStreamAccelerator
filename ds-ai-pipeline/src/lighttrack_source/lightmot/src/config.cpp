#include "config.h"
#include <iostream>

int INPUT_W = 416;
int INPUT_H = 416;
float TRACK_THRESH = 0.3;
float HIGH_THRESH = 0.5;
float MATCH_THRESH = 0.8;
float MATCH_THRESH_LOW = 0.5;
float MATCH_THRESH_UNCONFIRMED = 0.7;
int FRAME_RATE = 30;
int TRACK_BUFFER = 60;
int PREDICT_LOST_BUFFER = 0;
int PREDICT_LOST_THRESH = 0;
int NUM_CLASSES = 80;
int NUM_OMP_THREADS = 2;
bool USING_DET_BBOX = false;
int CLIP_BORDER = -1;
int MAX_TIME_LOST = int(FRAME_RATE / 30.0 * TRACK_BUFFER);
