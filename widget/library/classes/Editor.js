export class Editor {
    constructor(options) {
        this.data = {
            regionsOfInterest: options.regionsOfInterest
        };

        this.fps = 30;

        this.editInterval = null;
        this.editorOptions = options;

        this.selectedRegionOfInterestIndex = options.selectedRegionOfInterestIndex;
        this.selectedEdgeIndices = [-1, -1];
        this.selectedPointIndex = -1;
        this.selectedPointRadius = 0.025;

        this.editBy = options.editBy;

        this.mousePos = { x: 0, y: 0 };
        this.dragAnchorPoint = { x: 0, y: 0 };
        this.mouseInside = false;
        this.dragging = false;

        this.container = document.createElement('div');
        this.canvas = document.createElement('canvas');
    }

    initialize() {
        this.editInterval = setInterval(() => {
            this.draw(this.canvas.getContext("2d"));
        }, this.fps);
    }

    clearInterval() {
        if (this.editInterval !== undefined) {
            clearInterval(this.editInterval);
            this.editInterval = undefined;
        }
    }

    load() {
        this.loadContainer();
        this.loadCanvas();
        this.initialize();
    }

    loadContainer() {
        this.container.style.position = 'relative';
        this.container.style.zIndex = 12;
        this.container.onmouseover = this.handleMouseOver;
        this.container.onmouseout = this.handleMouseOut;
    }

    loadCanvas() {
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = 0;
        this.canvas.style.left = 0;
        this.canvas.width = this.editorOptions.size.width;
        this.canvas.height = this.editorOptions.size.height;
        this.canvas.style.border = "0px";
        this.canvas.tabIndex = -1;
        this.canvas.onkeyup = this.handleKeyUp;
        this.canvas.onclick = this.handleMouseClick;
        this.canvas.onmousedown = this.handleMouseDown;
        this.canvas.onmouseup = this.handleMouseUp;
        this.canvas.onmousemove = this.handleMouseMove;

        this.container.appendChild(this.canvas);
    }

    handleMouseOver = (e) => {
        this.canvas.focus();
        this.dragging = false;
        this.mouseInside = true;
        this.selectedPointIndex = -1;
        this.selectedEdgeIndices = [-1, -1];
    };

    handleMouseOut = (e) => {
        this.dragging = false;
        this.mouseInside = false;
        this.selectedPointIndex = -1;
        this.selectedEdgeIndices = [-1, -1];
    };

    handleKeyUp = (e) => {
        if (e.keyCode === 45 || e.keyCode === 187) {
            this.insertPoint();
        } else if (e.keyCode === 46 || e.keyCode === 189) {
            this.removePoint();
        } if (e.keyCode === 49 || e.keyCode === 97) {
            this.editBy = "Point";
        } else if (e.keyCode === 50 || e.keyCode === 98) {
            this.editBy = "Line";
        } else if (e.keyCode === 51 || e.keyCode === 99) {
            this.editBy = "Shape";
        }
    };

    handleMouseDown = (e) => {
        if (!this.dragging && this.selectedRegionOfInterestIndex.index !== -1) {
            const rect = this.canvas.getBoundingClientRect();
            const x = this.clamp((e.clientX - rect.left) / this.editorOptions.size.width, 0, 1);
            const y = this.clamp((e.clientY - rect.top) / this.editorOptions.size.height, 0, 1);

            this.dragAnchorPoint = { x: x, y: y };
        }
        this.dragging = true;
        this.updateMousePos(e);
    };

    handleMouseUp = (e) => {
        this.dragging = false;
    };

    handleMouseMove = (e) => {
        this.updateMousePos(e);
        if (this.editBy === "Point") {
            this.movePoint(e);
        } else if (this.editBy === "Line") {
            this.moveEdge(e);
        } else if (this.editBy === "Shape") {
            this.moveShape(e);
        }
    };

    handleMouseClick = (e) => {
        if (this.editBy === "Point") {
            this.addPoint(e);
        }
    };

    updateMousePos = (e) => {
        const rect = this.canvas.getBoundingClientRect();
        const x = this.clamp((e.clientX - rect.left) / this.editorOptions.size.width, 0, 1);
        const y = this.clamp((e.clientY - rect.top) / this.editorOptions.size.height, 0, 1);
        this.mousePos = { x: x, y: y };
    };

    // edit points
    addPoint = (e) => {
        if (this.selectedPointIndex === -1 && this.data.regionsOfInterest.length > 0) {
            const rect = this.canvas.getBoundingClientRect();
            const x = this.clamp((e.clientX - rect.left) / this.editorOptions.size.width, 0, 1);
            const y = this.clamp((e.clientY - rect.top) / this.editorOptions.size.height, 0, 1);
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.push([x, y]);
        }
    };

    insertPoint = () => {
        if (this.selectedRegionOfInterestIndex.index !== -1 &&
            this.selectedPointIndex !== -1 &&
            this.data.regionsOfInterest.length > 0 &&
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.length > 1) {
            const point = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[this.selectedPointIndex];
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.splice(this.selectedPointIndex, 0, [point[0], point[1]]);
            this.selectedPointIndex = -1;
        }
    };

    movePoint = (e) => {
        if (this.dragging &&
            this.selectedRegionOfInterestIndex.index !== -1 &&
            this.selectedPointIndex !== -1 &&
            this.data.regionsOfInterest.length > 0 &&
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.length > this.selectedPointIndex) {
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[this.selectedPointIndex] = [this.mousePos.x, this.mousePos.y];
        }
    };

    removePoint = () => {
        if (this.selectedRegionOfInterestIndex.index !== -1 &&
            this.selectedPointIndex !== -1 &&
            this.data.regionsOfInterest.length > 0 &&
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.length > this.selectedPointIndex) {
            this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.splice(this.selectedPointIndex, 1);
            this.selectedPointIndex = -1;
        }
    };

    findNearestPoint = (point) => {
        let nearestPointIndex = -1;
        let nearestPointDistance = -1;
        if (this.data.regionsOfInterest.length > 0) {
            const l = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.length;
            for (let i = 0; i < l; i++) {
                const p = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[i];
                const distance = Math.hypot(point.x - p[0], point.y - p[1]);
                if (distance <= nearestPointDistance || nearestPointDistance === -1) {
                    nearestPointDistance = distance;
                    nearestPointIndex = i;
                }
            }
        }
        return nearestPointDistance < this.selectedPointRadius ? nearestPointIndex : -1;
    };

    distanceFromPointToLineSegment = (point, start, end) => {
        let l2 = Math.pow(start.x - end.x, 2) + Math.pow(start.y - end.y, 2);
        if (l2 === 0) {
            return Math.pow(point.x - start.x, 2) + Math.pow(point.y - start.y, 2);
        }
        const t = Math.max(0, Math.min(1, ((point.x - start.x) * (end.x - start.x) + (point.y - start.y) * (end.y - start.y)) / l2));

        return Math.sqrt(Math.pow(point.x - (start.x + t * (end.x - start.x)), 2) + Math.pow(point.y - (start.y + t * (end.y - start.y)), 2));
    };

    findNearestEdge = (point) => {
        let edges = [];
        let selectedEdge = [-1, -1];
        if (this.data.regionsOfInterest.length > 0) {
            const roi = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index];
            const pl = roi.coordinates.length;
            if (pl > 1) {
                for (let p = 0; p < pl; p++) {
                    if (p < pl - 1) {
                        // first and inbetween            
                        const start = {
                            x: roi.coordinates[p][0],
                            y: roi.coordinates[p][1]
                        };
                        const end = {
                            x: roi.coordinates[p + 1][0],
                            y: roi.coordinates[p + 1][1]
                        };
                        edges.push({
                            indices: [p, p + 1],
                            distance: this.distanceFromPointToLineSegment(point, start, end)
                        });
                    } else {
                        // last         
                        const start = {
                            x: roi.coordinates[p][0],
                            y: roi.coordinates[p][1]
                        };
                        const end = {
                            x: roi.coordinates[0][0],
                            y: roi.coordinates[0][1]
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

    selectPoint = () => {
        if (this.selectedRegionOfInterestIndex.index !== -1) {
            const nearestPointIndex = this.findNearestPoint({ x: this.mousePos.x, y: this.mousePos.y });

            if (nearestPointIndex !== this.selectedPointIndex) {
                this.selectedPointIndex = nearestPointIndex;
            }
        }
    };

    // edit edge
    selectEdge = () => {
        if (this.selectedRegionOfInterestIndex.index !== -1) {
            const selectedEdgeIndices = this.findNearestEdge({ x: this.mousePos.x, y: this.mousePos.y });

            if (selectedEdgeIndices[0] !== this.selectedEdgeIndices[0] &&
                selectedEdgeIndices[1] !== this.selectedEdgeIndices[1]) {
                this.selectedEdgeIndices = selectedEdgeIndices;
            }
        }
    };

    moveEdge = (e) => {
        if (this.dragging && this.selectedRegionOfInterestIndex.index !== -1) {
            const distanceX = this.mousePos.x - this.dragAnchorPoint.x;
            const distanceY = this.mousePos.y - this.dragAnchorPoint.y;
            this.dragAnchorPoint.x = this.mousePos.x;
            this.dragAnchorPoint.y = this.mousePos.y;

            if (this.data.regionsOfInterest.length > 0) {
                const l = this.selectedEdgeIndices.length;
                for (let i = 0; i < l; i++) {
                    const index = this.selectedEdgeIndices[i];
                    const point = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[index];
                    point[0] = point[0] + distanceX;
                    point[1] = point[1] + distanceY;
                }
            }
        }
    };

    // edit shape
    moveShape = (e) => {
        if (this.dragging && this.selectedRegionOfInterestIndex.index !== -1) {
            const distanceX = this.mousePos.x - this.dragAnchorPoint.x;
            const distanceY = this.mousePos.y - this.dragAnchorPoint.y;
            this.dragAnchorPoint.x = this.mousePos.x;
            this.dragAnchorPoint.y = this.mousePos.y;

            if (this.data.regionsOfInterest.length > 0) {
                const l = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates.length;
                for (let i = 0; i < l; i++) {
                    const point = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[i];
                    point[0] = point[0] + distanceX;
                    point[1] = point[1] + distanceY;
                }
            }
        }
    };

    clamp = (value, min, max) => {
        return Math.min(Math.max(value, min), max);
    };

    // collision
    isPointInPolygon(point, polygon) {
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
            for (i, j; i < polygon.length; j = i++) {
                if ((polygon[i].y > point.y) !== (polygon[j].y > point.y) &&
                    point.x < (polygon[j].x - polygon[i].x) * (point.y - polygon[i].y) / (polygon[j].y - polygon[i].y) + polygon[i].x) {
                    isInside = !isInside;
                }
            }
        }

        return isInside;
    }

    // draw
    draw(context) {
        context.clearRect(0, 0, this.editorOptions.size.width, this.editorOptions.size.height);
        this.drawRegionsOfInterest(context);
        if (this.mouseInside) {
            if (this.editBy === "Point") {
                this.selectPoint();
                this.drawSelectedPoint(context);
            } else if (this.editBy === "Line") {
                this.selectEdge();
                this.drawSelectedEdge(context);
            } else if (this.editBy === "Shape") {
                if (this.selectedRegionOfInterestIndex.index !== -1 && this.data.regionsOfInterest.length > 0) {
                    const point = { x: this.mousePos.x, y: this.mousePos.y };
                    const roi = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index];
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

    drawRegionsOfInterest(context) {
        if (this.data.regionsOfInterest.length > 0) {
            const l = this.data.regionsOfInterest.length;
            for (let i = 0; i < l; i++) {
                const roi = this.data.regionsOfInterest[i];
                this.drawRegionOfInterest(context, roi, i);
            }
        }
    }

    drawRegionOfInterest(context, roi, index) {
        context.strokeStyle = roi.color;
        context.lineWidth = 3;

        const pl = roi.coordinates.length;
        for (let p = 0; p < pl; p++) {
            if (p > 0) {
                const start = {
                    x: this.editorOptions.size.width * roi.coordinates[p - 1][0],
                    y: this.editorOptions.size.height * roi.coordinates[p - 1][1]
                };
                const end = {
                    x: this.editorOptions.size.width * roi.coordinates[p][0],
                    y: this.editorOptions.size.height * roi.coordinates[p][1]
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
                x: this.editorOptions.size.width * roi.coordinates[0][0],
                y: this.editorOptions.size.height * roi.coordinates[0][1]
            };
            const last = {
                x: this.editorOptions.size.width * roi.coordinates[pl - 1][0],
                y: this.editorOptions.size.height * roi.coordinates[pl - 1][1]
            };
            if (this.selectedRegionOfInterestIndex.index === index && this.mouseInside && this.editBy === "Point") {
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
        if (this.selectedRegionOfInterestIndex.index === index && this.mouseInside && this.editBy === "Point") {
            for (let p = 0; p < pl; p++) {
                const point = {
                    x: this.editorOptions.size.width * roi.coordinates[p][0],
                    y: this.editorOptions.size.height * roi.coordinates[p][1]
                };
                context.setLineDash([]);
                context.beginPath();
                context.arc(point.x, point.y, 5, 0, 2 * Math.PI);
                context.closePath();
                context.stroke();
            }
        }
    }

    drawSelectedPoint = (context) => {
        if (this.selectedRegionOfInterestIndex.index !== -1 && this.data.regionsOfInterest.length > 0 && this.selectedPointIndex !== -1) {
            // TODO: change color
            context.strokeStyle = 'yellow';
            context.lineWidth = 3;

            const point = {
                x: this.editorOptions.size.width * this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[this.selectedPointIndex][0],
                y: this.editorOptions.size.height * this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index].coordinates[this.selectedPointIndex][1]
            };
            context.beginPath();
            context.arc(point.x, point.y, 5, 0, 2 * Math.PI);
            context.stroke();
        }
    };

    drawSelectedEdge = (context) => {
        if (this.selectedRegionOfInterestIndex.index !== -1 && this.data.regionsOfInterest.length > 0 && this.selectedEdgeIndices[0] !== -1) {
            // TODO: change color
            context.strokeStyle = 'yellow';
            context.lineWidth = 3;

            const roi = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index];

            const index1 = this.selectedEdgeIndices[0];
            const index2 = this.selectedEdgeIndices[1];

            const start = {
                x: this.editorOptions.size.width * roi.coordinates[index1][0],
                y: this.editorOptions.size.height * roi.coordinates[index1][1]
            };
            const end = {
                x: this.editorOptions.size.width * roi.coordinates[index2][0],
                y: this.editorOptions.size.height * roi.coordinates[index2][1]
            };
            context.setLineDash([]);
            context.beginPath();
            context.moveTo(start.x, start.y);
            context.lineTo(end.x, end.y);
            context.closePath();
            context.stroke();
        }
    };

    drawSelectedShape = (context) => {
        if (this.selectedRegionOfInterestIndex.index !== -1 && this.data.regionsOfInterest.length > 0) {
            // TODO: change color
            context.strokeStyle = 'yellow';
            context.lineWidth = 3;

            const roi = this.data.regionsOfInterest[this.selectedRegionOfInterestIndex.index];
            const pl = roi.coordinates.length;
            for (let p = 0; p < pl; p++) {
                if (p > 0) {
                    const start = {
                        x: this.editorOptions.size.width * roi.coordinates[p - 1][0],
                        y: this.editorOptions.size.height * roi.coordinates[p - 1][1]
                    };
                    const end = {
                        x: this.editorOptions.size.width * roi.coordinates[p][0],
                        y: this.editorOptions.size.height * roi.coordinates[p][1]
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
                    x: this.editorOptions.size.width * roi.coordinates[0][0],
                    y: this.editorOptions.size.height * roi.coordinates[0][1]
                };
                const last = {
                    x: this.editorOptions.size.width * roi.coordinates[pl - 1][0],
                    y: this.editorOptions.size.height * roi.coordinates[pl - 1][1]
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
