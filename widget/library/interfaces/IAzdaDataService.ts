import { DateFilterMode } from "../enums/DateFilterMode";
import { AzdaData } from "../types/AzdaData";

export interface IAzdaDataService {
    sensorName: string;
    get: (date: Date, dateFilterMode: DateFilterMode) => Promise<AzdaData[]>;
    onGetAzdaData?: (azdaData: AzdaData[]) => void;
}