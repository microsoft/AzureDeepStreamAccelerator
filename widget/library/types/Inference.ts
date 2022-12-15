import { SourceInfo } from "./SourceInfo";
import { Detection } from "./Detection";
import { InferenceType } from "../enums/InferenceType";

export type Inference = {
    sourceInfo: SourceInfo;
    type: InferenceType;
    id: string;
    detections: Detection[];
};
