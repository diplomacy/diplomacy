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
import $ from "jquery";

const ARMY = 'Army';
const FLEET = 'Fleet';
// SVG tag names.
const PREFIX_TAG = 'jdipNS'.toLowerCase();
const TAG_ORDERDRAWING = 'jdipNS:ORDERDRAWING'.toLowerCase();
const TAG_POWERCOLORS = 'jdipNS:POWERCOLORS'.toLowerCase();
const TAG_POWERCOLOR = 'jdipNS:POWERCOLOR'.toLowerCase();
const TAG_SYMBOLSIZE = 'jdipNS:SYMBOLSIZE'.toLowerCase();
const TAG_PROVINCE_DATA = 'jdipNS:PROVINCE_DATA'.toLowerCase();
const TAG_PROVINCE = 'jdipNS:PROVINCE'.toLowerCase();
const TAG_UNIT = 'jdipNS:UNIT'.toLowerCase();
const TAG_DISLODGED_UNIT = 'jdipNS:DISLODGED_UNIT'.toLowerCase();
const TAG_SUPPLY_CENTER = 'jdipNS:SUPPLY_CENTER'.toLowerCase();
const TAG_DISPLAY = 'jdipNS:DISPLAY'.toLowerCase();

function attr(node, name) {
    return node.attributes[name].value;
}

function offset(floatString, offset) {
    return "" + (parseFloat(floatString) + offset);
}

export class Renderer {
    constructor(svgDomElement, game, mapData) {
        this.svg = svgDomElement;
        this.game = game;
        this.mapData = mapData;
        this.metadata = {
            color: {},
            symbol_size: {},
            orders: {},
            coord: {}
        };
        this.initialInfluences = {};
        this.__load_metadata();
        this.__save_initial_influences();
    }

    __hashed_id(id) {
        return `${id}___${this.svg.parentNode.id}`;
    }

    __svg_element_from_id(id) {
        const hashedID = this.__hashed_id(id);
        const element = this.svg.getElementById(hashedID);
        if (!element)
            throw new Error(`Unable to find ID ${id} (looked for hashed ID ${hashedID})`);
        return element;
    }

    __load_metadata() {
        // Order drawings.
        const order_drawings = this.svg.getElementsByTagName(TAG_ORDERDRAWING);
        if (!order_drawings.length)
            throw new Error('Unable to find order drawings (tag ' + TAG_ORDERDRAWING + ') in SVG map.');
        for (let order_drawing of order_drawings) {
            for (let child_node of order_drawing.childNodes) {
                if (child_node.nodeName === TAG_POWERCOLORS) {
                    // Power colors.
                    for (let power_color of child_node.childNodes) {
                        if (power_color.nodeName === TAG_POWERCOLOR) {
                            this.metadata.color[attr(power_color, 'power').toUpperCase()] = attr(power_color, 'color');
                        }
                    }
                } else if (child_node.nodeName === TAG_SYMBOLSIZE) {
                    // Symbol size.
                    this.metadata.symbol_size[attr(child_node, 'name')] = [attr(child_node, 'height'), attr(child_node, 'width')];
                } else if (child_node.nodeName.startsWith(PREFIX_TAG)) {
                    // Order type.
                    const order_type = child_node.nodeName.replace(PREFIX_TAG + ':', '');
                    this.metadata.orders[order_type] = {};
                    for (let attribute of child_node.attributes) {
                        if (!attribute.name.includes(':')) {
                            this.metadata.orders[order_type][attribute.name] = attribute.value;
                        }
                    }
                }
            }
        }
        // Object coordinates.
        const all_province_data = this.svg.getElementsByTagName(TAG_PROVINCE_DATA);
        if (!all_province_data.length)
            throw new Error('Unable to find province data in SVG map (tag ' + TAG_PROVINCE_DATA + ').');
        for (let province_data of all_province_data) {
            for (let child_node of province_data.childNodes) {
                // Province.
                if (child_node.nodeName === TAG_PROVINCE) {
                    const province = attr(child_node, 'name').toUpperCase().replace('-', '/');
                    this.metadata.coord[province] = {};
                    for (let coord_node of child_node.childNodes) {
                        if (coord_node.nodeName === TAG_UNIT) {
                            this.metadata.coord[province].unit = [attr(coord_node, 'x'), attr(coord_node, 'y')];
                        } else if (coord_node.nodeName === TAG_DISLODGED_UNIT) {
                            this.metadata.coord[province].disl = [attr(coord_node, 'x'), attr(coord_node, 'y')];
                        } else if (coord_node.nodeName === TAG_SUPPLY_CENTER) {
                            this.metadata.coord[province].sc = [attr(coord_node, 'x'), attr(coord_node, 'y')];
                        }
                    }
                }
            }
        }
        // Deleting.
        this.svg.removeChild(this.svg.getElementsByTagName(TAG_DISPLAY)[0]);
        this.svg.removeChild(this.svg.getElementsByTagName(TAG_ORDERDRAWING)[0]);
        this.svg.removeChild(this.svg.getElementsByTagName(TAG_PROVINCE_DATA)[0]);

        // (this code was previously in render())
        // Removing mouse layer.
        this.svg.removeChild(this.__svg_element_from_id('MouseLayer'));
    }

