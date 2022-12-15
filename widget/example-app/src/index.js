import React from 'react';
import ReactDOM from "react-dom";
import App from "./App.jsx";
import { FluentProvider, webLightTheme } from '@fluentui/react-components';

ReactDOM.render(
    <FluentProvider theme={webLightTheme}>
        <App />
    </FluentProvider>,
    document.getElementById("root")
);