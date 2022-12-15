import * as React from 'react';

import { Card } from '@fluentui/react-components/unstable';
import { Button, ToggleButton } from "@fluentui/react-components";
import { Live24Regular, SelectObjectSkewEdit24Regular, RectangleLandscape24Regular, Shapes24Regular, FullScreenMaximize24Regular, Previous24Regular, Next24Regular, Play24Regular, Pause24Regular } from "@fluentui/react-icons";
import { PlayerMode } from '../../enums/PlayerMode';
import { WidgetMode } from '../../enums/WidgetMode';

export interface IPlayerToolbarProps {
    width: number;
    playerMode: PlayerMode;
    autoPlay: boolean;
    drawDetections: boolean;
    drawRegionsOfInterest: boolean;
    changePlayerMode: (playerMode: PlayerMode) => void;
    changeAutoPlay: (autoPlay: boolean) => void;
    changeDrawDetections: (drawDetections: boolean) => void;
    changeDrawRegionsOfInterest: (drawRegionsOfInterest: boolean) => void;
    changeWidgetMode: (widgetMode: WidgetMode) => void;
    previousAzdaData: () => void;
    nextAzdaData: () => void;
}

export interface IPlayerToolbarState {

}

export default class PlayerToolbar extends React.Component<IPlayerToolbarProps, IPlayerToolbarState> {
    constructor(props: IPlayerToolbarProps) {
        super(props);

        this.state = {

        }
    }

    public render() {
        return (
            <React.Fragment>
                <Card
                    style={{
                        width: this.props.width,
                        display: 'inline-grid',
                        gridTemplateColumns: 'auto auto auto'
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'flex-start'
                        }}
                    >
                        <ToggleButton
                            icon={<RectangleLandscape24Regular />}
                            title={`${this.props.drawDetections ? 'Hide' : 'Show'} Detections`}
                            style={{ marginRight: 2.5 }}
                            onClick={() => {
                                this.props.changeDrawDetections(!this.props.drawDetections);
                            }}
                        />
                        <ToggleButton
                            icon={<Shapes24Regular />}
                            title={`${this.props.drawRegionsOfInterest ? 'Hide' : 'Show'} Regions of Interest`}
                            onClick={() => {
                                this.props.changeDrawRegionsOfInterest(!this.props.drawRegionsOfInterest);
                            }}
                        />
                    </div>
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        <Button
                            icon={<Previous24Regular />}
                            title="Previous"
                            onClick={() => { this.props.previousAzdaData() }}
                        />
                        <Button
                            icon={this.props.playerMode === PlayerMode.Pause ? <Play24Regular /> : <Pause24Regular />}
                            title={this.props.playerMode === PlayerMode.Pause ? 'Press to Play' : 'Press to Pause'}
                            style={{
                                marginLeft: 2.5,
                                marginRight: 2.5
                            }}
                            onClick={() => {
                                this.props.changePlayerMode(this.props.playerMode === PlayerMode.Pause ? PlayerMode.Play : PlayerMode.Pause);
                            }}
                        />
                        <Button
                            icon={<Next24Regular />}
                            title="Next"
                            onClick={() => { this.props.nextAzdaData() }}
                        />
                    </div>
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'flex-end'
                        }}
                    >
                        <ToggleButton
                            icon={<Live24Regular />}
                            title={`${this.props.autoPlay ? 'Turn Off' : 'Turn On'} AutoPlay`}
                            style={{ marginRight: 2.5 }}
                            onClick={() => {
                                this.props.changeAutoPlay(!this.props.autoPlay);
                            }}
                        />
                        <Button
                            icon={<SelectObjectSkewEdit24Regular />}
                            title="Switch to Edit Mode"
                            style={{ marginRight: 2.5 }}
                            onClick={() => {
                                this.props.changeWidgetMode(WidgetMode.Edit);
                            }}
                        />
                    </div>
                </Card>
            </React.Fragment >
        );
    }
}
