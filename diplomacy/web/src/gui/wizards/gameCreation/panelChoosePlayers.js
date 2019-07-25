import React from "react";
import {FancyBox} from "../../components/fancyBox";
import PropTypes from "prop-types";
import Octicon, {ArrowLeft} from "@primer/octicons-react";

export class PanelChoosePlayers extends React.Component {
    render() {
        return (
            <FancyBox title={'Number of human players'} onClose={this.props.cancel}>
                <div className="row">
                    <div className="col-sm">
                        <button type="button" className="btn btn-secondary btn-sm btn-block inline" onClick={() => {
                            this.props.onUpdateParams({n_controls: 0});
                            this.props.forward(2);
                        }}>None - just bots
                        </button>
                    </div>
                    <div className="col-sm">
                        <button type="button" className="btn btn-secondary btn-sm btn-block inline" onClick={() => {
                            this.props.onUpdateParams({n_controls: this.props.nbPowers});
                            this.props.forward();
                        }}>All humans - no bots
                        </button>
                    </div>
                </div>
                <div className="d-flex flex-row justify-content-center my-2">
                    {(() => {
                        const choice = [];
                        for (let i = 0; i < this.props.nbPowers; ++i) {
                            choice.push(
                                <button key={i} type="button"
                                        className={`btn btn-secondary btn-sm flex-grow-1 ${i === 0 ? '' : 'ml-sm-1'}`}
                                        onClick={() => {
                                            this.props.onUpdateParams({n_controls: i + 1});
                                            this.props.forward();
                                        }}>
                                    {i + 1}
                                </button>
                            );
                        }
                        return choice;
                    })()}
                </div>
                <div>
                    <button type="button" className="btn btn-secondary btn-sm px-3"
                            onClick={() => this.props.backward()}>
                        <Octicon icon={ArrowLeft}/>
                    </button>
                </div>
            </FancyBox>
        );
    }
}

PanelChoosePlayers.propTypes = {
    backward: PropTypes.func.isRequired,
    forward: PropTypes.func.isRequired,
    cancel: PropTypes.func.isRequired,
    onUpdateParams: PropTypes.func.isRequired,
    nbPowers: PropTypes.number.isRequired
};
