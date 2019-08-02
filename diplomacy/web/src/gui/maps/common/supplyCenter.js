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
import {offset} from "./common";
import PropTypes from "prop-types";

export class SupplyCenter extends React.Component {
    render() {
        const Coordinates = this.props.coordinates;
        const SymbolSizes = this.props.symbolSizes;
        const symbol = 'SupplyCenter';
        const loc_x = offset(Coordinates[this.props.loc].sc[0], -8.5);
        const loc_y = offset(Coordinates[this.props.loc].sc[1], -11.0);
        return (
            <use href={`#${symbol}`}
                 x={loc_x}
                 y={loc_y}
                 width={SymbolSizes[symbol].width}
                 height={SymbolSizes[symbol].height}
                 className={`${this.props.powerName ? `sc${this.props.powerName.toLowerCase()}` : 'scnopower'}`}/>
        );
    }
}

SupplyCenter.propTypes = {
    loc: PropTypes.string.isRequired,
    powerName: PropTypes.string,
    coordinates: PropTypes.object.isRequired,
    symbolSizes: PropTypes.object.isRequired
};