    __save_initial_influences() {
        const mapLayer = this.__svg_element_from_id('MapLayer');
        if (!mapLayer)
            throw new Error('Unable to find map layer.');
        for (let element of mapLayer.childNodes) {
            if (element.tagName === 'path') {
                this.initialInfluences[element.id] = element.getAttribute('class');
            }
        }
    }

    __restore_initial_influences() {
        for (let id of Object.keys(this.initialInfluences)) {
            const className = this.initialInfluences[id];
            this.svg.getElementById(id).setAttribute('class', className);
        }
    }

    __set_current_phase() {
        const current_phase = (this.game.phase[0] === '?' || this.game.phase === 'COMPLETED') ? 'FINAL' : this.game.phase;
        const phase_display = this.__svg_element_from_id('CurrentPhase');
        if (phase_display) {
            phase_display.childNodes[0].nodeValue = current_phase;
        }
    }

    __set_note(note1, note2) {
        note1 = note1 || '';
        note2 = note2 || '';
        const display_note1 = this.__svg_element_from_id('CurrentNote');
        const display_note2 = this.__svg_element_from_id('CurrentNote2');
        if (display_note1)
            display_note1.childNodes[0].nodeValue = note1;
        if (display_note2)
            display_note2.childNodes[0].nodeValue = note2;
    }

    __add_unit(unit, power_name, is_dislogged) {
        const split_unit = unit.split(/ +/);
        const unit_type = split_unit[0];
        const loc = split_unit[1];
        const dislogged_type = is_dislogged ? 'disl' : 'unit';
        const symbol = unit_type === 'F' ? FLEET : ARMY;
        const loc_x = offset(this.metadata.coord[loc][dislogged_type][0], -11.5);
        const loc_y = offset(this.metadata.coord[loc][dislogged_type][1], -10.0);
        // Helpful link about creating SVG elements: https://stackoverflow.com/a/25949237
        const node = document.createElementNS("http://www.w3.org/2000/svg", 'use');
        node.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#' + this.__hashed_id((is_dislogged ? 'Dislodged' : '') + symbol));
        node.setAttribute('x', loc_x);
        node.setAttribute('y', loc_y);
        node.setAttribute('height', this.metadata.symbol_size[symbol][0]);
        node.setAttribute('width', this.metadata.symbol_size[symbol][1]);
        node.setAttribute('class', 'unit' + power_name.toLowerCase());
        node.setAttribute('diplomacyUnit', loc);
        const parent_node = this.__svg_element_from_id(is_dislogged ? 'DislodgedUnitLayer' : 'UnitLayer');
        if (parent_node)
            parent_node.appendChild(node);
    }

    __add_supply_center(loc, power_name) {
        const symbol = 'SupplyCenter';
        const loc_x = offset(this.metadata.coord[loc]['sc'][0], -8.5);
        const loc_y = offset(this.metadata.coord[loc]['sc'][1], -11.0);
        const node = document.createElementNS("http://www.w3.org/2000/svg", 'use');
        node.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#' + this.__hashed_id(symbol));
        node.setAttribute('x', loc_x);
        node.setAttribute('y', loc_y);
        node.setAttribute('height', this.metadata.symbol_size[symbol][0]);
        node.setAttribute('width', this.metadata.symbol_size[symbol][1]);
        node.setAttribute('class', power_name ? ('sc' + power_name.toLowerCase()) : 'scnopower');
        const parent_node = this.__svg_element_from_id('SupplyCenterLayer');
        if (parent_node)
            parent_node.appendChild(node);
    }

