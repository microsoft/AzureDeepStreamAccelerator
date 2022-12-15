import * as React from 'react';

import { Card } from '@fluentui/react-components/unstable';
import { Button } from "@fluentui/react-components";
import { CheckboxUnchecked24Filled, Shapes24Regular, FullScreenMaximize24Regular, Video24Regular, Previous24Regular, Next24Regular, Play24Regular, Pause24Regular } from "@fluentui/react-icons";
import { PlayerMode } from '../../enums/PlayerMode';
import { WidgetMode } from '../../enums/WidgetMode';
import { AzdaData } from '../../types/AzdaData';
import { Detection } from '../../types/Detection';
import { RegionOfInterest } from '../../types/RegionOfInterest';

export interface IPlayerProps {
    width: number;
    height: number;
    playerMode: PlayerMode;
    autoPlay: boolean;
    nextVideoUrl: string;
    widgetMode: WidgetMode;
    azdaData: AzdaData;
    drawDetections: boolean;
    drawRegionsOfInterest: boolean;

    changePlayerMode: (playerMode: PlayerMode) => void;
    nextAzdaData: () => void;

    drawDetection?: (context: CanvasRenderingContext2D, detection: Detection) => void;
    drawRegionOfInterest?: (context: CanvasRenderingContext2D, regionOfInterest: RegionOfInterest) => void;
}

export interface IPlayerState {

}

export default class Player extends React.Component<IPlayerProps, IPlayerState> {
    private canvasRef: React.RefObject<any> = React.createRef();
    private video: any = document.createElement('video');
    private nextVideo: any = document.createElement('video');
    private videoCurrentTime: number = 0;
    private videoProgressPercent: number = 0;
    private currentInferenceIndex: number = 0;
    private updateFramesPerSecond: number = 1000 / 30;
    private updateInterval: NodeJS.Timeout | undefined;

    constructor(props: IPlayerProps) {
        super(props);

        this.state = {

        }

        this.video.onloadstart = () => {
            this.reset();
        }

        this.video.onloadeddata = () => {
            this.setup();
        }
    }

    componentDidUpdate(prevProps: IPlayerProps) {
        if (prevProps.azdaData !== this.props.azdaData) {
            const context = this.canvasRef.current.getContext("2d");
            if(!this.props.autoPlay) {
                context.clearRect(0, 0, this.props.width, this.props.height + 5);
            }
            if (this.props.azdaData) {
                if(this.nextVideo.src !== '' && this.nextVideo.src === this.props.azdaData.videoUrl) {
                    this.video = this.nextVideo;
                    this.nextVideo = document.createElement('video');
                } else {
                    this.video.src = this.props.azdaData.videoUrl;
                }
                this.nextVideo.src = this.props.nextVideoUrl;
            }
        }
        if (
            prevProps.widgetMode !== this.props.widgetMode ||
            prevProps.drawDetections !== this.props.drawDetections ||
            prevProps.drawRegionsOfInterest !== this.props.drawRegionsOfInterest
        ) {
            if (this.props.azdaData) {
                this.pauseFrame();
            }
        }
    }

    componentWillUnmount() {
        this.reset();
    }

    public render() {
        return (
            <React.Fragment>
                <Card
                    style={{
                        width: this.props.width,
                        height: this.props.height
                    }}
                >
                    <canvas
                        ref={this.canvasRef}
                        width={this.props.width}
                        height={this.props.height + 10}
                        onClick={this.setInferenceIndex}
                    >
                    </canvas>
                </Card>
            </React.Fragment >
        );
    }

    // TODO: pausing makes it move ahead a bit, fix that
    pauseFrame = (): void => {
        this.props.changePlayerMode(PlayerMode.Pause);
        this.updateFrame();
    }

    updateFrame = (): void => {
        if (this.props.azdaData) {
            this.videoCurrentTime = this.currentInferenceIndex * this.updateFramesPerSecond;
            this.videoProgressPercent = this.currentInferenceIndex / this.props.azdaData.azdaOutput.inferences.length;
            this.video.play(this.videoCurrentTime);
            const context = this.canvasRef.current.getContext("2d");
            this.draw(context, this.props.azdaData.azdaOutput.inferences[this.currentInferenceIndex].detections, this.props.azdaData.azdaOutput.regionsOfInterest);
        }
    }

