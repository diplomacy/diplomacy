import React from "react";
import {Button} from "./button";
import PropTypes from "prop-types";

export class DeleteButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = {step: 0};
        this.onClick = this.onClick.bind(this);
    }

    onClick() {
        this.setState({step: this.state.step + 1}, () => {
            if (this.state.step === 2)
                this.props.onClick();
        });
    }

    render() {
        let title = '';
        let color = '';
        if (this.state.step === 0) {
            title = this.props.title;
            color = 'secondary';
        } else if (this.state.step === 1) {
            title = this.props.confirmTitle;
            color = 'danger';
        } else if (this.state.step === 2) {
            title = this.props.waitingTitle;
            color = 'danger';
        }
        return (
            <Button title={title} color={color} onClick={this.onClick} small={true} large={true}/>
        );
    }
}

DeleteButton.propTypes = {
    title: PropTypes.string.isRequired,
    confirmTitle: PropTypes.string.isRequired,
    waitingTitle: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired
};
