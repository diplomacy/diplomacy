import React from "react";
import PropTypes from 'prop-types';
import {FancyBox} from "./fancyBox";

export class Help extends React.Component {
    render() {
        return (
            <FancyBox title={'Help'} onClose={this.props.onClose}>
                <div>
                    <p>When building an order, press <strong>ESC</strong> to reset build.</p>
                    <p>Press letter associated to an order type to start building an order of this type.
                        <br/> Order type letter is indicated in order type name after order type radio button.
                    </p>
                    <p>In Phase History tab, use keyboard left and right arrows to navigate in past phases.</p>
                </div>
            </FancyBox>
        );
    }
}

Help.propTypes = {
    onClose: PropTypes.func.isRequired
};
