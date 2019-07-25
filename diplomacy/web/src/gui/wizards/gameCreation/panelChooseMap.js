import React from "react";
import {Maps} from "./mapList";
import {FancyBox} from "../../components/fancyBox";
import PropTypes from "prop-types";

export class PanelChooseMap extends React.Component {
    render() {
        const mapImg = require(`../../../maps/svg/${this.props.params.map.svgName()}.svg`);
        const mapEntries = [];
        let count = 0;
        for (let mapInfo of Maps) {
            ++count;
            if (!mapInfo.variants) {
                mapEntries.push(
                    <div key={count} className="mb-1">
                        <button type="button"
                                className="btn btn-secondary btn-sm btn-block"
                                onMouseOver={() => this.props.onUpdateParams({map: mapInfo})}
                                onClick={() => this.props.forward()}>
                            {mapInfo.title}
                        </button>
                    </div>
                );
            } else {
                const dropDownID = `collapse-${count}-${mapInfo.name}`;
                const variants = mapInfo.variants.slice();
                const defaultVariant = variants[0];
                mapEntries.push(
                    <div key={count}>
                        <div className="mb-1 d-flex flex-row justify-content-center">
                            <button type="button"
                                    className="btn btn-secondary btn-sm flex-grow-1 mr-1"
                                    onMouseOver={() => this.props.onUpdateParams({map: defaultVariant})}
                                    onClick={() => this.props.forward()}>
                                {mapInfo.title} ({defaultVariant.title})
                            </button>
                            <button type="button"
                                    className="btn btn-outline-secondary btn-sm collapsed"
                                    data-toggle="collapse"
                                    data-target={`#${dropDownID}`}
                                    aria-expanded={false}
                                    aria-controls={dropDownID}>
                                <span className="unroll"><strong>+</strong></span>
                                <span className="roll"><strong>-</strong></span>
                            </button>
                        </div>
                        <div className="collapse" id={dropDownID}>
                            <div>
                                {(() => {
                                    const views = [];
                                    for (let i = 1; i < variants.length; ++i) {
                                        const variantInfo = variants[i];
                                        views.push(
                                            <div key={variantInfo.name} className="mb-1">
                                                <button type="button"
                                                        className="btn btn-outline-secondary btn-sm btn-block"
                                                        onMouseOver={() => this.props.onUpdateParams({map: variantInfo})}
                                                        onClick={() => this.props.forward()}>
                                                    {variantInfo.title}
                                                </button>
                                            </div>
                                        );
                                    }
                                    return views;
                                })()}
                            </div>
                        </div>
                    </div>
                );
            }
        }
        return (
            <FancyBox title={'Choose a map'} onClose={this.props.cancel}>
                <div className="row panel-choose-map">
                    <div className="col-md">
                        <div className="map-list p-1 ml-0 ml-sm-1">
                            {mapEntries}
                        </div>
                    </div>
                    <div className="col-md">
                        <img className="img-fluid" src={mapImg} alt={this.props.params.map.title}/>
                    </div>
                </div>
            </FancyBox>
        );
    }
}

PanelChooseMap.propTypes = {
    forward: PropTypes.func.isRequired,
    cancel: PropTypes.func.isRequired,
    params: PropTypes.object.isRequired,
    onUpdateParams: PropTypes.func.isRequired
};
