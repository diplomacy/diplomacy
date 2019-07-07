import React from "react";
import PropTypes from "prop-types";

export class Tab extends React.Component {
    render() {
        const style = {
            display: this.props.display ? 'block' : 'none'
        };
        const id = this.props.id ? {id: this.props.id} : {};
        return (
            <div className={'tab mb-4 ' + this.props.className} style={style} {...id}>
                {this.props.children}
            </div>
        );
    }
}

Tab.propTypes = {
    display: PropTypes.bool,
    className: PropTypes.string,
    id: PropTypes.string,
    children: PropTypes.oneOfType([PropTypes.array, PropTypes.object])
};

Tab.defaultProps = {
    display: false,
    className: '',
    id: ''
};
