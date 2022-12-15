import { IRegionOfInterestServiceOptions } from "../interfaces/IRegionOfInterestServiceOptions";

export class RegionOfInterestServiceOptions implements IRegionOfInterestServiceOptions {
    connectionString: string; 
    deviceName: string; 
    moduleId: string;
    sensorName: string;
}