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

export class Disband extends React.Component {
    render() {
        const Coordinates = this.props.coordinates;
        const SymbolSizes = this.props.symbolSizes;
        const loc = this.props.loc;
        const phaseType = this.props.phaseType;
        let loc_x = 0;
        let loc_y = 0;
        if (phaseType === 'R') {
            loc_x = offset(Coordinates[loc].unit[0], -29.);
            loc_y = offset(Coordinates[loc].unit[1], -27.5);
        } else {
            loc_x = offset(Coordinates[loc].unit[0], -16.5);
            loc_y = offset(Coordinates[loc].unit[1], -15.);
        }
        const symbol = 'RemoveUnit';
        return (
            <g>
                <use x={loc_x}
                     y={loc_y}
                     height={SymbolSizes[symbol].height}
                     width={SymbolSizes[symbol].width}
                     href={`#${symbol}`}
                />
            </g>
        );
    }
}

Disband.propTypes = {
    loc: PropTypes.string.isRequired,
    phaseType: PropTypes.string.isRequired,
    coordinates: PropTypes.object.isRequired,
    symbolSizes: PropTypes.object.isRequired
};
