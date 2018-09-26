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
import {Forms} from "../../core/forms";
import {STRINGS} from "../../../diplomacy/utils/strings";
import PropTypes from "prop-types";

export class CreateForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = this.initState();
    }

    initState() {
        const state = {
            game_id: '',
            power_name: '',
            n_controls: 7,
            deadline: 300,
            registration_password: ''
        };
        for (let rule of STRINGS.PUBLIC_RULES)
            state[`rule_${rule.toLowerCase()}`] = false;
        return state;
    }

    render() {
        const onChange = Forms.createOnChangeCallback(this, this.props.onChange);
        const onSubmit = Forms.createOnSubmitCallback(this, this.props.onSubmit);
        return (
            <form>
                {Forms.createRow(
                    Forms.createColLabel('game_id', 'Game ID (optional)'),
                    <input id={'game_id'} className={'form-control'} type={'text'}
                           value={Forms.getValue(this.state, 'game_id')} onChange={onChange}/>
                )}
                {Forms.createRow(
                    Forms.createColLabel('power_name', 'power:'),
                    <select id={'power_name'} className={'form-control custom-select'}
                            value={Forms.getValue(this.state, 'power_name')} onChange={onChange}>
                        {Forms.createSelectOptions(STRINGS.ALL_POWER_NAMES, true)}
                    </select>
                )}
                {Forms.createRow(
                    Forms.createColLabel('n_controls', 'number of required players:'),
                    <input id={'n_controls'} className={'form-control'} type={'number'}
                           value={Forms.getValue(this.state, 'n_controls')} onChange={onChange}/>
                )}
                {Forms.createRow(
                    Forms.createColLabel('deadline', 'deadline (in seconds)'),
                    <input id={'deadline'} className={'form-control'} type={'number'}
                           value={Forms.getValue(this.state, 'deadline')}
                           onChange={onChange}/>
                )}
                {Forms.createRow(
                    Forms.createColLabel('registration_password', 'registration password'),
                    <input id={'registration_password'} className={'form-control'} type={'password'}
                           value={Forms.getValue(this.state, 'registration_password')} onChange={onChange}/>
                )}
                <div><strong>RULES:</strong></div>
                <div className={'mb-4'}>
                    {STRINGS.PUBLIC_RULES.map((rule, index) => (
                        <div key={index} className={'form-check-inline'}>
                            {Forms.createCheckbox(
                                `rule_${rule.toLowerCase()}`,
                                rule,
                                Forms.getValue(this.state, `rule_${rule.toLowerCase()}`),
                                onChange)}
                        </div>
                    ))}
                </div>
                {Forms.createRow('', Forms.createSubmit('create a game', true, onSubmit))}
            </form>
        );
    }
}

CreateForm.propTypes = {
    onChange: PropTypes.func,
    onSubmit: PropTypes.func
};