    __set_influence(loc, power_name) {
        loc = loc.toUpperCase().substr(0, 3);
        if (!['LAND', 'COAST'].includes(this.mapData.getProvince(loc).type))
            return;
        const path = this.__svg_element_from_id('_' + loc.toLowerCase());
        if (!path || path.nodeName !== 'path') {
            throw new Error(`Unable to find SVG path for loc ${loc}, got ${path ? path.nodeName : '(nothing)'}`);
        }
        path.setAttribute('class', power_name ? power_name.toLowerCase() : 'nopower');
    }

    issueHoldOrder(loc, power_name) {
        const polygon_coord = [];
        const loc_x = offset(this.metadata['coord'][loc]['unit'][0], 8.5);
        const loc_y = offset(this.metadata['coord'][loc]['unit'][1], 9.5);
        for (let ofs of [
            [13.8, -33.3], [33.3, -13.8], [33.3, 13.8], [13.8, 33.3], [-13.8, 33.3],
            [-33.3, 13.8], [-33.3, -13.8], [-13.8, -33.3]]
            ) {
            polygon_coord.push(offset(loc_x, ofs[0]) + ',' + offset(loc_y, ofs[1]));
        }
        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const poly_1 = document.createElementNS("http://www.w3.org/2000/svg", 'polygon');
        const poly_2 = document.createElementNS("http://www.w3.org/2000/svg", 'polygon');
        poly_1.setAttribute('stroke-width', '10');
        poly_1.setAttribute('class', 'varwidthshadow');
        poly_1.setAttribute('points', polygon_coord.join(' '));
        poly_2.setAttribute('stroke-width', '6');
        poly_2.setAttribute('class', 'varwidthorder');
        poly_2.setAttribute('points', polygon_coord.join(' '));
        poly_2.setAttribute('stroke', this.metadata['color'][power_name]);
        g_node.appendChild(poly_1);
        g_node.appendChild(poly_2);
        const orderLayer = this.__svg_element_from_id('Layer1');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    issueMoveOrder(src_loc, dest_loc, power_name) {
        let src_loc_x = 0;
        let src_loc_y = 0;
        const phaseType = this.game.getPhaseType();
        if (phaseType === 'R') {
            src_loc_x = offset(this.metadata.coord[src_loc]['unit'][0], -2.5);
            src_loc_y = offset(this.metadata.coord[src_loc]['unit'][1], -2.5);
        } else {
            src_loc_x = offset(this.metadata.coord[src_loc]['unit'][0], 10);
            src_loc_y = offset(this.metadata.coord[src_loc]['unit'][1], 10);
        }
        let dest_loc_x = offset(this.metadata.coord[dest_loc]['unit'][0], 10);
        let dest_loc_y = offset(this.metadata.coord[dest_loc]['unit'][1], 10);

        // Adjusting destination
        const delta_x = parseFloat(dest_loc_x) - parseFloat(src_loc_x);
        const delta_y = parseFloat(dest_loc_y) - parseFloat(src_loc_y);
        const vector_length = Math.sqrt(delta_x * delta_x + delta_y * delta_y);
        dest_loc_x = '' + Math.round((parseFloat(src_loc_x) + (vector_length - 30.) / vector_length * delta_x) * 100.) / 100.;
        dest_loc_y = '' + Math.round((parseFloat(src_loc_y) + (vector_length - 30.) / vector_length * delta_y) * 100.) / 100.;

        // Creating nodes.
        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const line_with_shadow = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const line_with_arrow = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        line_with_shadow.setAttribute('x1', src_loc_x);
        line_with_shadow.setAttribute('y1', src_loc_y);
        line_with_shadow.setAttribute('x2', dest_loc_x);
        line_with_shadow.setAttribute('y2', dest_loc_y);
        line_with_shadow.setAttribute('class', 'varwidthshadow');
        line_with_shadow.setAttribute('stroke-width', '10');
        line_with_arrow.setAttribute('x1', src_loc_x);
        line_with_arrow.setAttribute('y1', src_loc_y);
        line_with_arrow.setAttribute('x2', dest_loc_x);
        line_with_arrow.setAttribute('y2', dest_loc_y);
        line_with_arrow.setAttribute('class', 'varwidthorder');
        line_with_arrow.setAttribute('marker-end', 'url(#' + this.__hashed_id('arrow') + ')');
        line_with_arrow.setAttribute('stroke', this.metadata.color[power_name]);
        line_with_arrow.setAttribute('stroke-width', '6');
        g_node.appendChild(line_with_shadow);
        g_node.appendChild(line_with_arrow);
        const orderLayer = this.__svg_element_from_id('Layer1');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    issueSupportMoveOrder(loc, src_loc, dest_loc, power_name) {
        const loc_x = offset(this.metadata['coord'][loc]['unit'][0], 10);
        const loc_y = offset(this.metadata['coord'][loc]['unit'][1], 10);
        const src_loc_x = offset(this.metadata['coord'][src_loc]['unit'][0], 10);
        const src_loc_y = offset(this.metadata['coord'][src_loc]['unit'][1], 10);
        let dest_loc_x = offset(this.metadata['coord'][dest_loc]['unit'][0], 10);
        let dest_loc_y = offset(this.metadata['coord'][dest_loc]['unit'][1], 10);

        // Adjusting destination
        const delta_x = parseFloat(dest_loc_x) - parseFloat(src_loc_x);
        const delta_y = parseFloat(dest_loc_y) - parseFloat(src_loc_y);
        const vector_length = Math.sqrt(delta_x * delta_x + delta_y * delta_y);
        dest_loc_x = '' + Math.round((parseFloat(src_loc_x) + (vector_length - 30.) / vector_length * delta_x) * 100.) / 100.;
        dest_loc_y = '' + Math.round((parseFloat(src_loc_y) + (vector_length - 30.) / vector_length * delta_y) * 100.) / 100.;

        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const path_with_shadow = document.createElementNS("http://www.w3.org/2000/svg", 'path');
        const path_with_arrow = document.createElementNS("http://www.w3.org/2000/svg", 'path');
        path_with_shadow.setAttribute('class', 'shadowdash');
        path_with_shadow.setAttribute('d', `M ${loc_x},${loc_y} C ${src_loc_x},${src_loc_y} ${src_loc_x},${src_loc_y} ${dest_loc_x},${dest_loc_y}`);
        path_with_arrow.setAttribute('class', 'supportorder');
        path_with_arrow.setAttribute('marker-end', 'url(#' + this.__hashed_id('arrow') + ')');
        path_with_arrow.setAttribute('stroke', this.metadata['color'][power_name]);
        path_with_arrow.setAttribute('d', `M ${loc_x},${loc_y} C ${src_loc_x},${src_loc_y} ${src_loc_x},${src_loc_y} ${dest_loc_x},${dest_loc_y}`);
        g_node.appendChild(path_with_shadow);
        g_node.appendChild(path_with_arrow);
        const orderLayer = this.__svg_element_from_id('Layer2');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    issueSupportHoldOrder(loc, dest_loc, power_name) {
        const loc_x = offset(this.metadata['coord'][loc]['unit'][0], 10);
        const loc_y = offset(this.metadata['coord'][loc]['unit'][1], 10);
        let dest_loc_x = offset(this.metadata['coord'][dest_loc]['unit'][0], 10);
        let dest_loc_y = offset(this.metadata['coord'][dest_loc]['unit'][1], 10);

        const delta_x = parseFloat(dest_loc_x) - parseFloat(loc_x);
        const delta_y = parseFloat(dest_loc_y) - parseFloat(loc_y);
        const vector_length = Math.sqrt(delta_x * delta_x + delta_y * delta_y);
        dest_loc_x = '' + Math.round((parseFloat(loc_x) + (vector_length - 35.) / vector_length * delta_x) * 100.) / 100.;
        dest_loc_y = '' + Math.round((parseFloat(loc_y) + (vector_length - 35.) / vector_length * delta_y) * 100.) / 100.;

        const polygon_coord = [];
        const poly_loc_x = offset(this.metadata['coord'][dest_loc]['unit'][0], 8.5);
        const poly_loc_y = offset(this.metadata['coord'][dest_loc]['unit'][1], 9.5);
        for (let ofs of [
            [15.9, -38.3], [38.3, -15.9], [38.3, 15.9], [15.9, 38.3], [-15.9, 38.3], [-38.3, 15.9],
            [-38.3, -15.9], [-15.9, -38.3]
        ]) {
            polygon_coord.push(offset(poly_loc_x, ofs[0]) + ',' + offset(poly_loc_y, ofs[1]));
        }
        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const shadow_line = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const support_line = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const shadow_poly = document.createElementNS("http://www.w3.org/2000/svg", 'polygon');
        const support_poly = document.createElementNS("http://www.w3.org/2000/svg", 'polygon');
        shadow_line.setAttribute('x1', loc_x);
        shadow_line.setAttribute('y1', loc_y);
        shadow_line.setAttribute('x2', dest_loc_x);
        shadow_line.setAttribute('y2', dest_loc_y);
        shadow_line.setAttribute('class', 'shadowdash');
        support_line.setAttribute('x1', loc_x);
        support_line.setAttribute('y1', loc_y);
        support_line.setAttribute('x2', dest_loc_x);
        support_line.setAttribute('y2', dest_loc_y);
        support_line.setAttribute('class', 'supportorder');
        support_line.setAttribute('stroke', this.metadata['color'][power_name]);
        shadow_poly.setAttribute('class', 'shadowdash');
        shadow_poly.setAttribute('points', polygon_coord.join(' '));
        support_poly.setAttribute('class', 'supportorder');
        support_poly.setAttribute('points', polygon_coord.join(' '));
        support_poly.setAttribute('stroke', this.metadata['color'][power_name]);
        g_node.appendChild(shadow_line);
        g_node.appendChild(support_line);
        g_node.appendChild(shadow_poly);
        g_node.appendChild(support_poly);
        const orderLayer = this.__svg_element_from_id('Layer2');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    issueConvoyOrder(loc, src_loc, dest_loc, power_name) {
        const loc_x = offset(this.metadata['coord'][loc]['unit'][0], 10);
        const loc_y = offset(this.metadata['coord'][loc]['unit'][1], 10);
        const src_loc_x = offset(this.metadata['coord'][src_loc]['unit'][0], 10);
        const src_loc_y = offset(this.metadata['coord'][src_loc]['unit'][1], 10);
        let dest_loc_x = offset(this.metadata['coord'][dest_loc]['unit'][0], 10);
        let dest_loc_y = offset(this.metadata['coord'][dest_loc]['unit'][1], 10);

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
        const triangle_loc_x = offset(this.metadata['coord'][src_loc]['unit'][0], 10);
        const triangle_loc_y = offset(this.metadata['coord'][src_loc]['unit'][1], 10);
        for (let ofs of [[0, -38.3], [33.2, 19.1], [-33.2, 19.1]]) {
            triangle_coord.push(offset(triangle_loc_x, ofs[0]) + ',' + offset(triangle_loc_y, ofs[1]));
        }

        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const src_shadow_line = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const dest_shadow_line = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const src_convoy_line = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const dest_convoy_line = document.createElementNS("http://www.w3.org/2000/svg", 'line');
        const shadow_poly = document.createElementNS("http://www.w3.org/2000/svg", 'polygon');
        const convoy_poly = document.createElementNS("http://www.w3.org/2000/svg", 'polygon');
        src_shadow_line.setAttribute('x1', loc_x);
        src_shadow_line.setAttribute('y1', loc_y);
        src_shadow_line.setAttribute('x2', src_loc_x_1);
        src_shadow_line.setAttribute('y2', src_loc_y_1);
        src_shadow_line.setAttribute('class', 'shadowdash');

        dest_shadow_line.setAttribute('x1', src_loc_x_2);
        dest_shadow_line.setAttribute('y1', src_loc_y_2);
        dest_shadow_line.setAttribute('x2', dest_loc_x);
        dest_shadow_line.setAttribute('y2', dest_loc_y);
        dest_shadow_line.setAttribute('class', 'shadowdash');

        src_convoy_line.setAttribute('x1', loc_x);
        src_convoy_line.setAttribute('y1', loc_y);
        src_convoy_line.setAttribute('x2', src_loc_x_1);
        src_convoy_line.setAttribute('y2', src_loc_y_1);
        src_convoy_line.setAttribute('class', 'convoyorder');
        src_convoy_line.setAttribute('stroke', this.metadata['color'][power_name]);

        dest_convoy_line.setAttribute('x1', src_loc_x_2);
        dest_convoy_line.setAttribute('y1', src_loc_y_2);
        dest_convoy_line.setAttribute('x2', dest_loc_x);
        dest_convoy_line.setAttribute('y2', dest_loc_y);
        dest_convoy_line.setAttribute('class', 'convoyorder');
        dest_convoy_line.setAttribute('marker-end', 'url(#' + this.__hashed_id('arrow') + ')');

        dest_convoy_line.setAttribute('stroke', this.metadata['color'][power_name]);

        shadow_poly.setAttribute('class', 'shadowdash');
        shadow_poly.setAttribute('points', triangle_coord.join(' '));

        convoy_poly.setAttribute('class', 'convoyorder');
        convoy_poly.setAttribute('points', triangle_coord.join(' '));
        convoy_poly.setAttribute('stroke', this.metadata['color'][power_name]);

        g_node.appendChild(src_shadow_line);
        g_node.appendChild(dest_shadow_line);
        g_node.appendChild(src_convoy_line);
        g_node.appendChild(dest_convoy_line);
        g_node.appendChild(shadow_poly);
        g_node.appendChild(convoy_poly);

        const orderLayer = this.__svg_element_from_id('Layer2');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    issueBuildOrder(unit_type, loc, power_name) {
        const loc_x = offset(this.metadata['coord'][loc]['unit'][0], -11.5);
        const loc_y = offset(this.metadata['coord'][loc]['unit'][1], -10.);
        const build_loc_x = offset(this.metadata['coord'][loc]['unit'][0], -20.5);
        const build_loc_y = offset(this.metadata['coord'][loc]['unit'][1], -20.5);
        const symbol = unit_type === 'A' ? ARMY : FLEET;
        const build_symbol = 'BuildUnit';
        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const symbol_node = document.createElementNS("http://www.w3.org/2000/svg", 'use');
        const build_node = document.createElementNS("http://www.w3.org/2000/svg", 'use');
        symbol_node.setAttribute('x', loc_x);
        symbol_node.setAttribute('y', loc_y);
        symbol_node.setAttribute('height', this.metadata['symbol_size'][symbol][0]);
        symbol_node.setAttribute('width', this.metadata['symbol_size'][symbol][1]);
        symbol_node.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#' + this.__hashed_id(symbol));
        symbol_node.setAttribute('class', `unit${power_name.toLowerCase()}`);
        build_node.setAttribute('x', build_loc_x);
        build_node.setAttribute('y', build_loc_y);
        build_node.setAttribute('height', this.metadata['symbol_size'][build_symbol][0]);
        build_node.setAttribute('width', this.metadata['symbol_size'][build_symbol][1]);
        build_node.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#' + this.__hashed_id(build_symbol));
        g_node.appendChild(build_node);
        g_node.appendChild(symbol_node);
        const orderLayer = this.__svg_element_from_id('HighestOrderLayer');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    issueDisbandOrder(loc) {
        const phaseType = this.game.getPhaseType();
        let loc_x = 0;
        let loc_y = 0;
        if (phaseType === 'R') {
            loc_x = offset(this.metadata['coord'][loc]['unit'][0], -29.);
            loc_y = offset(this.metadata['coord'][loc]['unit'][1], -27.5);
        } else {
            loc_x = offset(this.metadata['coord'][loc]['unit'][0], -16.5);
            loc_y = offset(this.metadata['coord'][loc]['unit'][1], -15.);
        }
        const symbol = 'RemoveUnit';
        const g_node = document.createElementNS("http://www.w3.org/2000/svg", 'g');
        const symbol_node = document.createElementNS("http://www.w3.org/2000/svg", 'use');
        symbol_node.setAttribute('x', loc_x);
        symbol_node.setAttribute('y', loc_y);
        symbol_node.setAttribute('height', this.metadata['symbol_size'][symbol][0]);
        symbol_node.setAttribute('width', this.metadata['symbol_size'][symbol][1]);
        symbol_node.setAttributeNS('http://www.w3.org/1999/xlink', 'href', '#' + this.__hashed_id(symbol));
        g_node.appendChild(symbol_node);
        const orderLayer = this.__svg_element_from_id('HighestOrderLayer');
        if (!orderLayer)
            throw new Error(`Unable to find svg order layer.`);
        orderLayer.appendChild(g_node);
    }

    clear() {
        this.__set_note('', '');
        $(`#${this.__hashed_id('DislodgedUnitLayer')} use`).remove();
        $(`#${this.__hashed_id('UnitLayer')} use`).remove();
        $(`#${this.__hashed_id('SupplyCenterLayer')} use`).remove();
        $(`#${this.__hashed_id('Layer1')} g`).remove();
        $(`#${this.__hashed_id('Layer2')} g`).remove();
        $(`#${this.__hashed_id('HighestOrderLayer')} g`).remove();
        this.__restore_initial_influences();
    }

    render(includeOrders, orders) {
        // Setting phase and note.
        const nb_centers = [];
        for (let power of Object.values(this.game.powers)) {
            if (!power.isEliminated())
                nb_centers.push([power.name.substr(0, 3), power.centers.length]);
        }
        // Sort nb_centers by descending number of centers.
        nb_centers.sort((a, b) => {
            return -(a[1] - b[1]) || a[0].localeCompare(b[0]);
        });
        const nb_centers_per_power = nb_centers.map((couple) => (couple[0] + ': ' + couple[1])).join(' ');
        this.__set_current_phase();
        this.__set_note(nb_centers_per_power, this.game.note);

        // Adding units, supply centers, influence and orders.
        const scs = new Set(this.mapData.supplyCenters);
        for (let power of Object.values(this.game.powers)) {
            for (let unit of power.units)
                this.__add_unit(unit, power.name, false);
            for (let unit of Object.keys(power.retreats))
                this.__add_unit(unit, power.name, true);
            for (let center of power.centers) {
                this.__add_supply_center(center, power.name);
                this.__set_influence(center, power.name);
                scs.delete(center);
            }
            if (!power.isEliminated()) {
                for (let loc of power.influence) {
                    if (!this.mapData.supplyCenters.has(loc))
                        this.__set_influence(loc, power.name);
                }
            }

            if (includeOrders) {
                const powerOrders = (orders && orders.hasOwnProperty(power.name) && orders[power.name]) || [];
                for (let order of powerOrders) {
                    const tokens = order.split(/ +/);
                    if (!tokens || tokens.length < 3)
                        continue;
                    const unit_loc = tokens[1];
                    if (tokens[2] === 'H')
                        this.issueHoldOrder(unit_loc, power.name);
                    else if (tokens[2] === '-') {
                        const destLoc = tokens[tokens.length - (tokens[tokens.length - 1] === 'VIA' ? 2 : 1)];
                        this.issueMoveOrder(unit_loc, destLoc, power.name);
                    } else if (tokens[2] === 'S') {
                        const destLoc = tokens[tokens.length - 1];
                        if (tokens.includes('-')) {
                            const srcLoc = tokens[4];
                            this.issueSupportMoveOrder(unit_loc, srcLoc, destLoc, power.name);
                        } else {
                            this.issueSupportHoldOrder(unit_loc, destLoc, power.name);
                        }
                    } else if (tokens[2] === 'C') {
                        const srcLoc = tokens[4];
                        const destLoc = tokens[tokens.length - 1];
                        if ((srcLoc !== destLoc) && (tokens.includes('-'))) {
                            this.issueConvoyOrder(unit_loc, srcLoc, destLoc, power.name);
                        }
                    } else if (tokens[2] === 'B') {
                        this.issueBuildOrder(tokens[0], unit_loc, power.name);
                    } else if (tokens[2] === 'D') {
                        this.issueDisbandOrder(unit_loc);
                    } else if (tokens[2] === 'R') {
                        const srcLoc = tokens[1];
                        const destLoc = tokens[3];
                        this.issueMoveOrder(srcLoc, destLoc, power.name);
                    } else {
                        throw new Error(`Unknown error to render (${order}).`);
                    }
                }
            }
        }
        // Adding remaining supply centers.
        for (let remainingCenter of scs)
            this.__add_supply_center(remainingCenter, null);
    }

    update(game, mapData, showOrders, orders) {
        this.game = game;
        this.mapData = mapData;
        this.clear();
        this.render(showOrders, orders);
    }
}
