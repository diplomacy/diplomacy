# ==============================================================================
# Copyright (C) 2019 - Philip Paquette, Steven Bocco
#
#  This program is free software: you can redistribute it and/or modify it under
#  the terms of the GNU Affero General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
#  details.
#
#  You should have received a copy of the GNU Affero General Public License along
#  with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
""" Helper script to convert a SVG file into a React JS component file.
    Type `python <script name> --help` for help.
"""
import argparse
import os
import re
import sys
from xml.dom import minidom, Node

import ujson as json

LICENSE_TEXT = """/**
==============================================================================
Copyright (C) 2019 - Philip Paquette, Steven Bocco

 This program is free software: you can redistribute it and/or modify it under
 the terms of the GNU Affero General Public License as published by the Free
 Software Foundation, either version 3 of the License, or (at your option) any
 later version.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
 details.

 You should have received a copy of the GNU Affero General Public License along
 with this program.  If not, see <https:www.gnu.org/licenses/>.
==============================================================================
**/"""

SELECTOR_REGEX = re.compile(r'([\r\n][ \t]*)([^{\r\n]+){')


def prepend_css_selectors(prefix, css_text):
    def repl(match):
        if match.group(2).startswith('.sym'):
            return match.group(0)
        return '%s%s %s{' % (match.group(1), prefix, match.group(2))

    return SELECTOR_REGEX.sub(repl, css_text)


class ExtractedData:
    __slots__ = ('name', 'extra', 'style_lines', 'id_to_class')

    def __init__(self, name):
        self.name = name
        self.extra = {}
        self.style_lines = []
        self.id_to_class = {}


def safe_react_attribute_name(name):
    """ Convert given raw attribute name into a valid React HTML tag attribute name.
        :param name: attribute to convert
        :return: valid attribute
        :type name: str
        :rtype: str
    """
    # Replace 'class' with 'className'
    if name == 'class':
        return 'className'
    # Replace aa-bb-cc with aaBbCc.
    if '-' in name:
        input_pieces = name.split('-')
        output_pieces = [input_pieces[0]]
        for piece in input_pieces[1:]:
            output_pieces.append('%s%s' % (piece[0].upper(), piece[1:]))
        return ''.join(output_pieces)
    # Otherwise, return name as-is.
    return name


def compact_extra(extra):
    """ Compact extra dictionary so that it takes less place into final output string.
        :param extra: dictionary of extra data
        :type extra: dict
    """
    if 'children' in extra:
        names = set()
        text_found = False
        for child in extra['children']:
            if isinstance(child, str):
                text_found = True
            else:
                names.add(child['name'])
        if len(names) == len(extra['children']):
            # Each child has a different name, so they cannot be confused, and extra dictionary can be merged with them.
            children_dict = {}
            for child in extra['children']:
                child_name = child.pop('name')
                compact_extra(child)
                children_dict[child_name] = child
            extra.pop('children')
            extra.update(children_dict)
        elif not text_found:
            # Classify children by name.
            classed = {}
            for child in extra['children']:
                classed.setdefault(child['name'], []).append(child)
            # Remove extra['children']
            extra.pop('children')
            for name, children in classed.items():
                if len(children) == 1:
                    # This child is the only one with that name. Merge it with extra dictionary.
                    child = children[0]
                    child.pop('name')
                    compact_extra(child)
                    extra[name] = child
                else:
                    # We found many children with same name. Merge them as a list into extra dictionary.
                    values = []
                    for child in children:
                        child.pop('name')
                        compact_extra(child)
                        values.append(child)
                    extra[name] = values
        else:
            for child in extra['children']:
                compact_extra(child)
    if 'attributes' in extra:
        if not extra['attributes']:
            extra.pop('attributes')
        elif 'name' not in extra or 'name' not in extra['attributes']:
            # Dictionary can be merged with its 'attributes' field.
            extra.update(extra.pop('attributes'))


def extract_extra(node, extra):
    """ Collect extra information from given node into output extra.
        :type extra: dict
    """
    extra_dictionary = {'name': node.tagName, 'attributes': {}, 'children': []}
    # Collect attributes.
    for attribute_index in range(node.attributes.length):
        attribute = node.attributes.item(attribute_index)
        extra_dictionary['attributes'][attribute.name] = attribute.value
    # Collect children lines.
    for child in node.childNodes:
        if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
            # Child is a text.
            text = child.data.strip()
            if text:
                extra_dictionary['children'].append(text)
        else:
            # Child is a normal node. We still consider it as an extra node.
            extract_extra(child, extra_dictionary)
    # Save extra node data into list field extra['children'].
    extra.setdefault('children', []).append(extra_dictionary)


