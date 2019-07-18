import React from 'react';
import {Button} from "./button";
import {Bar} from "./layouts";
import PropTypes from 'prop-types';

export class PowerOrdersActionBar extends React.Component {
    render() {
        return (
            <Bar className={'p-2'}>
                <strong className={'mr-4'}>Orders:</strong>
                <Button title={'reset'} onClick={this.props.onReset}/>
                <Button title={'delete all'} onClick={this.props.onDeleteAll}/>
                <Button color={'primary'} title={'update'} onClick={this.props.onUpdate}/>
                {(this.props.onProcess &&
                    <Button color={'danger'} title={'process game'} onClick={this.props.onProcess}/>) || ''}
            </Bar>
        );
    }
}

PowerOrdersActionBar.propTypes = {
    onReset: PropTypes.func.isRequired,
    onDeleteAll: PropTypes.func.isRequired,
    onUpdate: PropTypes.func.isRequired,
    onProcess: PropTypes.func
};
