import * as React from 'react';
import { EditorMode } from '../../enums/EditorMode';
import { Point } from '../../types/Point';
import { RegionOfInterest } from '../../types/RegionOfInterest';

export interface IEditorProps {
    regionsOfInterest: RegionOfInterest[];
    regionOfInterest: RegionOfInterest;
    width: number;
    height: number;
    editorMode: EditorMode;
    changeEditorMode: (editorMode: EditorMode) => void;
}

export interface IEditorState {
}

export default class Editor extends React.Component<IEditorProps, IEditorState> {
    private canvasRef: React.RefObject<any> = React.createRef();
    private updateInterval: NodeJS.Timeout | undefined;
    private selectedEdgeIndices: number[];
    private selectedPointIndex: number;
    private selectedPointRadius: number;
    private selectedColor: string;
    private mousePos: Point;
    private dragAnchorPoint: Point;
    private mouseInside: boolean;
    private dragging: boolean;

    constructor(props: IEditorProps) {
        super(props);

        this.state = {
        }

        this.selectedEdgeIndices = [-1, -1];
        this.selectedPointIndex = -1;
        this.selectedPointRadius = 0.025;
        this.selectedColor = "yellow";
        this.mousePos = { x: 0, y: 0 };
        this.dragAnchorPoint = { x: 0, y: 0 };
    }

    componentDidMount(): void {
        this.updateInterval = setInterval(() => {
            const context = this.canvasRef.current.getContext("2d");
            this.draw(context);
        }, 1000 / 30)
    }

    componentWillUnmount(): void {
        if (this.updateInterval !== undefined) {
            clearInterval(this.updateInterval);
            this.updateInterval = undefined;
        }
    }