def attributes_to_string(attributes):
    """ Convert given HTML attributes ton an inline string.
        :param attributes: attributes to write
        :return: a string representing attributes
        :type attributes: dict
        :rtype: str
    """
    pieces = []
    for name in sorted(attributes):
        value = attributes[name]
        if value.startswith('{'):
            pieces.append('%s=%s' % (name, value))
        else:
            pieces.append('%s="%s"' % (name, value))
    return ' '.join(pieces)


def extract_dom(node, nb_indentation, lines, data):
    """ Parse given node.
        :param node: (input) node to parse
        :param nb_indentation: (input) number of indentation to use for current node content into output lines
            1 indentation is converted to 4 spaces.
        :param lines: (output) lines to collect output lines of text corresponding to parsed content
        :param data: ExtractedData object to collect extracted data (extra, style lines, ID-to-class mapping).
        :type nb_indentation: int
        :type lines: List[str]
        :type data: ExtractedData
    """
    if node.nodeType != Node.ELEMENT_NODE:
        return
    tag_name = node.tagName
    if ':' in tag_name:
        # Found unhandled tag (example: `<jdipNS:DISPLAY>`). Collect it (and all its descendants) into extra.
        extract_extra(node, data.extra)
    else:
        # Found valid tag.
        attributes = {}
        child_lines = []
        node_id = None
        node_class = None
        # Collect attributes.
        for attribute_index in range(node.attributes.length):
            attribute = node.attributes.item(attribute_index)
            attribute_name = safe_react_attribute_name(attribute.name)
            # Attributes "xmlns:*" are not handled by React. Skip them.
            if not attribute_name.startswith('xmlns:') and attribute_name != 'version':
                attributes[attribute_name] = attribute.value
                if attribute_name == 'id':
                    node_id = attribute.value
                elif attribute_name == 'className':
                    node_class = attribute.value
        if node_id:
            if node_class:
                # We parameterize class name for this node.
                attributes['className'] = "{classes['%s']}" % node_id
                data.id_to_class[node_id] = node_class
            if node.parentNode.getAttribute('id') == 'MouseLayer':
                # This node must react to onClick and onMouseOver.
                attributes['onClick'] = '{this.onClick}'
                attributes['onMouseOver'] = '{this.onHover}'
        # Collect children lines.
        for child in node.childNodes:
            if child.nodeType in (Node.TEXT_NODE, Node.CDATA_SECTION_NODE):
                # Found a text node.
                text = child.data.strip()
                if text:
                    child_lines.append(text)
            else:
                # Found an element node.
                extract_dom(child, nb_indentation + 1, child_lines, data)
        if tag_name == 'style':
            # Found 'style' tag. Save its children lines into style lines and return immediately,
            data.style_lines.extend(child_lines)
            return
        if tag_name == 'svg':
            if node_class:
                attributes['className'] += ' %s' % data.name
            else:
                attributes['className'] = data.name
        if node_id:
            if not child_lines:
                if node_id == 'SupplyCenterLayer':
                    child_lines.append('{renderedSupplyCenters}')
                elif node_id == 'Layer2':
                    child_lines.append('{renderedOrders2}')
                elif node_id == 'Layer1':
                    child_lines.append('{renderedOrders}')
                elif node_id == 'UnitLayer':
                    child_lines.append('{renderedUnits}')
                elif node_id == 'DislodgedUnitLayer':
                    child_lines.append('{renderedDislodgedUnits}')
                elif node_id == 'HighestOrderLayer':
                    child_lines.append('{renderedHighestOrders}')
                elif node_id == 'CurrentNote':
                    child_lines.append("{nb_centers_per_power ? nb_centers_per_power : ''}")
                elif node_id == 'CurrentNote2':
                    child_lines.append("{note ? note : ''}")
            if node_id == 'CurrentPhase' and len(child_lines) == 1 and isinstance(child_lines[0], str):
                child_lines = ['{current_phase}']
        # We have a normal element node (not style node). Convert it to output lines.
        indentation = ' ' * (4 * nb_indentation)
        attributes_string = attributes_to_string(attributes)
        if child_lines:
            # Node must be written as an open tag.
            if len(child_lines) == 1:
                # If we just have 1 child line, write a compact line.
                lines.append(
                    '%s<%s%s>%s</%s>' % (
                        indentation, tag_name, (' %s' % attributes_string) if attributes_string else '',
                        child_lines[0].lstrip(),
                        tag_name))
            else:
                # Otherwise, write node normally.
                lines.append(
                    '%s<%s%s>' % (indentation, tag_name, (' %s' % attributes_string) if attributes_string else ''))
                lines.extend(child_lines)
                lines.append('%s</%s>' % (indentation, tag_name))
        else:
            # Node can be written as a close tag.
            lines.append(
                '%s<%s%s/>' % (indentation, tag_name, (' %s' % attributes_string) if attributes_string else ''))


