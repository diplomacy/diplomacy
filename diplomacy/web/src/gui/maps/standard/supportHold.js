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
import {Colors, Coordinates, offset} from "./common";
import PropTypes from "prop-types";

export class SupportHold extends React.Component {
    render() {
        const loc = this.props.loc;
        const dest_loc = this.props.dstLoc;
        const loc_x = offset(Coordinates[loc].unit[0], 10);
        const loc_y = offset(Coordinates[loc].unit[1], 10);
        let dest_loc_x = offset(Coordinates[dest_loc].unit[0], 10);
        let dest_loc_y = offset(Coordinates[dest_loc].unit[1], 10);

        const delta_x = parseFloat(dest_loc_x) - parseFloat(loc_x);
        const delta_y = parseFloat(dest_loc_y) - parseFloat(loc_y);
        const vector_length = Math.sqrt(delta_x * delta_x + delta_y * delta_y);
        dest_loc_x = '' + Math.round((parseFloat(loc_x) + (vector_length - 35.) / vector_length * delta_x) * 100.) / 100.;
        dest_loc_y = '' + Math.round((parseFloat(loc_y) + (vector_length - 35.) / vector_length * delta_y) * 100.) / 100.;

        const polygon_coord = [];
        const poly_loc_x = offset(Coordinates[dest_loc].unit[0], 8.5);
        const poly_loc_y = offset(Coordinates[dest_loc].unit[1], 9.5);
        for (let ofs of [
            [15.9, -38.3], [38.3, -15.9], [38.3, 15.9], [15.9, 38.3], [-15.9, 38.3], [-38.3, 15.9],
            [-38.3, -15.9], [-15.9, -38.3]
        ]) {
            polygon_coord.push(offset(poly_loc_x, ofs[0]) + ',' + offset(poly_loc_y, ofs[1]));
        }
        return (
            <g>
                <line x1={loc_x}
                      y1={loc_y}
                      x2={dest_loc_x}
                      y2={dest_loc_y}
                      className={'shadowdash'}/>
                <line x1={loc_x}
                      y1={loc_y}
                      x2={dest_loc_x}
                      y2={dest_loc_y}
                      className={'supportorder'}
                      stroke={Colors[this.props.powerName]}/>
                <polygon className={'shadowdash'}
                         points={polygon_coord.join(' ')}/>
                <polygon className={'supportorder'}
                         points={polygon_coord.join(' ')}
                         stroke={Colors[this.props.powerName]}
                />
            </g>
        );
    }
}

SupportHold.propTypes = {
    loc: PropTypes.string.isRequired,
    dstLoc: PropTypes.string.isRequired,
    powerName: PropTypes.string.isRequired,
};
