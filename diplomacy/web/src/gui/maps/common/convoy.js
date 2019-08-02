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

export class Convoy extends React.Component {
    render() {
        const Coordinates = this.props.coordinates;
        const Colors = this.props.colors;
        const loc = this.props.loc;
        const src_loc = this.props.srcLoc;
        const dest_loc = this.props.dstLoc;
        const loc_x = offset(Coordinates[loc].unit[0], 10);
        const loc_y = offset(Coordinates[loc].unit[1], 10);
        const src_loc_x = offset(Coordinates[src_loc].unit[0], 10);
        const src_loc_y = offset(Coordinates[src_loc].unit[1], 10);
        let dest_loc_x = offset(Coordinates[dest_loc].unit[0], 10);
        let dest_loc_y = offset(Coordinates[dest_loc].unit[1], 10);

        const src_delta_x = parseFloat(src_loc_x) - parseFloat(loc_x);
        const src_delta_y = parseFloat(src_loc_y) - parseFloat(loc_y);
        const src_vector_length = Math.sqrt(src_delta_x * src_delta_x + src_delta_y * src_delta_y);
        const src_loc_x_1 = '' + Math.round((parseFloat(loc_x) + (src_vector_length - 30.) / src_vector_length * src_delta_x) * 100.) / 100.;
        const src_loc_y_1 = '' + Math.round((parseFloat(loc_y) + (src_vector_length - 30.) / src_vector_length * src_delta_y) * 100.) / 100.;

        let dest_delta_x = parseFloat(src_loc_x) - parseFloat(dest_loc_x);
        let dest_delta_y = parseFloat(src_loc_y) - parseFloat(dest_loc_y);
        let dest_vector_length = Math.sqrt(dest_delta_x * dest_delta_x + dest_delta_y * dest_delta_y);
        const src_loc_x_2 = '' + Math.round((parseFloat(dest_loc_x) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_x) * 100.) / 100.;
        const src_loc_y_2 = '' + Math.round((parseFloat(dest_loc_y) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_y) * 100.) / 100.;

        dest_delta_x = parseFloat(dest_loc_x) - parseFloat(src_loc_x);
        dest_delta_y = parseFloat(dest_loc_y) - parseFloat(src_loc_y);
        dest_vector_length = Math.sqrt(dest_delta_x * dest_delta_x + dest_delta_y * dest_delta_y);
        dest_loc_x = '' + Math.round((parseFloat(src_loc_x) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_x) * 100.) / 100.;
        dest_loc_y = '' + Math.round((parseFloat(src_loc_y) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_y) * 100.) / 100.;

        const triangle_coord = [];
        const triangle_loc_x = offset(Coordinates[src_loc].unit[0], 10);
        const triangle_loc_y = offset(Coordinates[src_loc].unit[1], 10);
        for (let ofs of [[0, -38.3], [33.2, 19.1], [-33.2, 19.1]]) {
            triangle_coord.push(offset(triangle_loc_x, ofs[0]) + ',' + offset(triangle_loc_y, ofs[1]));
        }

        return (
            <g>
                <line x1={loc_x}
                      y1={loc_y}
                      x2={src_loc_x_1}
                      y2={src_loc_y_1}
                      className={'shadowdash'}/>
                <line x1={src_loc_x_2}
                      y1={src_loc_y_2}
                      x2={dest_loc_x}
                      y2={dest_loc_y}
                      className={'shadowdash'}/>
                <line x1={loc_x}
                      y1={loc_y}
                      x2={src_loc_x_1}
                      y2={src_loc_y_1}
                      className={'convoyorder'}
                      stroke={Colors[this.props.powerName]}/>
                <line x1={src_loc_x_2}
                      y1={src_loc_y_2}
                      x2={dest_loc_x}
                      y2={dest_loc_y}
                      className={'convoyorder'}
                      markerEnd={'url(#arrow)'}
                      stroke={Colors[this.props.powerName]}/>
                <polygon className={'shadowdash'}
                         points={triangle_coord.join(' ')}/>
                <polygon className={'convoyorder'}
                         points={triangle_coord.join(' ')}
                         stroke={Colors[this.props.powerName]}/>
            </g>
        );
    }
}

Convoy.propTypes = {
    loc: PropTypes.string.isRequired,
    srcLoc: PropTypes.string.isRequired,
    dstLoc: PropTypes.string.isRequired,
    powerName: PropTypes.string.isRequired,
    coordinates: PropTypes.object.isRequired,
    colors: PropTypes.object.isRequired
};
