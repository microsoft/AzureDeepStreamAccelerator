import { Inference } from "./Inference";
import { Event } from "./Event";
import { RegionOfInterest } from "./RegionOfInterest";

export type AzdaOutput = {
    inferences: Inference[];
    events: Event[];
    regionsOfInterest: RegionOfInterest[];
    schemaVersion: string;
};
