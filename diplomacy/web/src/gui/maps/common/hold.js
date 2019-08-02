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

export class Hold extends React.Component {
    render() {
        const Coordinates = this.props.coordinates;
        const Colors = this.props.colors;
        const polygon_coord = [];
        const loc_x = offset(Coordinates[this.props.loc].unit[0], 8.5);
        const loc_y = offset(Coordinates[this.props.loc].unit[1], 9.5);
        for (let ofs of [
            [13.8, -33.3], [33.3, -13.8], [33.3, 13.8], [13.8, 33.3], [-13.8, 33.3],
            [-33.3, 13.8], [-33.3, -13.8], [-13.8, -33.3]]
            ) {
            polygon_coord.push(offset(loc_x, ofs[0]) + ',' + offset(loc_y, ofs[1]));
        }
        return (
            <g>
                <polygon strokeWidth={10} className={'varwidthshadow'} points={polygon_coord.join(' ')}/>
                <polygon strokeWidth={6} className={'varwidthorder'} points={polygon_coord.join(' ')}
                         stroke={Colors[this.props.powerName]}/>
            </g>
        );
    }
}

Hold.propTypes = {
    loc: PropTypes.string.isRequired,
    powerName: PropTypes.string.isRequired,
    coordinates: PropTypes.object.isRequired,
    colors: PropTypes.object.isRequired
};
