import * as React from 'react';

import { Card } from '@fluentui/react-components/unstable';
import { Button, Tab, TabList } from "@fluentui/react-components";
import { CircleSmall24Regular, Line24Regular, CheckboxUnchecked24Filled, Video24Regular, FullScreenMaximize24Regular } from "@fluentui/react-icons";
import { WidgetMode } from '../../enums/WidgetMode';
import { EditorMode } from '../../enums/EditorMode';

export interface IEditorToolbarProps {
    width: number;
    editorMode: EditorMode;
    changeWidgetMode: (widgetMode: WidgetMode) => void;
    changeEditorMode: (editorMode: EditorMode) => void;
}

export interface IEditorToolbarState {

}

export default class EditorToolbar extends React.Component<IEditorToolbarProps, IEditorToolbarState> {
    constructor(props: IEditorToolbarProps) {
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
                        <Button
                            style={{ visibility: 'hidden' }}
                            icon={<FullScreenMaximize24Regular />}
                        />
                        <Button
                            style={{ visibility: 'hidden' }}
                            icon={<FullScreenMaximize24Regular />}
                        />
                    </div>
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}
                    >
                        <TabList
                            size='small'
                            onTabSelect={(event, data) => {
                                this.props.changeEditorMode((data.value as EditorMode));
                            }}
                            defaultSelectedValue={(this.props.editorMode as any)}
                        >
                            <Tab icon={<CircleSmall24Regular />} value={EditorMode.Point} title='Point' aria-label='Point'></Tab>
                            <Tab icon={<Line24Regular />} value={EditorMode.Line} title='Line' aria-label='Line'></Tab>
                            <Tab icon={<CheckboxUnchecked24Filled />} value={EditorMode.Shape} title='Shape' aria-label='Shape'></Tab>
                        </TabList>
                    </div>
                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'flex-end'
                        }}
                    >
                        <Button
                            style={{ visibility: 'hidden' }}
                            icon={<FullScreenMaximize24Regular />}
                        />
                        <Button
                            icon={<Video24Regular />}
                            title="Switch to Play Mode"
                            style={{ marginRight: 2.5 }}
                            onClick={() => {
                                this.props.changeWidgetMode(WidgetMode.Play);
                            }}
                        />
                    </div>
                </Card>
            </React.Fragment >
        );
    }
}
