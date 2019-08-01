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

export class Move extends React.Component {
    render() {
        const src_loc = this.props.srcLoc;
        const dest_loc = this.props.dstLoc;
        let src_loc_x = 0;
        let src_loc_y = 0;
        if (this.props.phaseType === 'R') {
            src_loc_x = offset(Coordinates[src_loc].unit[0], -2.5);
            src_loc_y = offset(Coordinates[src_loc].unit[1], -2.5);
        } else {
            src_loc_x = offset(Coordinates[src_loc].unit[0], 10);
            src_loc_y = offset(Coordinates[src_loc].unit[1], 10);
        }
        let dest_loc_x = offset(Coordinates[dest_loc].unit[0], 10);
        let dest_loc_y = offset(Coordinates[dest_loc].unit[1], 10);

        // Adjusting destination
        const delta_x = parseFloat(dest_loc_x) - parseFloat(src_loc_x);
        const delta_y = parseFloat(dest_loc_y) - parseFloat(src_loc_y);
        const vector_length = Math.sqrt(delta_x * delta_x + delta_y * delta_y);
        dest_loc_x = '' + Math.round((parseFloat(src_loc_x) + (vector_length - 30.) / vector_length * delta_x) * 100.) / 100.;
        dest_loc_y = '' + Math.round((parseFloat(src_loc_y) + (vector_length - 30.) / vector_length * delta_y) * 100.) / 100.;
        return (
            <g>
                <line x1={src_loc_x}
                      y1={src_loc_y}
                      x2={dest_loc_x}
                      y2={dest_loc_y}
                      className={'varwidthshadow'}
                      strokeWidth={10}/>
                <line x1={src_loc_x}
                      y1={src_loc_y}
                      x2={dest_loc_x}
                      y2={dest_loc_y}
                      className={'varwidthorder'}
                      markerEnd={'url(#arrow)'}
                      stroke={Colors[this.props.powerName]}
                      strokeWidth={6}/>
            </g>
        );
    }
}

Move.propTypes = {
    srcLoc: PropTypes.string.isRequired,
    dstLoc: PropTypes.string.isRequired,
    powerName: PropTypes.string.isRequired,
    phaseType: PropTypes.string.isRequired
};
