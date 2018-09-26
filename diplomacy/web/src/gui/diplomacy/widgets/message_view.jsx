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
import {UTILS} from "../../../diplomacy/utils/utils";
import PropTypes from 'prop-types';

export class MessageView extends React.Component {
    // message
    render() {
        const message = this.props.message;
        const owner = this.props.owner;
        const id = this.props.id ? {id: this.props.id} : {};
        const messagesLines = message.message.replace('\r\n', '\n').replace('\r', '\n').split('\n');
        let onClick = null;
        const classNames = ['game-message'];
        if (owner === message.sender)
            classNames.push('message-sender');
        else {
            classNames.push('message-recipient');
            if (message.read || this.props.read)
                classNames.push('message-read');
            onClick = this.props.onClick ? {onClick: () => this.props.onClick(message)} : {};
        }
        return (
            <div className={'game-message-wrapper'} {...id}>
                <div className={classNames.join(' ')} {...onClick}>
                    <div className={'message-header'}>
                        {message.sender} {UTILS.html.UNICODE_SMALL_RIGHT_ARROW} {message.recipient}
                    </div>
                    <div className={'message-content'}>{messagesLines.map((line, lineIndex) => <div key={lineIndex}>{line}</div>)}</div>
                </div>
            </div>
        );
    }
}

MessageView.propTypes = {
    message: PropTypes.object,
    owner: PropTypes.string,
    onClick: PropTypes.func,
    id: PropTypes.string,
    read: PropTypes.bool
};
