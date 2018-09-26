// ==============================================================================
// Copyright (C) 2019 - Philip Paquette, Steven Bocco
//
//  This program is free software: you can redistribute it and/or modify it under
//  the terms of the GNU Affero General Public License as published by the Free
//  Software Foundation, either version 3 of the License, or (at your option) any
//  later version.
//
//  This program is distributed in the hope that it will be useful, but WITHOUT
//  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
//  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
//  details.
//
//  You should have received a copy of the GNU Affero General Public License along
//  with this program.  If not, see <https://www.gnu.org/licenses/>.
// ==============================================================================
import React from "react";
import PropTypes from 'prop-types';

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


export class Action extends React.Component {
    // title
    // isActive
    // onClick
    // See Button parameters.

    render() {
        return (
            <div className="action nav-item" onClick={this.props.onClick}>
                <div
                    className={'nav-link' + (this.props.isActive ? ' active' : '') + (this.props.highlight !== null ? ' updated' : '')}>
                    {this.props.title}
                    {this.props.highlight !== null
                    && this.props.highlight !== undefined
                    && <span className={'update'}>{this.props.highlight}</span>}
                </div>
            </div>
        );
    }
}

Action.propTypes = {
    title: PropTypes.string.isRequired,
    onClick: PropTypes.func.isRequired,
    highlight: PropTypes.any,
    isActive: PropTypes.bool
};

Action.defaultProps = {
    highlight: null,
    isActive: false
};
