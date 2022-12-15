import { RegionOfInterest } from "../types/RegionOfInterest";

export interface IRegionOfInterestService {
    sensorName: string;
    get: () => Promise<RegionOfInterest[]>;
    update: (regionsOfInterst: RegionOfInterest[]) => Promise<RegionOfInterest[]>; 
}