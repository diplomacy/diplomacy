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
import React from 'react';
import {Button} from "./widgets";
import PropTypes from 'prop-types';

const TIMES = '\u00D7';

export class FancyBox extends React.Component {
    // open-tag (<FancyBox></FancyBox>)
    // PROPERTIES
    // title
    // onClose
    render() {
        return (
            <div className={'fancy-wrapper'} onClick={this.props.onClose}>
                <div className={'fancy-box container'} onClick={(event) => {
                    if (!event)
                        event = window.event;
                    if (event.hasOwnProperty('cancelBubble'))
                        event.cancelBubble = true;
                    if (event.stopPropagation)
                        event.stopPropagation();
                }}>
                    <div className={'row fancy-bar'}>
                        <div className={'col-11 align-self-center fancy-title'}>{this.props.title}</div>
                        <div className={'col-1 fancy-button'}>
                            <Button title={TIMES} color={'danger'} onClick={this.props.onClose}/>
                        </div>
                    </div>
                    <div className={'row'}>
                        <div className={'col fancy-content'}>{this.props.children}</div>
                    </div>
                </div>
            </div>
        );
    }
}


FancyBox.propTypes = {
    title: PropTypes.string.isRequired,
    onClose: PropTypes.func.isRequired,
    children: PropTypes.oneOfType([PropTypes.array, PropTypes.object])
};
