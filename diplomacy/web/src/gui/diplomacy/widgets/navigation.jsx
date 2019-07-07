import React from "react";
import Octicon, {Person} from "@githubprimer/octicons-react";
import PropTypes from "prop-types";

export class Navigation extends React.Component {
    render() {
        const hasNavigation = this.props.navigation && this.props.navigation.length;
        if (hasNavigation) {
            return (
                <div className={'title row'}>
                    <div className={'col align-self-center'}>
                        <strong>{this.props.title}</strong>
                        {this.props.afterTitle ? this.props.afterTitle : ''}
                    </div>
                    <div className={'col-sm-1'}>
                        {(!hasNavigation && (
                            <div className={'float-right'}>
                                <strong>
                                    <u className={'mr-2'}>{this.props.username}</u>
                                    <Octicon icon={Person}/>
                                </strong>
                            </div>
                        )) || (
                            <div className="dropdown float-right">
                                <button className="btn btn-secondary dropdown-toggle" type="button"
                                        id="dropdownMenuButton" data-toggle="dropdown"
                                        aria-haspopup="true" aria-expanded="false">
                                    {(this.props.username && (
                                        <span>
                                                <u className={'mr-2'}>{this.props.username}</u>
                                                <Octicon icon={Person}/>
                                            </span>
                                    )) || 'Menu'}
                                </button>
                                <div className="dropdown-menu dropdown-menu-right"
                                     aria-labelledby="dropdownMenuButton">
                                    {this.props.navigation.map((nav, index) => {
                                        const navTitle = nav[0];
                                        const navAction = nav[1];
                                        return <span key={index} className="dropdown-item"
                                                     onClick={navAction}>{navTitle}</span>;
                                    })}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            );
        }
        return (
            <div className={'title'}><strong>{this.props.title}</strong></div>
        );
    }
}

Navigation.propTypes = {
    title: PropTypes.string.isRequired,
    afterTitle: PropTypes.object,
    navigation: PropTypes.array,
    username: PropTypes.string,
};