    setInferenceIndex = (e: React.MouseEvent<HTMLCanvasElement, MouseEvent>): void => {
        if (this.canvasRef.current) {
            const rect = this.canvasRef.current.getBoundingClientRect();
            const x = Math.min(Math.max((e.clientX - rect.left) / this.props.width, 0), 1);
            const y = Math.min(Math.max((e.clientY - rect.top) / this.props.height, 0), 1);
            if (this.props.azdaData && this.props.azdaData.azdaOutput.inferences.length > 0) {
                if (y >= 0.9) {
                    this.currentInferenceIndex = Math.round(this.props.azdaData.azdaOutput.inferences.length * x);
                    this.pauseFrame();
                } else {
                    this.props.changePlayerMode(this.props.playerMode === PlayerMode.Play ? PlayerMode.Pause : PlayerMode.Play);
                }
            }
        }
    }

    setup() {
        if (
            this.props.azdaData &&
            this.props.azdaData.azdaOutput.inferences.length > 0 &&
            this.updateInterval === undefined
        ) {
            this.updateFramesPerSecond = this.video.duration * 1000 / this.props.azdaData.azdaOutput.inferences.length;
            this.updateInterval = setInterval(() => {
                if (
                    this.props.azdaData &&
                    this.props.azdaData.azdaOutput.inferences.length > 0 &&
                    this.props.playerMode === PlayerMode.Play
                ) {
                    if (this.currentInferenceIndex < this.props.azdaData.azdaOutput.inferences.length) {
                        // draw
                        this.video.play(this.videoCurrentTime);
                        const context = this.canvasRef.current.getContext("2d");
                        this.draw(context, this.props.azdaData.azdaOutput.inferences[this.currentInferenceIndex].detections, this.props.azdaData.azdaOutput.regionsOfInterest);
                        // update for next draw
                        this.currentInferenceIndex++;
                        this.videoCurrentTime += this.updateFramesPerSecond;
                        this.videoProgressPercent = this.currentInferenceIndex / this.props.azdaData.azdaOutput.inferences.length;
                    } else {
                        this.videoCurrentTime = 0;
                        this.currentInferenceIndex = 0;
                        this.videoProgressPercent = 0;
                        this.props.changePlayerMode(PlayerMode.Pause);
                        if(this.props.autoPlay) {
                            this.props.nextAzdaData();
                        }
                    }
                }
            }, this.updateFramesPerSecond);
        }
    }

    reset() {
        if (this.updateInterval !== undefined) {
            clearInterval(this.updateInterval);
            this.updateInterval = undefined;
        }
        this.videoCurrentTime = 0;
        this.currentInferenceIndex = 0;
        this.videoProgressPercent = 0;
    }

    private draw(context: CanvasRenderingContext2D, detections: Detection[], regionsOfInterest: RegionOfInterest[]) {
        if(!this.props.autoPlay) {
            context.clearRect(0, 0, this.props.width, this.props.height + 5);
        } else {
            context.clearRect(0, this.props.height, this.props.width, this.props.height + 5);
        }
        this.drawVideoFrame(context);
        if (this.props.drawRegionsOfInterest && this.props.widgetMode === WidgetMode.Play) {
            this.drawRegionsOfInterest(context, regionsOfInterest);
        }
        if (this.props.drawDetections && this.props.widgetMode === WidgetMode.Play) {
            this.drawDetections(context, detections);
        }
        this.drawVideoProgressPercent(context);
    }

    private drawVideoProgressPercent(context: CanvasRenderingContext2D) {
        context.strokeStyle = "#adadad";
        context.lineWidth = 3.5;
        context.setLineDash([]);
        context.beginPath();
        context.moveTo(-10, this.props.height + 2.5);
        context.lineTo(this.props.width * this.videoProgressPercent + 10, this.props.height + 2.5);
        context.closePath();
        context.stroke();
    }

    private drawVideoFrame(context: CanvasRenderingContext2D) {
        const video = this.video;
        if (video) {
            context.drawImage(this.video, 0, 0, this.props.width, this.props.height);
        }
    }

