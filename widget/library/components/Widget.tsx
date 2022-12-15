import * as React from "react";
import { WidgetMode } from "../enums/WidgetMode";
import { IAzdaDataService } from "../interfaces/IAzdaDataService";
import { IAzdaDataServiceOptions } from "../interfaces/IAzdaDataServiceOptions";
import { IRegionOfInterestService } from "../interfaces/IRegionOfInterestService";
import { IRegionOfInterestServiceOptions } from "../interfaces/IRegionOfInterestServiceOptions";
import AzdaDataService from "../services/AzdaDataService";
import { AzdaDataServiceOptions } from "../services/AzdaDataServiceOptions";
import RegionOfInterestService from "../services/RegionOfInterestService";
import { RegionOfInterestServiceOptions } from "../services/RegionOfInterestServiceOptions";
import { Detection } from "../types/Detection";
import { Inference } from "../types/Inference";
import { AzdaData } from "../types/AzdaData";
import { RegionOfInterest } from "../types/RegionOfInterest";
import EditorContainer from "./editor/EditorContainer";
import PlayerContainer from "./player/PlayerContainer";

export interface IWidgetProps {
    azdaDataServiceOptions: IAzdaDataServiceOptions;
    regionOfInterestServiceOptions: IRegionOfInterestServiceOptions;

    mode?: WidgetMode | null;

    azdaDataService?: IAzdaDataService;
    regionOfInterestService?: IRegionOfInterestService;

    onInference?: (inference: Inference) => void;
    onAzdaData?: (azdaData: AzdaData[]) => void;

    drawDetection?: (context: CanvasRenderingContext2D, detection: Detection) => void;
    drawRegionOfInterest?: (context: CanvasRenderingContext2D, regionOfInterest: RegionOfInterest) => void;
}

export interface IWidgetState {
    mode: WidgetMode;
    width: number;
    height: number;
}

class Widget extends React.Component<IWidgetProps, IWidgetState> {
    private azdaDataService: IAzdaDataService;
    private regionOfInterestService: IRegionOfInterestService;

    constructor(props: IWidgetProps) {
        super(props);

        this.state = {
            mode: this.props.mode ? this.props.mode : WidgetMode.Play,
            // NOTE: 16:9 aspect ratio
            width: 720,
            height: 405
        };

        this.azdaDataService = this.props.azdaDataService ?
            new (this.props.azdaDataService as any)(this.props.azdaDataServiceOptions) :
            new AzdaDataService((this.props.azdaDataServiceOptions as AzdaDataServiceOptions));

        this.regionOfInterestService = this.props.regionOfInterestService ?
            new (this.props.regionOfInterestService as any)(this.props.regionOfInterestServiceOptions) :
            new RegionOfInterestService((this.props.regionOfInterestServiceOptions as RegionOfInterestServiceOptions));
    }

    render() {
        return (
            <React.Fragment>
                <div
                    style={{
                        margin: 10
                    }}
                >
                    <PlayerContainer
                        azdaDataService={this.azdaDataService}
                        width={this.state.width}
                        height={this.state.height}
                        widgetMode={this.state.mode}
                        changeWidgetMode={this.changeMode}
                        onInference={this.props.onInference}
                        onAzdaData={this.props.onAzdaData}
                        drawDetection={this.props.drawDetection}
                        drawRegionOfInterest={this.props.drawRegionOfInterest}
                    />
                    {
                        this.state.mode === WidgetMode.Edit ? (
                            <EditorContainer
                                regionOfInterestService={this.regionOfInterestService}
                                width={this.state.width}
                                height={this.state.height}
                                widgetMode={this.state.mode}
                                changeWidgetMode={this.changeMode}
                            />
                        ) : null
                    }
                </div>
            </React.Fragment>
        )
    }

    changeMode = (mode: WidgetMode): void => {
        this.setState({
            mode: mode
        });
    }
}

export default Widget;
