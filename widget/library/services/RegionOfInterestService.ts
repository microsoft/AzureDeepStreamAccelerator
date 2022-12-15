import { IRegionOfInterestService } from '../interfaces/IRegionOfInterestService';
import { RegionOfInterest } from '../types/RegionOfInterest';
import { Registry } from 'azure-iothub';
import { RegionOfInterestServiceOptions } from './RegionOfInterestServiceOptions';

export default class RegionOfInterestService implements IRegionOfInterestService {
    private registry: Registry;
    private deviceName: string;
    private moduleId: string;
    public sensorName: string;

    constructor(regionOfInterestServiceOptions: RegionOfInterestServiceOptions) {
        this.registry = Registry.fromConnectionString(regionOfInterestServiceOptions.connectionString);
        this.deviceName = regionOfInterestServiceOptions.deviceName;
        this.moduleId = regionOfInterestServiceOptions.moduleId;
        this.sensorName = regionOfInterestServiceOptions.sensorName;
    }

    async get() {
        let regionsOfInterest = [];
        if (this.registry && this.deviceName && this.moduleId && this.sensorName) {
            const res = await this.registry.getModuleTwin(this.deviceName, this.moduleId);
            if (res.httpResponse.statusCode === 200) {
                const moduleTwin = res.responseBody;
                if (moduleTwin) {
                    try {
                        const sensor = moduleTwin.properties.desired.azdaSkill.components.sensors.find((sensor: any) => {
                            return sensor.name === this.sensorName
                        });
                        if (sensor) {
                            regionsOfInterest = sensor.regionsOfInterest;
                        }
                    } catch (e) {
                        console.log(e);
                    }
                }
            }
        }

        return regionsOfInterest;
    };

    async update(regionsOfInterest: RegionOfInterest[]): Promise<RegionOfInterest[]> {
        let updatedRegionsOfInterest = [];
        if (this.registry && this.deviceName && this.moduleId && this.sensorName) {
            const reportedResponse = await this.registry.getModuleTwin(this.deviceName, this.moduleId);
            if (reportedResponse.httpResponse.statusCode === 200) {
                const reportedModuleTwin = reportedResponse.responseBody;
                if (reportedModuleTwin) {
                    try {
                        let reportedSensorIndex: number = -1;
                        const reportedSensor = reportedModuleTwin.properties.desired.azdaSkill.components.sensors.find((sensor: any, index: number) => {
                            if (sensor.name === this.sensorName) {
                                reportedSensorIndex = index;
                                return true;
                            } else {
                                return false;
                            }
                        });
                        if (reportedSensor && reportedSensorIndex !== -1) {
                            reportedModuleTwin.properties.desired.azdaSkill.components.sensors[reportedSensorIndex].regionsOfInterest = regionsOfInterest;
                            const updateResponse = await this.registry.updateModuleTwin(this.deviceName, this.moduleId, reportedModuleTwin, '*');
                            if (updateResponse.httpResponse.statusCode === 200) {
                                const updatedModuleTwin = updateResponse.responseBody;
                                if (updatedModuleTwin) {
                                    const updatedSensor = updatedModuleTwin.properties.desired.azdaSkill.components.sensors.find((sensor: any) => {
                                        return sensor.name === this.sensorName
                                    });
                                    if (updatedSensor) {
                                        updatedRegionsOfInterest = updatedSensor.regionsOfInterest;
                                    }
                                }
                            }
                        }
                    } catch (e) {
                        console.log(e);
                    }
                }
            }
        }
        return updatedRegionsOfInterest;
    }
}