    private drawDetections(context: CanvasRenderingContext2D, detections: Detection[]) {
        const l = detections.length;
        for (let i = 0; i < l; i++) {
            const detection: Detection = detections[i];
            this.drawDetection(context, detection);
        }
    }

    private drawDetection(context: CanvasRenderingContext2D, detection: Detection) {
        if (this.props.drawDetection !== undefined && this.props.drawDetection) {
            this.props.drawDetection(context, detection);
        } else {
            const box = {
                l: detection.rect[0] * this.props.width,
                t: detection.rect[1] * this.props.height,
                w: detection.rect[2] * this.props.width,
                h: detection.rect[3] * this.props.height
            }

            context.font = '13px Segoe UI';
            context.strokeStyle = '#106ebe';
            context.lineWidth = 1;
            context.strokeText(`${detection.label} ${(+detection.confidence * 100).toFixed(0)}%`, box.l, box.t - 8);
            context.fillStyle = '#fff';
            context.fillText(`${detection.label} ${(+detection.confidence * 100).toFixed(0)}%`, box.l, box.t - 8);

            context.beginPath();
            context.moveTo(box.l + box.w / 2, box.t);
            context.arcTo(
                box.l + box.w,
                box.t,
                box.l + box.w,
                box.t + box.h,
                6.5
            );
            context.arcTo(
                box.l + box.w,
                box.t + box.h,
                box.l,
                box.t + box.h,
                6.5
            );
            context.arcTo(
                box.l,
                box.t + box.h,
                box.l,
                box.t,
                6.5
            );
            context.arcTo(
                box.l,
                box.t,
                box.l + box.w,
                box.t,
                6.5
            );
            context.arcTo(
                box.l + box.w,
                box.t,
                box.l + box.w,
                box.t + box.h,
                6.5
            );
            context.strokeStyle = '#106ebe';
            context.lineWidth = 3.5;
            context.stroke();
            context.strokeStyle = '#fff';
            context.lineWidth = 2.5;
            context.stroke();
        }
    }

    private drawRegionsOfInterest(context: CanvasRenderingContext2D, regionsOfInterest: RegionOfInterest[]) {
        const l = regionsOfInterest.length;
        for (let i = 0; i < l; i++) {
            const regionOfInterest: RegionOfInterest = regionsOfInterest[i];
            this.drawRegionOfInterest(context, regionOfInterest);
        }
    }

    private drawRegionOfInterest(context: CanvasRenderingContext2D, regionOfInterest: RegionOfInterest) {
        if (this.props.drawRegionOfInterest !== undefined && this.props.drawRegionOfInterest) {
            this.props.drawRegionOfInterest(context, regionOfInterest);
        } else {
            context.strokeStyle = regionOfInterest.color;
            context.lineWidth = 3;

            const pl = regionOfInterest.coordinates.length;
            for (let p = 0; p < pl; p++) {
                if (p > 0) {
                    const start = {
                        x: this.props.width * regionOfInterest.coordinates[p - 1][0],
                        y: this.props.height * regionOfInterest.coordinates[p - 1][1]
                    };
                    const end = {
                        x: this.props.width * regionOfInterest.coordinates[p][0],
                        y: this.props.height * regionOfInterest.coordinates[p][1]
                    };
                    context.setLineDash([]);
                    context.beginPath();
                    context.moveTo(start.x, start.y);
                    context.lineTo(end.x, end.y);
                    context.closePath();
                    context.stroke();
                }
            }
            if (pl > 2) {
                const first = {
                    x: this.props.width * regionOfInterest.coordinates[pl - pl][0],
                    y: this.props.height * regionOfInterest.coordinates[pl - pl][1]
                };
                const last = {
                    x: this.props.width * regionOfInterest.coordinates[pl - 1][0],
                    y: this.props.height * regionOfInterest.coordinates[pl - 1][1]
                };
                context.setLineDash([]);
                context.beginPath();
                context.moveTo(last.x, last.y);
                context.lineTo(first.x, first.y);
                context.closePath();
                context.stroke();
            }
        }
    }
}
