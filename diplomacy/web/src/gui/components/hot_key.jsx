import React from 'react';
import PropTypes from 'prop-types';
import Mousetrap from 'mousetrap';

// One document listener dispatches each key to its most recently mounted owner.
const keyboard = Mousetrap; // Reuse Mousetrap's single built-in document instance.
const owners = new Map();

function keysFor(props) {
    return [...new Set(props.keys)].sort();
}

export default class HotKey extends React.Component {
    componentDidMount() {
        this.bindKeys();
    }

    componentDidUpdate() {
        const keys = keysFor(this.props);
        if (keys.length !== this.boundKeys.length || keys.some((key, index) => key !== this.boundKeys[index])) {
            this.unbindKeys();
            this.bindKeys();
        }
    }

    componentWillUnmount() {
        this.unbindKeys();
    }

    bindKeys() {
        this.boundKeys = keysFor(this.props);
        for (const key of this.boundKeys) {
            if (!owners.has(key)) {
                owners.set(key, []);
                keyboard.bind(key, (event, combination) => {
                    const stack = owners.get(key);
                    const owner = stack && stack[stack.length - 1];
                    if (owner)
                        owner.props.onKeysPressed(event, combination);
                    // Do not return the callback's value: false would prevent default.
                });
            }
            owners.get(key).push(this);
        }
    }

    unbindKeys() {
        for (const key of this.boundKeys) {
            const stack = owners.get(key);
            stack.splice(stack.indexOf(this), 1);
            if (!stack.length) {
                keyboard.unbind(key);
                owners.delete(key);
            }
        }
    }

    render() {
        return null;
    }
}

HotKey.propTypes = {
    keys: PropTypes.arrayOf(PropTypes.string).isRequired,
    onKeysPressed: PropTypes.func.isRequired
};
