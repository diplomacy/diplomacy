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
import SVG from 'react-inlinesvg';
import mapSVG from '../../standard.svg';
import {Renderer} from "./renderer";
import {MapData} from "../utils/map_data";
import {DOMOrderBuilder} from "./dom_order_builder";
import PropTypes from 'prop-types';
import {DOMPastMap} from "./dom_past_map";

export class Map extends React.Component {
    // id: ID of div wrapping SVG map.
    // mapInfo: dict
    // game: game engine
    // onError: callback(error)
    // showOrders: bool

    // orderBuilding: dict
    // onOrderBuilding: callback(powerName, orderBuildingPath)
    // onOrderBuilt: callback(powerName, orderString)

    constructor(props) {
        super(props);
        this.renderer = null;
        this.domOrderBuilder = null;
        this.domPastMap = null;
        this.initSVG = this.initSVG.bind(this);
    }

    initSVG() {
        const svg = document.getElementById(this.props.id).getElementsByTagName('svg')[0];

        const game = this.props.game;
        const mapData = new MapData(this.props.mapInfo, game);
        this.renderer = new Renderer(svg, game, mapData);
        this.renderer.render(this.props.showOrders, this.props.orders);
        if (this.props.orderBuilding) {
            this.domOrderBuilder = new DOMOrderBuilder(
                svg,
                this.props.onOrderBuilding, this.props.onOrderBuilt, this.props.onSelectLocation, this.props.onSelectVia,
                this.props.onError
            );
            this.domOrderBuilder.init(game, mapData, this.props.orderBuilding);
        } else if (this.props.onHover) {
            this.domPastMap = new DOMPastMap(svg, this.props.onHover);
            this.domPastMap.init(game, mapData, this.props.orders);
        }
    }

    render() {
        if (this.renderer) {
            const game = this.props.game;
            const mapData = new MapData(this.props.mapInfo, game);
            this.renderer.update(game, mapData, this.props.showOrders, this.props.orders);
            if (this.domOrderBuilder)
                this.domOrderBuilder.update(game, mapData, this.props.orderBuilding);
            else if (this.domPastMap)
                this.domPastMap.update(game, mapData, this.props.orders);
        }
        const divFactory = ((props, children) => <div id={this.props.id} {...props}>{children}</div>);
        return <SVG wrapper={divFactory} uniquifyIDs={true} uniqueHash={this.props.id} src={mapSVG}
                    onLoad={this.initSVG} onError={err => this.props.onError(err.message)}>Game map</SVG>;
    }
}

Map.propTypes = {
    id: PropTypes.string,
    showOrders: PropTypes.bool,
    orders: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string)),
    onSelectLocation: PropTypes.func,
    onSelectVia: PropTypes.func,
    game: PropTypes.object,
    mapInfo: PropTypes.object,
    orderBuilding: PropTypes.object,
    onOrderBuilding: PropTypes.func,
    onOrderBuilt: PropTypes.func,
    onError: PropTypes.func,
    onHover: PropTypes.func,
};