    public render() {
        return (
            <React.Fragment>
                <div
                    style={{
                        position: 'relative',
                        zIndex: 12
                    }}
                    onMouseOver={this.onMouseOver}
                    onMouseOut={this.onMouseOut}
                >
                <canvas 
                    ref={this.canvasRef}
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        borderWidth: 0
                    }}
                    tabIndex={-1}
                    width={this.props.width}
                    height={this.props.height}
                    onKeyUp={this.onKeyUp}
                    onClick={this.onClick}
                    onMouseDown={this.onMouseDown}
                    onMouseUp={this.onMouseUp}
                    onMouseMove={this.onMouseMove}
                >
                </canvas>
                </div>
            </React.Fragment>
        );
    }

    // handle events
    onMouseOver = (e: any): void => {
        if(this.canvasRef.current) {
            this.canvasRef.current.focus();
        }
        this.dragging = false;
        this.mouseInside = true;
        this.selectedPointIndex = -1;
        this.selectedEdgeIndices = [-1, -1];
    };

    onMouseOut = (e: any): void => {
        this.dragging = false;
        this.mouseInside = false;
        this.selectedPointIndex = -1;
        this.selectedEdgeIndices = [-1, -1];
    };

    onKeyUp = (e: any): void => {
        if (e.keyCode === 45 || e.keyCode === 187) {
            this.insertPoint();
        } else if (e.keyCode === 46 || e.keyCode === 189) {
            this.removePoint();
        } if (e.keyCode === 49 || e.keyCode === 97) {
            this.props.changeEditorMode(EditorMode.Point);
        } else if (e.keyCode === 50 || e.keyCode === 98) {
            this.props.changeEditorMode(EditorMode.Line);
        } else if (e.keyCode === 51 || e.keyCode === 99) {
            this.props.changeEditorMode(EditorMode.Shape);
        }
    };

    onMouseDown = (e: any): void => {
        if (!this.dragging && this.props.regionOfInterest) {
            if(this.canvasRef.current) {
                const rect = this.canvasRef.current.getBoundingClientRect();
                const x = this.clamp((e.clientX - rect.left) / this.props.width, 0, 1);
                const y = this.clamp((e.clientY - rect.top) / this.props.height, 0, 1);
    
                this.dragAnchorPoint = { x: x, y: y };
            }
        }
        this.dragging = true;
        this.updateMousePos(e);
    };

    onMouseUp = (e: any): void => {
        this.dragging = false;
    };

    onMouseMove = (e: any): void => {
        this.updateMousePos(e);
        if (this.props.editorMode === EditorMode.Point) {
            this.movePoint(e);
        } else if (this.props.editorMode === EditorMode.Line) {
            this.moveEdge(e);
        } else if (this.props.editorMode === EditorMode.Shape) {
            this.moveShape(e);
        }
    };

    onClick = (e: any): void => {
        if (this.props.editorMode === EditorMode.Point) {
            this.addPoint(e);
        }
    };

    updateMousePos = (e: any): void => {
        if(this.canvasRef.current) {
            const rect = this.canvasRef.current.getBoundingClientRect();
            const x = this.clamp((e.clientX - rect.left) / this.props.width, 0, 1);
            const y = this.clamp((e.clientY - rect.top) / this.props.height, 0, 1);
            this.mousePos = { x: x, y: y };
        }
    };

    // edit points
    addPoint = (e: any): void => {
        if (
            this.selectedPointIndex === -1 && 
            this.props.regionsOfInterest.length > 0 &&
            this.canvasRef.current
        ) {
            const rect = this.canvasRef.current.getBoundingClientRect();
            const x = this.clamp((e.clientX - rect.left) / this.props.width, 0, 1);
            const y = this.clamp((e.clientY - rect.top) / this.props.height, 0, 1);
            this.props.regionOfInterest.coordinates.push([x, y]);
        }
    };

    insertPoint = (): void => {
        if (this.props.regionOfInterest &&
            this.selectedPointIndex !== -1 &&
            this.props.regionsOfInterest.length > 0 &&
            this.props.regionOfInterest.coordinates.length > 1) {
            const point = this.props.regionOfInterest.coordinates[this.selectedPointIndex];
            this.props.regionOfInterest.coordinates.splice(this.selectedPointIndex, 0, [point[0], point[1]]);
            this.selectedPointIndex = -1;
        }
    };

    movePoint = (e: any): void => {
        if (this.dragging &&
            this.props.regionOfInterest &&
            this.selectedPointIndex !== -1 &&
            this.props.regionsOfInterest.length > 0 &&
            this.props.regionOfInterest.coordinates.length > this.selectedPointIndex) {
            this.props.regionOfInterest.coordinates[this.selectedPointIndex] = [this.mousePos.x, this.mousePos.y];
        }
    };

    removePoint = (): void => {
        if (this.props.regionOfInterest &&
            this.selectedPointIndex !== -1 &&
            this.props.regionsOfInterest.length > 0 &&
            this.props.regionOfInterest.coordinates.length > this.selectedPointIndex) {
            this.props.regionOfInterest.coordinates.splice(this.selectedPointIndex, 1);
            this.selectedPointIndex = -1;
        }
    };

    findNearestPoint = (point: Point): number => {
        let nearestPointIndex = -1;
        let nearestPointDistance = -1;
        if (this.props.regionsOfInterest.length > 0) {
            const l = this.props.regionOfInterest.coordinates.length;
            for (let i = 0; i < l; i++) {
                const p = this.props.regionOfInterest.coordinates[i];
                const distance = Math.hypot(point.x - p[0], point.y - p[1]);
                if (distance <= nearestPointDistance || nearestPointDistance === -1) {
                    nearestPointDistance = distance;
                    nearestPointIndex = i;
                }
            }
        }
        return nearestPointDistance < this.selectedPointRadius ? nearestPointIndex : -1;
    };

    distanceFromPointToLineSegment = (point: Point, start: Point, end: Point): number => {
        let l2 = Math.pow(start.x - end.x, 2) + Math.pow(start.y - end.y, 2);
        if (l2 === 0) {
            return Math.pow(point.x - start.x, 2) + Math.pow(point.y - start.y, 2);
        }
        const t = Math.max(0, Math.min(1, ((point.x - start.x) * (end.x - start.x) + (point.y - start.y) * (end.y - start.y)) / l2));

        return Math.sqrt(Math.pow(point.x - (start.x + t * (end.x - start.x)), 2) + Math.pow(point.y - (start.y + t * (end.y - start.y)), 2));
    };

    findNearestEdge = (point: Point): number[] => {
        let edges = [];
        let selectedEdge = [-1, -1];
        if (this.props.regionsOfInterest.length > 0) {
            const regionOfInterest = this.props.regionOfInterest;
            const pl = regionOfInterest.coordinates.length;
            if (pl > 1) {
                for (let p = 0; p < pl; p++) {
                    if (p < pl - 1) {
                        // first and inbetween            
                        const start = {
                            x: regionOfInterest.coordinates[p][0],
                            y: regionOfInterest.coordinates[p][1]
                        };
                        const end = {
                            x: regionOfInterest.coordinates[p + 1][0],
                            y: regionOfInterest.coordinates[p + 1][1]
                        };
                        edges.push({
                            indices: [p, p + 1],
                            distance: this.distanceFromPointToLineSegment(point, start, end)
                        });
                    } else {
                        // last         
                        const start = {
                            x: regionOfInterest.coordinates[p][0],
                            y: regionOfInterest.coordinates[p][1]
                        };
                        const end = {
                            x: regionOfInterest.coordinates[0][0],
                            y: regionOfInterest.coordinates[0][1]
                        };
                        edges.push({
                            indices: [p, 0],
                            distance: this.distanceFromPointToLineSegment(point, start, end)
                        });
                    }
                }
                edges = edges.sort((a, b) => {
                    return a.distance > b.distance ? 1 : -1;
                });

                if (edges.length > 0 && edges[0].distance < 0.05) {
                    selectedEdge = edges[0].indices;
                }
            }
        }

        return selectedEdge;
    };

    selectPoint = (): void => {
        if (this.props.regionOfInterest) {
            const nearestPointIndex = this.findNearestPoint({ x: this.mousePos.x, y: this.mousePos.y });

            if (nearestPointIndex !== this.selectedPointIndex) {
                this.selectedPointIndex = nearestPointIndex;
            }
        }
    };

    // edit edge
    selectEdge = (): void => {
        if (this.props.regionOfInterest) {
            const selectedEdgeIndices = this.findNearestEdge({ x: this.mousePos.x, y: this.mousePos.y });

            if (selectedEdgeIndices[0] !== this.selectedEdgeIndices[0] &&
                selectedEdgeIndices[1] !== this.selectedEdgeIndices[1]) {
                this.selectedEdgeIndices = selectedEdgeIndices;
            }
        }
    };

    moveEdge = (e: any): void => {
        if (this.dragging && this.props.regionOfInterest) {
            const distanceX = this.mousePos.x - this.dragAnchorPoint.x;
            const distanceY = this.mousePos.y - this.dragAnchorPoint.y;
            this.dragAnchorPoint.x = this.mousePos.x;
            this.dragAnchorPoint.y = this.mousePos.y;

            if (this.props.regionsOfInterest.length > 0) {
                const l = this.selectedEdgeIndices.length;
                for (let i = 0; i < l; i++) {
                    const index = this.selectedEdgeIndices[i];
                    const point = this.props.regionOfInterest.coordinates[index];
                    point[0] = point[0] + distanceX;
                    point[1] = point[1] + distanceY;
                }
            }
        }
    };

    // edit shape
    moveShape = (e: any): void => {
        if (this.dragging && this.props.regionOfInterest) {
            const distanceX = this.mousePos.x - this.dragAnchorPoint.x;
            const distanceY = this.mousePos.y - this.dragAnchorPoint.y;
            this.dragAnchorPoint.x = this.mousePos.x;
            this.dragAnchorPoint.y = this.mousePos.y;

            if (this.props.regionsOfInterest.length > 0) {
                const l = this.props.regionOfInterest.coordinates.length;
                for (let i = 0; i < l; i++) {
                    const point = this.props.regionOfInterest.coordinates[i];
                    point[0] = point[0] + distanceX;
                    point[1] = point[1] + distanceY;
                }
            }
        }
    };

    clamp = (value: number, min: number, max: number): number => {
        return Math.min(Math.max(value, min), max);
    };

    // collision detection
    isPointInPolygon(point: Point, polygon: Point[]): boolean {
        let isInside = false;
        if (polygon.length > 0) {
            let minX = polygon[0].x;
            let maxX = polygon[0].x;
            let minY = polygon[0].y;
            let maxY = polygon[0].y;
            for (let n = 1; n < polygon.length; n++) {
                const q = polygon[n];
                minX = Math.min(q.x, minX);
                maxX = Math.max(q.x, maxX);
                minY = Math.min(q.y, minY);
                maxY = Math.max(q.y, maxY);
            }

            if (point.x < minX || point.x > maxX || point.y < minY || point.y > maxY) {
                return false;
            }

            let i = 0, j = polygon.length - 1;
            for (i = 0, j; i < polygon.length; j = i++) {
                if ((polygon[i].y > point.y) !== (polygon[j].y > point.y) &&
                    point.x < (polygon[j].x - polygon[i].x) * (point.y - polygon[i].y) / (polygon[j].y - polygon[i].y) + polygon[i].x) {
                    isInside = !isInside;
                }
            }
        }

        return isInside;
    }

    // draw
    draw(context: CanvasRenderingContext2D): void {
        context.clearRect(0, 0, this.props.width, this.props.height);
        this.drawRegionsOfInterest(context);
        if (this.mouseInside) {
            if (this.props.editorMode === EditorMode.Point) {
                this.selectPoint();
                this.drawSelectedPoint(context);
            } else if (this.props.editorMode === EditorMode.Line) {
                this.selectEdge();
                this.drawSelectedEdge(context);
            } else if (this.props.editorMode === EditorMode.Shape) {
                if (this.props.regionOfInterest && this.props.regionsOfInterest.length > 0) {
                    const point = { x: this.mousePos.x, y: this.mousePos.y };
                    const roi = this.props.regionOfInterest;
                    const coordinates = [];
                    let l = roi.coordinates.length;
                    if (l > 0) {
                        for (let i = 0; i < l; i++) {
                            coordinates.push({ x: roi.coordinates[i][0], y: roi.coordinates[i][1] });
                        }
                    }
                    if (this.isPointInPolygon(point, coordinates)) {
                        this.drawSelectedShape(context);
                    }
                }
            }
        }
    }

    drawRegionsOfInterest(context: CanvasRenderingContext2D): void {
        if (this.props.regionsOfInterest.length > 0) {
            const l = this.props.regionsOfInterest.length;
            for (let i = 0; i < l; i++) {
                const regionOfInterest = this.props.regionsOfInterest[i];
                this.drawRegionOfInterest(context, regionOfInterest);
            }
        }
    }

    drawRegionOfInterest(context: CanvasRenderingContext2D, regionOfInterest: RegionOfInterest): void {
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
                x: this.props.width * regionOfInterest.coordinates[0][0],
                y: this.props.height * regionOfInterest.coordinates[0][1]
            };
            const last = {
                x: this.props.width * regionOfInterest.coordinates[pl - 1][0],
                y: this.props.height * regionOfInterest.coordinates[pl - 1][1]
            };
            if (this.props.regionOfInterest === regionOfInterest && this.mouseInside && this.props.editorMode === EditorMode.Point) {
                context.setLineDash([3, 5]);
            } else {
                context.setLineDash([]);
            }
            context.beginPath();
            context.moveTo(last.x, last.y);
            context.lineTo(first.x, first.y);
            context.closePath();
            context.stroke();
        }
        if (this.props.regionOfInterest === regionOfInterest && this.mouseInside && this.props.editorMode === EditorMode.Point) {
            for (let p = 0; p < pl; p++) {
                const point = {
                    x: this.props.width * regionOfInterest.coordinates[p][0],
                    y: this.props.height * regionOfInterest.coordinates[p][1]
                };
                context.setLineDash([]);
                context.beginPath();
                context.arc(point.x, point.y, 5, 0, 2 * Math.PI);
                context.closePath();
                context.stroke();
            }
        }
    }

    drawSelectedPoint = (context: CanvasRenderingContext2D): void => {
        if (this.props.regionOfInterest && this.props.regionsOfInterest.length > 0 && this.selectedPointIndex !== -1) {
            context.strokeStyle = this.selectedColor;
            context.lineWidth = 3;

            const point = {
                x: this.props.width * this.props.regionOfInterest.coordinates[this.selectedPointIndex][0],
                y: this.props.height * this.props.regionOfInterest.coordinates[this.selectedPointIndex][1]
            };
            context.beginPath();
            context.arc(point.x, point.y, 5, 0, 2 * Math.PI);
            context.stroke();
        }
    };

    drawSelectedEdge = (context: CanvasRenderingContext2D): void => {
        if (this.props.regionOfInterest && this.props.regionsOfInterest.length > 0 && this.selectedEdgeIndices[0] !== -1) {
            context.strokeStyle = this.selectedColor;
            context.lineWidth = 3;

            const roi = this.props.regionOfInterest;

            const index1 = this.selectedEdgeIndices[0];
            const index2 = this.selectedEdgeIndices[1];

            const start = {
                x: this.props.width * roi.coordinates[index1][0],
                y: this.props.height * roi.coordinates[index1][1]
            };
            const end = {
                x: this.props.width * roi.coordinates[index2][0],
                y: this.props.height * roi.coordinates[index2][1]
            };
            context.setLineDash([]);
            context.beginPath();
            context.moveTo(start.x, start.y);
            context.lineTo(end.x, end.y);
            context.closePath();
            context.stroke();
        }
    };

    drawSelectedShape = (context: CanvasRenderingContext2D): void => {
        if (this.props.regionOfInterest && this.props.regionsOfInterest.length > 0) {
            context.strokeStyle = this.selectedColor;
            context.lineWidth = 3;

            const roi = this.props.regionOfInterest;
            const pl = roi.coordinates.length;
            for (let p = 0; p < pl; p++) {
                if (p > 0) {
                    const start = {
                        x: this.props.width * roi.coordinates[p - 1][0],
                        y: this.props.height * roi.coordinates[p - 1][1]
                    };
                    const end = {
                        x: this.props.width * roi.coordinates[p][0],
                        y: this.props.height * roi.coordinates[p][1]
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
                    x: this.props.width * roi.coordinates[0][0],
                    y: this.props.height * roi.coordinates[0][1]
                };
                const last = {
                    x: this.props.width * roi.coordinates[pl - 1][0],
                    y: this.props.height * roi.coordinates[pl - 1][1]
                };
                context.setLineDash([]);
                context.beginPath();
                context.moveTo(last.x, last.y);
                context.lineTo(first.x, first.y);
                context.closePath();
                context.stroke();
            }
        }
    };
}
