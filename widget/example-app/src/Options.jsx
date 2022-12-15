import * as React from 'react';

export default class Options extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sensorName: this.props.sensorName,
            sasUrl: this.props.sasUrl,
            sasToken: this.props.sasToken,
            containerName: this.props.containerName,
            connectionString: this.props.connectionString,
            deviceName: this.props.deviceName,
            moduleId: this.props.moduleId
        }
    }

    componentDidUpdate(prevProps) {
        if (this.props.sensorName !== prevProps.sensorName) {
            this.setState({
                sensorName: this.props.sensorName
            });
        }
        if (this.props.sasUrl !== prevProps.sasUrl) {
            this.setState({
                sasUrl: this.props.sasUrl
            });
        }
        if (this.props.sasToken !== prevProps.sasToken) {
            this.setState({
                sasToken: this.props.sasToken
            });
        }
        if (this.props.containerName !== prevProps.containerName) {
            this.setState({
                containerName: this.props.containerName
            });
        }
        if (this.props.connectionString !== prevProps.connectionString) {
            this.setState({
                connectionString: this.props.connectionString
            });
        }
        if (this.props.deviceName !== prevProps.deviceName) {
            this.setState({
                deviceName: this.props.deviceName
            });
        }
        if (this.props.moduleId !== prevProps.moduleId) {
            this.setState({
                moduleId: this.props.moduleId
            });
        }
    }

    render() {
        return (
            <div
                style={{
                    margin: 10
                }}
            >
                <table
                    width={700}
                    cellPadding={10}
                >
                    <thead>
                        <tr>
                            <th>
                                Widget Options
                            </th>
                        </tr>
                    </thead>
                </table>
                <table
                    width={700}
                    cellPadding={10}
                >
                    <thead>
                        <tr>
                            <th>
                                Sensor
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>
                                Name
                            </td>
                            <td align='right'>
                                <input style={{ width: 400 }}
                                    defaultValue={this.state.sensorName}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            sensorName: value
                                        });
                                    }}
                                />
                            </td>
                        </tr>
                    </tbody>
                </table>
                <table
                    width={700}
                    cellPadding={10}
                >
                    <thead>
                        <tr>
                            <th>
                                Data
                            </th>
                        </tr>
                        <tr>
                            <td valign='top'>
                                Blob Storage SAS Url
                            </td>
                            <td align='right'>
                                <textarea
                                    style={{ width: 400, height: 100 }}
                                    defaultValue={this.state.sasUrl}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            sasUrl: value
                                        });
                                    }}
                                ></textarea>
                            </td>
                        </tr>
                        <tr>
                            <td valign='top'>
                                Blob Storage Container SAS Token
                            </td>
                            <td align='right'>
                                <textarea
                                    style={{ width: 400, height: 100 }}
                                    defaultValue={this.state.sasToken}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            sasToken: value
                                        });
                                    }}
                                ></textarea>
                            </td>
                        </tr>
                        <tr>
                            <td valign='top'>
                                Blob Storage Container Name
                            </td>
                            <td align='right'>
                                <input style={{ width: 400 }}
                                    defaultValue={this.state.containerName}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            containerName: value
                                        });
                                    }}
                                />
                            </td>
                        </tr>
                    </thead>
                </table>
                <table
                    width={700}
                    cellPadding={10}
                >
                    <thead>
                        <tr>
                            <th>
                                Regions of Interest
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td valign='top'>
                                IoTHub Connection String
                            </td>
                            <td align='right'>
                                <textarea
                                    style={{ width: 400, height: 100 }}
                                    defaultValue={this.state.connectionString}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            connectionString: value
                                        });
                                    }}
                                ></textarea>
                            </td>
                        </tr>
                        <tr>
                            <td valign='top'>
                                IotHub Device Name
                            </td>
                            <td align='right'>
                                <input style={{ width: 400 }}
                                    defaultValue={this.state.deviceName}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            deviceName: value
                                        });
                                    }}
                                />
                            </td>
                        </tr>
                        <tr>
                            <td valign='top'>
                                IotHub Module Id
                            </td>
                            <td align='right'>
                                <input style={{ width: 400 }}
                                    defaultValue={this.state.moduleId}
                                    onChange={(e) => {
                                        const value = e.target.value;
                                        this.setState({
                                            moduleId: value
                                        });
                                    }}
                                />
                            </td>
                        </tr>
                    </tbody>
                </table>
                <table
                    width={700}
                    cellPadding={10}
                >
                    <thead>
                        <tr>
                            <th>
                            </th>
                            <th align='right'>
                                <button
                                    disabled={!this.valid()}
                                    onClick={() => {
                                        this.props.setOptions({
                                            sensorName: this.state.sensorName,
                                            sasUrl: this.state.sasUrl,
                                            sasToken: this.state.sasToken,
                                            containerName: this.state.containerName,
                                            connectionString: this.state.connectionString,
                                            deviceName: this.state.deviceName,
                                            moduleId: this.state.moduleId
                                        }, true)
                                    }}
                                >
                                    Continue
                                </button>
                            </th>
                        </tr>
                    </thead>
                </table>
            </div>
        )
    }

    valid = () => {
        for (const key in this.state) {
            if (Object.hasOwnProperty.call(this.state, key)) {
                const element = this.state[key];
                if(element === '') {
                    return false;
                }
            }
        }
        return true;
    }
}