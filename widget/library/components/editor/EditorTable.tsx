import * as React from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Card, Dialog, DialogActions, DialogSurface, DialogTitle, DialogTrigger } from '@fluentui/react-components/unstable';
import { Button, Input, Label } from "@fluentui/react-components";
import { Add24Regular, Delete24Regular, Save24Regular } from "@fluentui/react-icons";
import "./EditorTable.css";
import { RegionOfInterest } from '../../types/RegionOfInterest';

export interface IEditorTableProps {
    regionsOfInterest: RegionOfInterest[];
    regionOfInterest: RegionOfInterest;

    changeRegionOfInterest: (regionOfInterest: RegionOfInterest) => void;
    updateRegionsOfInterest: (regionsOfInterest: RegionOfInterest[], editorTable: EditorTable, callback: (editorTable: EditorTable) => void) => void;
    addRegionOfInterest: () => void;
    removeRegionOfInterest: (regionOfInterest: RegionOfInterest) => void;
}

export interface IEditorTableState {
    openUpdateRegionsOfInterestDialog: boolean;
}

export default class EditorTable extends React.Component<IEditorTableProps, IEditorTableState> {
    constructor(props: IEditorTableProps) {
        super(props);

        this.state = {
            openUpdateRegionsOfInterestDialog: false
        }
    }

    public render() {
        return (
            <React.Fragment>
                <div
                    style={{
                        width: 240
                    }}
                >
                    <Card
                        style={{
                            display: 'flex',
                            flexDirection: 'row-reverse'
                        }}
                    >
                        <Button
                            icon={<Add24Regular />}
                            title="Add Region of Interest"
                            style={{ float: 'right' }}
                            onClick={() => {
                                this.props.addRegionOfInterest();
                            }}
                        />
                    </Card>
                    <Card
                        style={{
                            marginBottom: 5,
                            marginTop: 5,
                            height: this.props.regionOfInterest ? 240 : 345
                        }}
                    >
                        <div
                            className={"scrollhost"}
                        >
                            <table
                                style={{
                                    borderCollapse: 'collapse',
                                    width: '100%'
                                }}
                            >
                                <tbody>
                                    {
                                        this.props.regionsOfInterest.map((regionOfInterest, key) => {
                                            return (
                                                <tr
                                                    key={uuidv4()}
                                                    className='rowHover'
                                                    style={this.props.regionOfInterest === regionOfInterest ? { backgroundColor: '#f3f2f1' } : {}}
                                                    onClick={(e) => {
                                                        this.props.changeRegionOfInterest(regionOfInterest);
                                                    }}
                                                >
                                                    <td
                                                        style={{
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center'
                                                        }}
                                                    >
                                                        <Label>{regionOfInterest.label}</Label>
                                                    </td>
                                                </tr>
                                            )
                                        })
                                    }
                                </tbody>
                            </table>
                        </div>
                    </Card>
                    {
                        this.props.regionOfInterest ? (
                            <Card
                                style={{
                                    marginTop: 5,
                                    marginBottom: 5,
                                    height: 75
                                }}
                            >
                                <div>
                                    <table
                                        style={{
                                            width: '100%'
                                        }}
                                    >
                                        <tbody>
                                            <tr>
                                                <td>
                                                    <Input
                                                        type="text"
                                                        style={{
                                                            width: '100%'
                                                        }}
                                                        defaultValue={this.props.regionOfInterest.label}
                                                        onChange={(e) => {
                                                            const value = (e.target as any).value;
                                                            this.props.regionOfInterest.label = value;
                                                            this.forceUpdate();
                                                        }}
                                                    />
                                                </td>
                                            </tr>
                                            <tr>
                                                <td
                                                    style={{
                                                        alignContent: 'center',
                                                        justifyContent: 'space-between',
                                                        display: 'flex'
                                                    }}
                                                >
                                                    <input
                                                        type="color"
                                                        style={{
                                                            width: '85%',
                                                            height: '32px',
                                                            border: '1px solid lightgrey'
                                                        }}
                                                        value={this.props.regionOfInterest.color}
                                                        onChange={(e) => {
                                                            this.props.regionOfInterest.color = e.target.value;
                                                            this.forceUpdate();
                                                        }}
                                                    />
                                                    <Button
                                                        icon={<Delete24Regular />}
                                                        style={{
                                                            width: 25
                                                        }}
                                                        title="Delete Region of Interest"
                                                        onClick={() => {
                                                            this.props.removeRegionOfInterest(this.props.regionOfInterest);
                                                        }}
                                                    />
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </Card>
                        ) : null
                    }
                    <Card
                        style={{
                            display: 'flex',
                            flexDirection: 'row-reverse'
                        }}
                    >
                        <Button
                            icon={<Save24Regular />}
                            title="Save Regions of Interest"
                            onClick={() => {
                                this.props.updateRegionsOfInterest(this.props.regionsOfInterest, this, (editorTable: EditorTable) => {
                                    editorTable.setState({
                                        openUpdateRegionsOfInterestDialog: true
                                    });
                                });
                            }}
                        />
                        <Dialog open={this.state.openUpdateRegionsOfInterestDialog}>
                            <DialogSurface aria-label="label">
                                <DialogTitle>Regions of Interest Updated</DialogTitle>
                                <DialogActions>
                                    <DialogTrigger>
                                        <Button
                                            appearance="secondary"
                                            onClick={() => {
                                                this.setState({
                                                    openUpdateRegionsOfInterestDialog: false
                                                })
                                            }}
                                        >
                                            Okay
                                        </Button>
                                    </DialogTrigger>
                                </DialogActions>
                            </DialogSurface>
                        </Dialog>
                    </Card>
                </div>
            </React.Fragment >
        );
    }
}
