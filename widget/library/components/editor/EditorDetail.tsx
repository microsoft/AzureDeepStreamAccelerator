import * as React from 'react';
import { SketchPicker, TwitterPicker } from 'react-color';
import { Card } from '@fluentui/react-components/unstable';
import { Button, Input, Label } from "@fluentui/react-components";
import { Delete24Regular } from "@fluentui/react-icons";
import "./EditorTable.css";
import { RegionOfInterest } from '../../types/RegionOfInterest';

export interface IEditorTableProps {
    regionOfInterest: RegionOfInterest;

    removeRegionOfInterest: (regionOfInterest: RegionOfInterest) => void;
}

export interface IEditorTableState {

}

export default class EditorDetail extends React.Component<IEditorTableProps, IEditorTableState> {
    constructor(props: IEditorTableProps) {
        super(props);

        this.state = {

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
                            icon={<Delete24Regular />}
                            style={{
                                width: 25
                            }}
                            title="Delete Region of Interest"
                            onClick={() => {
                                this.props.removeRegionOfInterest(this.props.regionOfInterest);
                            }}
                        />
                    </Card>
                    <Card
                        style={{
                            marginTop: 5,
                            height: 345
                        }}
                    >
                        <div>
                            <table
                                style={{
                                    borderCollapse: 'collapse',
                                    width: '100%'
                                }}
                            >
                                <tbody>
                                    <tr>
                                        <td
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center'
                                            }}
                                        >
                                            <Input
                                                type="text"
                                                width={'100%'}
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
                                                display: 'flex',
                                                alignItems: 'center'
                                            }}
                                        >
                                            <div
                                                style={{
                                                    marginTop: 5
                                                }}
                                            >
                                                <input
                                                    type="color"                                                
                                                    value={this.props.regionOfInterest.color}
                                                    onChange={(e) => {
                                                        this.props.regionOfInterest.color = e.target.value;
                                                        this.forceUpdate();
                                                    }}
                                                />
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </Card>
                    <Card
                        style={{
                            marginTop: 5,
                            height: 32
                        }}
                    >
                    </Card>
                </div>
            </React.Fragment >
        );
    }
}
