import * as React from 'react';
import { WidgetMode } from '../../enums/WidgetMode';
import { IAzdaDataService } from '../../interfaces/IAzdaDataService';
import { Detection } from '../../types/Detection';
import { Inference } from '../../types/Inference';
import { AzdaData } from '../../types/AzdaData';
import { RegionOfInterest } from '../../types/RegionOfInterest';
import { PlayerMode } from '../../enums/PlayerMode';
import Player from './Player';
import PlayerToolbar from './PlayerToolbar';
import PlayerTable from './PlayerTable';
import { DateFilterMode } from '../../enums/DateFilterMode';

export interface IPlayerContainerProps {
    azdaDataService: IAzdaDataService;
    width: number;
    height: number;
    widgetMode: WidgetMode;

    changeWidgetMode: (widgetMode: WidgetMode) => void;

    onInference?: (inference: Inference) => void;
    onAzdaData?: (azdaData: AzdaData[]) => void;

    drawDetection?: (context: CanvasRenderingContext2D, detection: Detection) => void;
    drawRegionOfInterest?: (context: CanvasRenderingContext2D, regionOfInterest: RegionOfInterest) => void;
}

export interface IPlayerContainerState {
    azdaDataList: AzdaData[];
    azdaData: AzdaData | null;
    playerMode: PlayerMode;
    dateFilterMode: DateFilterMode;
    searchDate: Date;
    drawDetections: boolean;
    drawRegionsOfInterest: boolean;
    autoPlay: boolean;
    nextVideoUrl: string;
}

export default class PlayerContainer extends React.Component<IPlayerContainerProps, IPlayerContainerState> {
    constructor(props: IPlayerContainerProps) {
        super(props);

        this.state = {
            azdaDataList: [],
            azdaData: null,
            playerMode: PlayerMode.Pause,
            dateFilterMode: DateFilterMode.Hour,
            searchDate: new Date(),
            drawDetections: true,
            drawRegionsOfInterest: true,
            autoPlay: true,
            nextVideoUrl: ''
        }
    }

    public render() {
        return (
            <React.Fragment>
                <div
                    style={{
                        position: 'relative'
                    }}
                >
                    <div
                        style={{
                            position: 'absolute',
                            left: 0,
                            top: 0,
                            margin: 0,
                            padding: 0
                        }}
                    >
                        <Player
                            width={this.props.width}
                            height={this.props.height}
                            playerMode={this.state.playerMode}
                            autoPlay={this.state.autoPlay}
                            nextVideoUrl={this.state.nextVideoUrl}
                            nextAzdaData={this.nextAzdaData}
                            widgetMode={this.props.widgetMode}
                            drawDetections={this.state.drawDetections}
                            drawRegionsOfInterest={this.state.drawRegionsOfInterest}
                            drawDetection={this.props.drawDetection}
                            drawRegionOfInterest={this.props.drawRegionOfInterest}
                            changePlayerMode={this.changePlayerMode}
                            azdaData={this.state.azdaData}
                        />
                    </div>
                    {
                        this.props.widgetMode === WidgetMode.Play ? (
                            <React.Fragment>
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: 0,
                                        top: 435,
                                        margin: 0,
                                        padding: 0
                                    }}
                                >
                                    <PlayerToolbar
                                        width={this.props.width}
                                        playerMode={this.state.playerMode}
                                        autoPlay={this.state.autoPlay}
                                        drawDetections={this.state.drawDetections}
                                        drawRegionsOfInterest={this.state.drawRegionsOfInterest}
                                        changePlayerMode={this.changePlayerMode}
                                        changeAutoPlay={this.changeAutoPlay}
                                        changeDrawDetections={this.changeDrawDetections}
                                        changeDrawRegionsOfInterest={this.changeDrawRegionsOfInterest}
                                        changeWidgetMode={this.props.changeWidgetMode}
                                        previousAzdaData={this.previousAzdaData}
                                        nextAzdaData={this.nextAzdaData}
                                    />
                                </div>
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: 750,
                                        top: 0,
                                        margin: 0,
                                        padding: 0
                                    }}
                                >
                                    <PlayerTable
                                        dateFilterMode={this.state.dateFilterMode}
                                        searchDate={this.state.searchDate}
                                        changeSearchDate={this.changeSearchDate}
                                        changeDateFilterMode={this.changeDateFilterMode}
                                        azdaDataList={this.state.azdaDataList}
                                        azdaData={this.state.azdaData}
                                        changeAzdaData={this.changeAzdaData}
                                    />
                                </div>
                            </React.Fragment>
                        ) : null
                    }
                </div>
            </React.Fragment >
        );
    }

    changePlayerMode = (playerMode: PlayerMode): void => {
        this.setState({
            playerMode: playerMode
        });
    }

    changeAutoPlay = (autoPlay: boolean): void => {
        this.setState({
            autoPlay: autoPlay
        });
    }

    changeDateFilterMode = (dateFilterMode: DateFilterMode): void => {
        this.setState({
            dateFilterMode: dateFilterMode
        }, () => {
            this.getAzdadata(this);
        });
    }

    changeSearchDate = (searchDate: Date): void => {
        this.setState({
            searchDate: searchDate
        }, () => {
            this.getAzdadata(this);
        });
    }

    changeDrawDetections = (drawDetections: boolean): void => {
        this.setState({
            drawDetections: drawDetections
        });
    }

    changeDrawRegionsOfInterest = (drawRegionsOfInterest: boolean): void => {
        this.setState({
            drawRegionsOfInterest: drawRegionsOfInterest
        });
    }

    previousAzdaData = (): void => {
        if (this.state.azdaData) {
            const index = this.state.azdaDataList.indexOf(this.state.azdaData);
            if (index - 1 >= 0) {
                this.changeAzdaData(
                    this.state.azdaDataList[index - 1],
                    this.state.azdaDataList[index].videoUrl
                );
            }
        }
    }

    nextAzdaData = (): void => {
        if (this.state.azdaData) {
            const index = this.state.azdaDataList.indexOf(this.state.azdaData);
            if (index + 1 < this.state.azdaDataList.length) {
                this.changeAzdaData(
                    this.state.azdaDataList[index + 1],
                    index + 2 < this.state.azdaDataList.length ? this.state.azdaDataList[index + 2].videoUrl : ''
                );
            }
        }
    }

    changeAzdaData = (azdaData: AzdaData, nextVideoUrl?: string): void => {
        this.setState({
            azdaData: azdaData,
            playerMode: PlayerMode.Play,
            nextVideoUrl: nextVideoUrl ? nextVideoUrl : ''
        });
    }

    async getAzdadata(playerContainer: PlayerContainer): Promise<AzdaData[]> {
        this.setState({
            azdaDataList: [],
            azdaData: null,
            autoPlay: false
        });
        const azdaDataList = await this.props.azdaDataService.get(this.state.searchDate, this.state.dateFilterMode);
        playerContainer.setState({
            azdaDataList: azdaDataList,
            azdaData: azdaDataList.length > 0 ? azdaDataList[0] : null,
            autoPlay: azdaDataList.length > 0
        });
        return azdaDataList;
    }
}
