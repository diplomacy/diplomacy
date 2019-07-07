import React from "react";
import PropTypes from "prop-types";

export class Button extends React.Component {
    /** Bootstrap button.
     * Bootstrap classes:
     * - btn
     * - btn-primary
     * - mx-1 (margin-left 1px, margin-right 1px)
     * Props: title (str), onClick (function).
     * **/
    // title
    // onClick
    // pickEvent = false
    // large = false
    // small = false

    constructor(props) {
        super(props);
        this.onClick = this.onClick.bind(this);
    }

    onClick(event) {
        if (this.props.onClick)
            this.props.onClick(this.props.pickEvent ? event : null);
    }

    render() {
        return (
            <button
                className={`btn btn-${this.props.color || 'secondary'}` + (this.props.large ? ' btn-block' : '') + (this.props.small ? ' btn-sm' : '')}
                disabled={this.props.disabled}
                onClick={this.onClick}>
                <strong>{this.props.title}</strong>
            </button>
        );
    }
}

Button.propTypes = {
    title: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
    color: PropTypes.string,
    large: PropTypes.bool,
    small: PropTypes.bool,
    pickEvent: PropTypes.bool,
    disabled: PropTypes.bool
};

Button.defaultPropTypes = {
    disabled: false
};
