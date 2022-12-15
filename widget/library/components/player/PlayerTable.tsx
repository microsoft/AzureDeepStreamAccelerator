import * as React from 'react';
import { Card } from '@fluentui/react-components/unstable';
import { Input, Menu, MenuTrigger, MenuButton, MenuPopover, MenuList, MenuItem, Label } from "@fluentui/react-components";
import { DateFilterMode } from '../../enums/DateFilterMode';
import { AzdaData } from '../../types/AzdaData';
import "./PlayerTable.css";

export interface IPlayerTableProps {
    azdaDataList: AzdaData[];
    azdaData: AzdaData;
    dateFilterMode: DateFilterMode;
    searchDate: Date;
    changeSearchDate: (searchDate: Date) => void;
    changeDateFilterMode: (dateFilterMode: DateFilterMode) => void;
    changeAzdaData: (azdaData: AzdaData, nextVideoUrl: string) => void;
}

export interface IPlayerTableState {
}

export default class PlayerTable extends React.Component<IPlayerTableProps, IPlayerTableState> {
    constructor(props: IPlayerTableProps) {
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
                    <Card>
                        <Input
                            type='datetime-local'
                            onChange={(e) => {
                                const value = (e.target as any).value;
                                const searchDate = new Date(value);
                                this.props.changeSearchDate(searchDate);
                            }}
                        />
                    </Card>
                    <Card
                        style={{
                            marginTop: 5,
                            display: 'flex',
                            flexDirection: 'row-reverse'
                        }}
                    >
                        <Menu>
                            <MenuTrigger>
                                <MenuButton>{this.props.dateFilterMode}</MenuButton>
                            </MenuTrigger>
                            <MenuPopover>
                                <MenuList>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Year)}>Year</MenuItem>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Month)}>Month</MenuItem>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Week)}>Week</MenuItem>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Day)}>Day</MenuItem>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Hour)}>Hour</MenuItem>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Minute)}>Minute</MenuItem>
                                    <MenuItem onClick={() => this.props.changeDateFilterMode(DateFilterMode.Second)}>Second</MenuItem>
                                </MenuList>
                            </MenuPopover>
                        </Menu>
                    </Card>
                    <Card
                        style={{
                            marginTop: 5,
                            height: 345
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
                                        this.props.azdaDataList.map((azdaData, key) => {
                                            return (
                                                <tr
                                                    className='rowHover'
                                                    key={key}
                                                    style={this.props.azdaData === azdaData ? { backgroundColor: '#f3f2f1' } : {}}
                                                    onClick={(e) => {
                                                        const index = this.props.azdaDataList.indexOf(azdaData);
                                                        this.props.changeAzdaData(
                                                            azdaData,
                                                            index + 1 < this.props.azdaDataList.length ? this.props.azdaDataList[index + 1].videoUrl : ''
                                                        );
                                                    }}
                                                >
                                                    <td align='center'>
                                                        {azdaData.date.toString()}
                                                    </td>
                                                </tr>
                                            )
                                        })
                                    }
                                </tbody>
                            </table>
                        </div>
                    </Card>
                </div>
            </React.Fragment >
        );
    }
}
