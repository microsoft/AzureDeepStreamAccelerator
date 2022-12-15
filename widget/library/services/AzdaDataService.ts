import { IAzdaDataService } from '../interfaces/IAzdaDataService';
import { BlobServiceClient } from '@azure/storage-blob';
import axios from 'axios';
import { DateFilterMode } from '../enums/DateFilterMode';
import { AzdaData } from '../types/AzdaData';
import { AzdaDataServiceOptions } from './AzdaDataServiceOptions';
import { DateRange } from '../types/DateRange';

export default class AzdaDataService implements IAzdaDataService {
    public sensorName: string;
    private blobServiceClient: BlobServiceClient;
    private baseUrl: string;
    private containerName: string;
    private sasToken: string;

    constructor(azdaDataServiceOptions: AzdaDataServiceOptions) {
        this.blobServiceClient = new BlobServiceClient(azdaDataServiceOptions.sasUrl);
        this.baseUrl = azdaDataServiceOptions.sasUrl.split('?')[0];
        this.containerName = azdaDataServiceOptions.containerName;
        this.sasToken = azdaDataServiceOptions.sasToken;
        this.sensorName = azdaDataServiceOptions.sensorName;
    }

    async get(date: Date, dateFilterMode: DateFilterMode): Promise<AzdaData[]> {
        let azdaData: AzdaData[] = [];
        if (this.blobServiceClient && this.baseUrl && this.containerName) {
            try {
                const dateRange: DateRange = this.calculateDateRange(date, dateFilterMode);

                const containerClient = this.blobServiceClient.getContainerClient(this.containerName);
                const blobList = containerClient.findBlobsByTags(`"Sensor"='${this.sensorName}' AND "Date">'${dateRange.before.toISOString()}' AND "Date"<'${dateRange.after.toISOString()}'`);
                for await (const blob of blobList) {
                    let ext = "";
                    const values = (`${blob.name}`).split('.');
                    const l = values.length;
                    if (l > 0) {
                        ext = values[l - 1];
                    }
                    if (ext === "json") {
                        try {
                            const date = (blob as any).tags.Date;
                            let response = await axios.get(`${this.baseUrl}${this.containerName}/${blob.name}?${this.sasToken}`);
                            if (response.status === 200) {
                                azdaData.push({
                                    date: date,
                                    azdaOutput: response.data,
                                    videoUrl: `${this.baseUrl}${this.containerName}/${blob.name.replace("json", "mp4")}?${this.sasToken}`
                                });
                            }
                        } catch (e) {
                            console.log(e);
                        }
                    }
                }
            } catch (e) {
                console.log(e);
            }
        }
        return azdaData;
    };

    calculateDateRange(date: Date, dateFilterMode: DateFilterMode): DateRange {
        const dateRange: DateRange = {
            before: new Date(date.toISOString()),
            after: new Date(date.toISOString())
        }

        try {
            switch (dateFilterMode) {
                case DateFilterMode.Year:
                    dateRange.before = new Date(dateRange.before.getUTCFullYear());
                    dateRange.after = new Date(dateRange.after.getUTCFullYear());
                    dateRange.before.setDate(dateRange.before.getDate() - 1);
                    dateRange.after.setFullYear(dateRange.after.getFullYear() + 1);
                    break;
                case DateFilterMode.Month:
                    dateRange.before = new Date(`${dateRange.before.getUTCFullYear()}-${dateRange.before.getMonth() + 1}`);
                    dateRange.after = new Date(`${dateRange.after.getUTCFullYear()}-${dateRange.after.getMonth() + 1}`);
                    dateRange.before.setDate(dateRange.before.getDate() - 1);
                    dateRange.after.setMonth(dateRange.after.getMonth() + 1);
                    break;
                case DateFilterMode.Week:
                    dateRange.before.setDate(dateRange.before.getDate() + 0 - dateRange.before.getDay() - 1);
                    dateRange.after.setDate(dateRange.after.getDate() + 7);
                    break;
                case DateFilterMode.Day:
                    dateRange.before.setDate(dateRange.before.getDate() - 1);
                    dateRange.after.setDate(dateRange.after.getDate() + 1);
                    break;
                case DateFilterMode.Hour:
                    dateRange.before.setHours(dateRange.before.getHours() - 1);
                    dateRange.after.setHours(dateRange.after.getHours() + 1);
                    break;
                case DateFilterMode.Minute:
                    dateRange.before.setMinutes(dateRange.before.getMinutes() - 1);
                    dateRange.after.setMinutes(dateRange.after.getMinutes() + 1);
                    break;
                case DateFilterMode.Second:
                    dateRange.before.setSeconds(dateRange.before.getSeconds() - 1);
                    dateRange.after.setSeconds(dateRange.after.getSeconds() + 1);
                    break;
                case DateFilterMode.Millisecond:
                    dateRange.before.setMilliseconds(dateRange.before.getMilliseconds() - 1);
                    dateRange.after.setMilliseconds(dateRange.after.getMilliseconds() + 1);
                    break;
            }
        } catch (e) {
            console.log(e);
        }

        return dateRange;
    }
}