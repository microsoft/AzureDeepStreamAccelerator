import { IAzdaDataServiceOptions } from "../interfaces/IAzdaDataServiceOptions";

export class AzdaDataServiceOptions implements IAzdaDataServiceOptions {
    sasUrl: string;
    sasToken: string;
    containerName: string;
    sensorName: string;
}