def main():
    """ Main script function. """
    parser = argparse.ArgumentParser(
        prog='Convert a SVG file to a React Component.'
    )
    parser.add_argument('--input', '-i', type=str, required=True, help='SVG file to convert.')
    parser.add_argument('--name', '-n', type=str, required=True, help="Component name.")
    parser.add_argument('--output', '-o', type=str, default=os.getcwd(),
                        help='Output folder (default to working folder).')
    args = parser.parse_args()
    root = minidom.parse(args.input).documentElement
    class_name = args.name
    output_folder = args.output
    assert os.path.isdir(output_folder), 'Not a directory: %s' % output_folder
    extra_class_name = '%sExtra' % class_name
    lines = []
    data = ExtractedData(class_name)
    extract_dom(root, 3, lines, data)
    compact_extra(data.extra)

    output_file_name = os.path.join(output_folder, '%s.js' % class_name)
    style_file_name = os.path.join(output_folder, '%s.css' % class_name)
    extra_file_name = os.path.join(output_folder, '%s.js' % extra_class_name)
    extra_parsed_file_name = os.path.join(output_folder, '%sParsed.js' % extra_class_name)

    if data.style_lines:
        with open(style_file_name, 'w') as style_file:
            style_file.write(LICENSE_TEXT)
            style_file.write('\n')
            style_file.writelines(prepend_css_selectors('.%s' % class_name, '\n'.join(data.style_lines)))

    if data.extra:
        with open(extra_file_name, 'w') as extra_file:
            extra_file.write("""%(license_text)s
export const %(extra_class_name)s = %(extra_content)s;
            """ % {
                'extra_class_name': extra_class_name,
                'extra_content': json.dumps(data.extra, indent=4),
                'license_text': LICENSE_TEXT
            })

        with open(extra_parsed_file_name, 'w') as extra_parsed_file:
            extra_parsed_file.write("""%(license_text)s
import {%(extra_class_name)s} from "./%(extra_class_name)s";
import {getColors, getCoordinates, getSymbolSizes} from "../common/common";

export const Coordinates = getCoordinates(%(extra_class_name)s);
export const SymbolSizes = getSymbolSizes(%(extra_class_name)s);
export const Colors = getColors(%(extra_class_name)s);
""" % {
                'license_text': LICENSE_TEXT,
                'extra_class_name': extra_class_name
            })

    with open(output_file_name, 'w') as file:
        file.write("""%(license_text)s
/** Generated using %(program_name)s with parameters:
%(args)s
**/
import React from 'react';
import PropTypes from 'prop-types';
%(style_content)s
%(extra_content)s
import {getClickedID, parseLocation, setInfluence} from "../common/common";
import {Game} from "../../../diplomacy/engine/game";
import {MapData} from "../../utils/map_data";
import {UTILS} from "../../../diplomacy/utils/utils";
import {Diplog} from "../../../diplomacy/utils/diplog";
import {extendOrderBuilding} from "../../utils/order_building";
import {Unit} from "../common/unit";
import {SupplyCenter} from "../common/supplyCenter";
import {Hold} from "../common/hold";
import {Move} from "../common/move";
import {SupportMove} from "../common/supportMove";
import {SupportHold} from "../common/supportHold";
import {Convoy} from "../common/convoy";
import {Build} from "../common/build";
import {Disband} from "../common/disband";

export class %(classname)s extends React.Component {
    constructor(props) {
        super(props);
        this.onClick = this.onClick.bind(this);
        this.onHover = this.onHover.bind(this);
    }
    onClick(event) {
        if (this.props.orderBuilding)
            return this.handleClickedID(getClickedID(event));
    }
    onHover(event) {
        return this.handleHoverID(getClickedID(event));
    }
    handleClickedID(id) {
        const orderBuilding = this.props.orderBuilding;
        if (!orderBuilding.builder)
            return this.props.onError('No orderable locations.');
        const province = this.props.mapData.getProvince(id);
        if (!province)
            return;

        const stepLength = orderBuilding.builder.steps.length;
        if (orderBuilding.path.length >= stepLength)
            throw new Error(`Order building: current steps count (${orderBuilding.path.length}) should be less than` +
                ` expected steps count (${stepLength}) (${orderBuilding.path.join(', ')}).`);

        const lengthAfterClick = orderBuilding.path.length + 1;
        let validLocations = [];
        const testedPath = [orderBuilding.type].concat(orderBuilding.path);
        const value = UTILS.javascript.getTreeValue(this.props.game.ordersTree, testedPath);
        if (value !== null) {
            const checker = orderBuilding.builder.steps[lengthAfterClick - 1];
            try {
                const possibleLocations = checker(province, orderBuilding.power);
                for (let possibleLocation of possibleLocations) {
                    possibleLocation = possibleLocation.toUpperCase();
                    if (value.includes(possibleLocation))
                        validLocations.push(possibleLocation);
                }
            } catch (error) {
                return this.props.onError(error);
            }
        }
        if (!validLocations.length)
            return this.props.onError('Disallowed.');

        if (validLocations.length > 1 && orderBuilding.type === 'S' && orderBuilding.path.length >= 2) {
            // We are building a support order and we have a multiple choice for a location.
            // Let's check if next location to choose is a coast. To have a coast:
            // - all possible locations must start with same 3 characters.
            // - we expect at least province name in possible locations (e.g. 'SPA' for 'SPA/NC').
            // If we have a coast, we will remove province name from possible locations.
            let isACoast = true;
            let validLocationsNoProvinceName = [];
            for (let i = 0; i < validLocations.length; ++i) {
                let location = validLocations[i];
                if (i > 0) {
                    // Compare 3 first letters with previous location.
                    if (validLocations[i - 1].substring(0, 3).toUpperCase() !== validLocations[i].substring(0, 3).toUpperCase()) {
                        // No same prefix with previous location. We does not have a coast.
                        isACoast = false;
                        break;
                    }
                }
                if (location.length !== 3)
                    validLocationsNoProvinceName.push(location);
            }
            if (validLocations.length === validLocationsNoProvinceName.length) {
                // We have not found province name.
                isACoast = false;
            }
            if (isACoast) {
                // We want to choose location in a coastal province. Let's remove province name.
                validLocations = validLocationsNoProvinceName;
            }
        }

        if (validLocations.length > 1) {
            if (this.props.onSelectLocation) {
                return this.props.onSelectLocation(validLocations, orderBuilding.power, orderBuilding.type, orderBuilding.path);
            } else {
                Diplog.warn(`Forced to select first valid location.`);
                validLocations = [validLocations[0]];
            }
        }
        let orderBuildingType = orderBuilding.type;
        if (lengthAfterClick === stepLength && orderBuildingType === 'M') {
            const moveOrderPath = ['M'].concat(orderBuilding.path, validLocations[0]);
            const moveTypes = UTILS.javascript.getTreeValue(this.props.game.ordersTree, moveOrderPath);
            if (moveTypes !== null) {
                if (moveTypes.length === 2 && this.props.onSelectVia) {
                    // This move can be done either regularly or VIA a fleet. Let user choose.
                    return this.props.onSelectVia(validLocations[0], orderBuilding.power, orderBuilding.path);
                } else {
                    orderBuildingType = moveTypes[0];
                }
            }
        }
        extendOrderBuilding(
            orderBuilding.power, orderBuildingType, orderBuilding.path, validLocations[0],
            this.props.onOrderBuilding, this.props.onOrderBuilt, this.props.onError
        );
    }
    handleHoverID(id) {
        if (this.props.onHover) {
            const province = this.props.mapData.getProvince(id);
            if (province) {
                this.props.onHover(province.name, this.getRelatedOrders(province.name));
            }
        }
    }
    getRelatedOrders(name) {
        const orders = [];
        if (this.props.orders) {
            for (let powerOrders of Object.values(this.props.orders)) {
                if (powerOrders) {
                    for (let order of powerOrders) {
                        const pieces = order.split(/ +/);
                        if (pieces[1].slice(0, 3) === name.toUpperCase().slice(0, 3))
                            orders.push(order);
                    }
                }
            }
        }
        return orders;
    }
    getNeighbors(extraLocation) {
        const selectedPath = [this.props.orderBuilding.type].concat(this.props.orderBuilding.path);
        if (extraLocation)
            selectedPath.push(extraLocation);
        const possibleNeighbors = UTILS.javascript.getTreeValue(this.props.game.ordersTree, selectedPath);
        const neighbors = possibleNeighbors ? possibleNeighbors.map(neighbor => parseLocation(neighbor)) : [];
        return neighbors.length ? neighbors: null;
    }
    render() {
        const classes = %(classes)s;
        const game = this.props.game;
        const mapData = this.props.mapData;
        const orders = this.props.orders;

        //// Current phase.
        const current_phase = (game.phase[0] === '?' || game.phase === 'COMPLETED') ? 'FINAL' : game.phase;

        //// Notes.
        const nb_centers = [];
        for (let power of Object.values(game.powers)) {
            if (!power.isEliminated())
                nb_centers.push([power.name.substr(0, 3), power.centers.length]);
        }
        // Sort nb_centers by descending number of centers.
        nb_centers.sort((a, b) => {
            return -(a[1] - b[1]) || a[0].localeCompare(b[0]);
        });
        const nb_centers_per_power = nb_centers.map((couple) => (couple[0] + ': ' + couple[1])).join(' ');
        const note = game.note;

        //// Adding units, supply centers, influence and orders.
        const scs = new Set(mapData.supplyCenters);
        const renderedUnits = [];
        const renderedDislodgedUnits = [];
        const renderedSupplyCenters = [];
        const renderedOrders = [];
        const renderedOrders2 = [];
        const renderedHighestOrders = [];
        for (let power of Object.values(game.powers)) {
            for (let unit of power.units) {
                renderedUnits.push(
                    <Unit key={unit}
                          unit={unit}
                          powerName={power.name}
                          isDislodged={false}
                          coordinates={Coordinates}
                          symbolSizes={SymbolSizes}/>
                );
            }
            for (let unit of Object.keys(power.retreats)) {
                renderedDislodgedUnits.push(
                    <Unit key={unit}
                          unit={unit}
                          powerName={power.name}
                          isDislodged={true}
                          coordinates={Coordinates}
                          symbolSizes={SymbolSizes}/>
                );
            }
            for (let center of power.centers) {
                renderedSupplyCenters.push(
                    <SupplyCenter key={center}
                                  loc={center}
                                  powerName={power.name}
                                  coordinates={Coordinates}
                                  symbolSizes={SymbolSizes}/>
                );
                setInfluence(classes, mapData, center, power.name);
                scs.delete(center);
            }
            if (!power.isEliminated()) {
                for (let loc of power.influence) {
                    if (!mapData.supplyCenters.has(loc))
                        setInfluence(classes, mapData, loc, power.name);
                }
            }

            if (orders) {
                const powerOrders = (orders && orders.hasOwnProperty(power.name) && orders[power.name]) || [];
                for (let order of powerOrders) {
                    const tokens = order.split(/ +/);
                    if (!tokens || tokens.length < 3)
                        continue;
                    const unit_loc = tokens[1];
                    if (tokens[2] === 'H') {
                        renderedOrders.push(
                            <Hold key={order}
                                  loc={unit_loc}
                                  powerName={power.name}
                                  coordinates={Coordinates}
                                  colors={Colors}/>
                        );
                    } else if (tokens[2] === '-') {
                        const destLoc = tokens[tokens.length - (tokens[tokens.length - 1] === 'VIA' ? 2 : 1)];
                        renderedOrders.push(
                            <Move key={order}
                                  srcLoc={unit_loc}
                                  dstLoc={destLoc}
                                  powerName={power.name}
                                  phaseType={game.getPhaseType()}
                                  coordinates={Coordinates}
                                  colors={Colors}/>
                        );
                    } else if (tokens[2] === 'S') {
                        const destLoc = tokens[tokens.length - 1];
                        if (tokens.includes('-')) {
                            const srcLoc = tokens[4];
                            renderedOrders2.push(
                                <SupportMove key={order}
                                             loc={unit_loc}
                                             srcLoc={srcLoc}
                                             dstLoc={destLoc}
                                             powerName={power.name}
                                             coordinates={Coordinates}
                                             colors={Colors}/>
                            );
                        } else {
                            renderedOrders2.push(
                                <SupportHold key={order}
                                             loc={unit_loc}
                                             dstLoc={destLoc}
                                             powerName={power.name}
                                             coordinates={Coordinates}
                                             colors={Colors}/>
                            );
                        }
                    } else if (tokens[2] === 'C') {
                        const srcLoc = tokens[4];
                        const destLoc = tokens[tokens.length - 1];
                        if ((srcLoc !== destLoc) && (tokens.includes('-'))) {
                            renderedOrders2.push(
                                <Convoy key={order}
                                        loc={unit_loc}
                                        srcLoc={srcLoc}
                                        dstLoc={destLoc}
                                        powerName={power.name}
                                        coordinates={Coordinates} colors={Colors}/>
                            );
                        }
                    } else if (tokens[2] === 'B') {
                        renderedHighestOrders.push(
                            <Build key={order}
                                   unitType={tokens[0]}
                                   loc={unit_loc}
                                   powerName={power.name}
                                   coordinates={Coordinates}
                                   symbolSizes={SymbolSizes}/>
                        );
                    } else if (tokens[2] === 'D') {
                        renderedHighestOrders.push(
                            <Disband key={order}
                                     loc={unit_loc}
                                     phaseType={game.getPhaseType()}
                                     coordinates={Coordinates}
                                     symbolSizes={SymbolSizes}/>
                        );
                    } else if (tokens[2] === 'R') {
                        const srcLoc = tokens[1];
                        const destLoc = tokens[3];
                        renderedOrders.push(
                            <Move key={order}
                                  srcLoc={srcLoc}
                                  dstLoc={destLoc}
                                  powerName={power.name}
                                  phaseType={game.getPhaseType()}
                                  coordinates={Coordinates}
                                  colors={Colors}/>
                        );
                    } else {
                        throw new Error(`Unknown error to render (${order}).`);
                    }
                }
            }
        }
        // Adding remaining supply centers.
        for (let remainingCenter of scs) {
            renderedSupplyCenters.push(
                <SupplyCenter key={remainingCenter}
                              loc={remainingCenter}
                              coordinates={Coordinates}
                              symbolSizes={SymbolSizes}/>
            );
        }

        if (this.props.orderBuilding && this.props.orderBuilding.path.length) {
            const clicked = parseLocation(this.props.orderBuilding.path[0]);
            const province  = this.props.mapData.getProvince(clicked);
            if (!province)
                throw new Error(('Unknown clicked province ' + clicked));
            const clickedID = province.getID(classes);
            if (!clicked)
                throw new Error(`Unknown path (${clickedID}) for province (${clicked}).`);
            classes[clickedID] = 'provinceRed';
            const neighbors = this.getNeighbors();
            if (neighbors) {
                for (let neighbor of neighbors) {
                    const neighborProvince = this.props.mapData.getProvince(neighbor);
                    if (!neighborProvince)
                        throw new Error('Unknown neighbor province ' + neighbor);
                    const neighborID = neighborProvince.getID(classes);
                    if (!neighborID)
                        throw new Error(`Unknown neoghbor path (${neighborID}) for province (${neighbor}).`);
                    classes[neighborID] = neighborProvince.isWater() ? 'provinceBlue' : 'provinceGreen';
                }
            }
        }

        return (
%(svg)s
        );
    }
}
%(classname)s.propTypes = {
    game: PropTypes.instanceOf(Game).isRequired,
    mapData: PropTypes.instanceOf(MapData).isRequired,
    orders: PropTypes.object,
    onHover: PropTypes.func,
    onError: PropTypes.func.isRequired,
    onSelectLocation: PropTypes.func,
    onSelectVia: PropTypes.func,
    onOrderBuilding: PropTypes.func,
    onOrderBuilt: PropTypes.func,
    orderBuilding: PropTypes.object
};
""" % {
            'style_content': "import './%s.css';" % class_name if data.style_lines else '',
            'extra_content': 'import {Coordinates, SymbolSizes, Colors} from "./%sParsed";' % (
                extra_class_name) if data.extra else '',
            'classname': class_name,
            'classes': json.dumps(data.id_to_class),
            'svg': '\n'.join(lines),
            'program_name': sys.argv[0],
            'args': args,
            'license_text': LICENSE_TEXT
        })


if __name__ == '__main__':
    main()
