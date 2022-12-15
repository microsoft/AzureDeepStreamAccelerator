import * as React from 'react';
import Widget from '../../library/components/Widget';
import './App.css';
import Options from './Options';

export default class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sensorName: '',
            sasUrl: '',
            sasToken: '',
            containerName: '',
            connectionString: '',
            deviceName: '',
            moduleId: '',

            servicesOptionsLoaded: false
        }
    }

    componentDidMount() {
        this.getOptions();
    }

    render() {
        return (
            <React.Fragment>
                <h1 style={{ color: 'lightgrey'}}>Widget Example App</h1>
                {
                    this.state.servicesOptionsLoaded ? (
                        <Widget
                            azdaDataServiceOptions={{
                                sasUrl: this.state.sasUrl,
                                sasToken: this.state.sasToken,
                                containerName: this.state.containerName,
                                sensorName: this.state.sensorName
                            }}
                            regionOfInterestServiceOptions={{
                                connectionString: this.state.connectionString,
                                deviceName: this.state.deviceName,
                                moduleId: this.state.moduleId,
                                sensorName: this.state.sensorName
                            }}
                        />
                    ) : (
                        <Options
                            sensorName={this.state.sensorName}
                            sasUrl={this.state.sasUrl}
                            sasToken={this.state.sasToken}
                            containerName={this.state.containerName}
                            connectionString={this.state.connectionString}
                            deviceName={this.state.deviceName}
                            moduleId={this.state.moduleId}
                            setOptions={this.setOptions}
                        />
                    )
                }
            </React.Fragment>
        );
    }
    getOptions = () => {
        let options = {
            sensorName: '',
            sasUrl: '',
            sasToken: '',
            containerName: '',
            connectionString: '',
            deviceName: '',
            moduleId: ''
        };

        let optionsString = localStorage.getItem('Widget Example App Options');
        if(optionsString) {
            options = JSON.parse(optionsString);
        }

        this.setState({
            sensorName: options.sensorName,
            sasUrl: options.sasUrl,
            sasToken: options.sasToken,
            containerName: options.containerName,
            connectionString: options.connectionString,
            deviceName: options.deviceName,
            moduleId: options.moduleId
        });
    }

    setOptions = (options, save = false) => {
        this.setState({
            sensorName: options.sensorName,
            sasUrl: options.sasUrl,
            sasToken: options.sasToken,
            containerName: options.containerName,
            connectionString: options.connectionString,
            deviceName: options.deviceName,
            moduleId: options.moduleId,

            servicesOptionsLoaded: true
        });
        if(save) {
            localStorage.setItem('Widget Example App Options', JSON.stringify({
                sensorName: options.sensorName,
                sasUrl: options.sasUrl,
                sasToken: options.sasToken,
                containerName: options.containerName,
                connectionString: options.connectionString,
                deviceName: options.deviceName,
                moduleId: options.moduleId,
            }))
        }
    }
}