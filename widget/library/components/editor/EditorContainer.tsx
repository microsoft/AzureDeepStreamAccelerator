import * as React from 'react';
import { WidgetMode } from '../../enums/WidgetMode';
import { EditorMode } from '../../enums/EditorMode';
import EditorToolbar from './EditorToolbar';
import EditorTable from './EditorTable';
import { RegionOfInterest } from '../../types/RegionOfInterest';
import { IRegionOfInterestService } from '../../interfaces/IRegionOfInterestService';
import Editor from './Editor';
import EditorDetail from './EditorDetail';

export interface IEditorContainerProps {
    regionOfInterestService: IRegionOfInterestService;
    width: number;
    height: number;
    widgetMode: WidgetMode;

    changeWidgetMode: (widgetMode: WidgetMode) => void;
}

export interface IEditorContainerState {
    editorMode: EditorMode;
    regionsOfInterest: RegionOfInterest[];
    regionOfInterest: RegionOfInterest | null;
}

export default class EditorContainer extends React.Component<IEditorContainerProps, IEditorContainerState> {
    constructor(props: IEditorContainerProps) {
        super(props);

        this.state = {
            editorMode: EditorMode.Point,
            regionsOfInterest: [],
            regionOfInterest: null
        }
    }

    componentDidMount(): void {
        this.getRegionsOfInterest(this);
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
                            padding: 0,
                            width: this.props.width,
                            height: this.props.height
                        }}
                    >
                        <Editor
                            regionsOfInterest={this.state.regionsOfInterest}
                            regionOfInterest={this.state.regionOfInterest}
                            width={this.props.width}
                            height={this.props.height}
                            editorMode={this.state.editorMode}
                            changeEditorMode={this.changeEditorMode}
                        />
                    </div>
                    {
                        this.props.widgetMode === WidgetMode.Edit ? (
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
                                    <EditorToolbar
                                        width={this.props.width}
                                        editorMode={this.state.editorMode}
                                        changeWidgetMode={this.props.changeWidgetMode}
                                        changeEditorMode={this.changeEditorMode}
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
                                    <EditorTable
                                        regionsOfInterest={this.state.regionsOfInterest}
                                        regionOfInterest={this.state.regionOfInterest}
                                        changeRegionOfInterest={this.changeRegionOfInterest}
                                        updateRegionsOfInterest={this.updateRegionsOfInterest}
                                        addRegionOfInterest={this.addRegionOfInterest}
                                        removeRegionOfInterest={this.removeRegionOfInterest}
                                    />
                                </div>
                            </React.Fragment>
                        ) : null
                    }
                </div>
            </React.Fragment >
        );
    }

    async getRegionsOfInterest(editorContainer: EditorContainer) {
        const regionsOfInterest = await this.props.regionOfInterestService.get();
        editorContainer.setState({
            regionsOfInterest: regionsOfInterest,
            regionOfInterest: regionsOfInterest.length > 0 ? regionsOfInterest[0] : null
        });
    }

    updateRegionsOfInterest = (
        regionsOfInterest: RegionOfInterest[],
        editorTable: EditorTable,
        callback: (editorTable: EditorTable) => void
    ) => {
        this.updateRegionsOfInterestAsync(
            regionsOfInterest,
            this,
            editorTable,
            callback
        );
    }

    async updateRegionsOfInterestAsync(
        regionsOfInterest: RegionOfInterest[],
        editorContainer: EditorContainer,
        editorTable: EditorTable,
        callback: (editorTable: EditorTable) => void
    ) {
        const regionsOfInterestList = await editorContainer.props.regionOfInterestService.update(regionsOfInterest);
        callback(editorTable);
    }

    addRegionOfInterest = (): void => {
        let regionOfInterest: RegionOfInterest = {
            label: `Region of interest #${(this.state.regionsOfInterest.length + 1)}`,
            color: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
            coordinates: [],
            sensor: this.props.regionOfInterestService.sensorName
        };
        this.state.regionsOfInterest.push(regionOfInterest);
        this.setState({
            regionsOfInterest: this.state.regionsOfInterest,
            regionOfInterest: regionOfInterest
        }, () => {
            console.log(this.state.regionsOfInterest);
        });
    }

    removeRegionOfInterest = (regionOfInterest: RegionOfInterest): void => {
        const index = this.state.regionsOfInterest.indexOf(regionOfInterest);
        let regionsOfInterest: RegionOfInterest[] = [...this.state.regionsOfInterest.slice(0, index), ...this.state.regionsOfInterest.slice(index + 1)];
        this.setState({
            regionsOfInterest: regionsOfInterest,
            regionOfInterest: regionsOfInterest.length > 0 ? regionsOfInterest[0] : null
        }, () => {
            console.log(this.state.regionsOfInterest);
        });
    }

    changeRegionOfInterest = (regionOfInterest: RegionOfInterest): void => {
        this.setState({
            regionOfInterest: regionOfInterest
        });
    }

    changeEditorMode = (editorMode: EditorMode): void => {
        this.setState({
            editorMode: editorMode
        });
    }
}
