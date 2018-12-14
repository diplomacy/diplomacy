# ==============================================================================
# Copyright (C) 2019 - Philip Paquette
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
# -*- coding: utf-8 -*-
""" Renderer
    - Contains the renderer object which is responsible for rendering a game state to svg
"""
import os
from xml.dom import minidom
from diplomacy import settings

# Constants
LAYER_SC = 'SupplyCenterLayer'
LAYER_ORDER = 'OrderLayer'
LAYER_UNIT = 'UnitLayer'
LAYER_DISL = 'DislodgedUnitLayer'
ARMY = 'Army'
FLEET = 'Fleet'

def _attr(node_element, attr_name):
    """ Shorthand method to retrieve an XML attribute """
    return node_element.attributes[attr_name].value

def _offset(str_float, offset):
    """ Shorthand to add a offset to an attribute """
    return str(float(str_float) + offset)


class Renderer():
    """ Renderer object responsible for rendering a game state to svg """

    def __init__(self, game):
        """ Constructor
            :param game: The instantiated game object to render
            :type game: diplomacy.Game
        """
        self.game = game
        self.metadata = {}
        self.xml_map = None
        self.xml_map_path = os.path.join(settings.PACKAGE_DIR, 'maps', 'svg', self.game.map.name + '.svg')

        # Loading XML
        if os.path.exists(self.xml_map_path):
            self.xml_map = minidom.parse(self.xml_map_path).toxml()
        self._load_metadata()

    def norm_order(self, order):
        """ Normalizes the order format and split it into tokens
            This is only used for **movement** orders (to make sure NO_CHECK games used the correct format)
            Formats:
                A PAR H
                A PAR - BUR [VIA]
                A PAR S BUR
                A PAR S F BRE - PIC
                F BRE C A PAR - LON

            :param order: The unformatted order (e.g. 'Paris - Burgundy')
            :return: The tokens of the formatted order (e.g. ['A', 'PAR', '-', 'BUR'])
        """
        return self.game._add_unit_types(self.game._expand_order(order.split()))    # pylint: disable=protected-access

    def render(self, incl_orders=True, incl_abbrev=False, output_format='svg'):
        """ Renders the current game and returns the XML representation
            :param incl_orders:  Optional. Flag to indicate we also want to render orders.
            :param incl_abbrev: Optional. Flag to indicate we also want to display the provinces abbreviations.
            :param output_format: The desired output format.
            :return: The rendered image in the specified format.
        """
        # pylint: disable=too-many-branches
        if output_format not in ['svg']:
            raise ValueError('Only "svg" format is current supported.')
        if not self.game or not self.game.map or not self.xml_map:
            return None

        # Parsing XML
        xml_map = minidom.parseString(self.xml_map)
        scs = self.game.map.scs[:]

        # Setting phase and note
        nb_centers = [(power.name[:3], len(power.centers))
                      for power in self.game.powers.values()
                      if not power.is_eliminated()]
        nb_centers = sorted(nb_centers, key=lambda key: key[1], reverse=True)
        nb_centers_per_power = ' '.join(['{}: {}'.format(name, centers) for name, centers in nb_centers])
        xml_map = self._set_current_phase(xml_map, self.game.get_current_phase())
        xml_map = self._set_note(xml_map, nb_centers_per_power, self.game.note)

        # Adding units, supply centers, and influence
        for power in self.game.powers.values():
            for unit in power.units:
                xml_map = self._add_unit(xml_map, unit, power.name, is_dislodged=False)
            for unit in power.retreats:
                xml_map = self._add_unit(xml_map, unit, power.name, is_dislodged=True)
            for center in power.centers:
                xml_map = self._add_supply_center(xml_map, center, power.name)
                xml_map = self._set_influence(xml_map, center, power.name, has_supply_center=True)
                scs.remove(center)
            for loc in power.influence:
                xml_map = self._set_influence(xml_map, loc, power.name, has_supply_center=False)

            # Orders
            if incl_orders:

                # Regular orders (Normalized)
                # A PAR H
                # A PAR - BUR [VIA]
                # A PAR S BUR
                # A PAR S F BRE - PIC
                # F BRE C A PAR - LON
                for order_key in power.orders:

                    # No_check order (Order, Invalid, Reorder)
                    # Otherwise regular order (unit is key, order without unit is value)
                    if order_key[0] in 'RIO':
                        order = power.orders[order_key]
                    else:
                        order = '{} {}'.format(order_key, power.orders[order_key])

                    # Normalizing and splitting in tokens
                    tokens = self.norm_order(order)
                    unit_loc = tokens[1]

                    # Parsing based on order type
                    if not tokens or len(tokens) < 3:
                        continue
                    elif tokens[2] == 'H':
                        xml_map = self._issue_hold_order(xml_map, unit_loc, power.name)
                    elif tokens[2] == '-':
                        dest_loc = tokens[-1] if tokens[-1] != 'VIA' else tokens[-2]
                        xml_map = self._issue_move_order(xml_map, unit_loc, dest_loc, power.name)
                    elif tokens[2] == 'S':
                        dest_loc = tokens[-1]
                        if '-' in tokens:
                            src_loc = tokens[4] if tokens[3] == 'A' or tokens[3] == 'F' else tokens[3]
                            xml_map = self._issue_support_move_order(xml_map, unit_loc, src_loc, dest_loc, power.name)
                        else:
                            xml_map = self._issue_support_hold_order(xml_map, unit_loc, dest_loc, power.name)
                    elif tokens[2] == 'C':
                        src_loc = tokens[4] if tokens[3] == 'A' or tokens[3] == 'F' else tokens[3]
                        dest_loc = tokens[-1]
                        if src_loc != dest_loc and '-' in tokens:
                            xml_map = self._issue_convoy_order(xml_map, unit_loc, src_loc, dest_loc, power.name)
                    else:
                        raise RuntimeError('Unknown order: {}'.format(' '.join(tokens)))

                # Adjustment orders
                # VOID xxx
                # A PAR B
                # A PAR D
                # A PAR R BUR
                # WAIVE
                for order in power.adjust:
                    tokens = order.split()
                    if not tokens or tokens[0] == 'VOID' or tokens[-1] == 'WAIVE':
                        continue
                    elif tokens[-1] == 'B':
                        if len(tokens) < 3:
                            continue
                        xml_map = self._issue_build_order(xml_map, tokens[0], tokens[1], power.name)
                    elif tokens[-1] == 'D':
                        xml_map = self._issue_disband_order(xml_map, tokens[1])
                    elif tokens[-2] == 'R':
                        src_loc = tokens[1] if tokens[0] == 'A' or tokens[0] == 'F' else tokens[0]
                        dest_loc = tokens[-1]
                        xml_map = self._issue_move_order(xml_map, src_loc, dest_loc, power.name)
                    else:
                        raise RuntimeError('Unknown order: {}'.format(order))

        # Adding remaining supply centers
        for center in scs:
            xml_map = self._add_supply_center(xml_map, center, None)

        # Removing abbrev and mouse layer
        svg_node = xml_map.getElementsByTagName('svg')[0]
        for child_node in svg_node.childNodes:
            if child_node.nodeName != 'g':
                continue
            if _attr(child_node, 'id') == 'BriefLabelLayer' and not incl_abbrev:
                svg_node.removeChild(child_node)
            elif _attr(child_node, 'id') == 'MouseLayer':
                svg_node.removeChild(child_node)

        # Returning
        return xml_map.toxml()

    def _load_metadata(self):
        """ Loads meta-data embedded in the XML map and clears unused nodes """
        if not self.xml_map:
            return
        xml_map = minidom.parseString(self.xml_map)

        # Data
        self.metadata = {
            'color': {},
            'symbol_size': {},
            'orders': {},
            'coord': {}
        }

        # Order drawings
        for order_drawing in xml_map.getElementsByTagName('jdipNS:ORDERDRAWING'):
            for child_node in order_drawing.childNodes:

                # Power Colors
                if child_node.nodeName == 'jdipNS:POWERCOLORS':
                    for power_color in child_node.childNodes:
                        if power_color.nodeName == 'jdipNS:POWERCOLOR':
                            self.metadata['color'][_attr(power_color, 'power').upper()] = _attr(power_color, 'color')

                # Symbol size
                elif child_node.nodeName == 'jdipNS:SYMBOLSIZE':
                    self.metadata['symbol_size'][_attr(child_node, 'name')] = (_attr(child_node, 'height'),
                                                                               _attr(child_node, 'width'))

                # Order type
                elif child_node.nodeName.startswith('jdipNS'):
                    order_type = child_node.nodeName.replace('jdipNS:', '')
                    self.metadata['orders'][order_type] = {}
                    for attr_name, attr_value in child_node.attributes.items():
                        if ':' in attr_name:
                            continue
                        self.metadata['orders'][order_type][attr_name] = attr_value

        # Object coordinates
        for province_data in xml_map.getElementsByTagName('jdipNS:PROVINCE_DATA'):
            for child_node in province_data.childNodes:

                # Province
                if child_node.nodeName == 'jdipNS:PROVINCE':
                    province = _attr(child_node, 'name').upper().replace('-', '/')
                    self.metadata['coord'][province] = {}

                    for coord_node in child_node.childNodes:
                        if coord_node.nodeName == 'jdipNS:UNIT':
                            self.metadata['coord'][province]['unit'] = (_attr(coord_node, 'x'), _attr(coord_node, 'y'))
                        elif coord_node.nodeName == 'jdipNS:DISLODGED_UNIT':
                            self.metadata['coord'][province]['disl'] = (_attr(coord_node, 'x'), _attr(coord_node, 'y'))
                        elif coord_node.nodeName == 'jdipNS:SUPPLY_CENTER':
                            self.metadata['coord'][province]['sc'] = (_attr(coord_node, 'x'), _attr(coord_node, 'y'))

        # Deleting
        svg_node = xml_map.getElementsByTagName('svg')[0]
        svg_node.removeChild(xml_map.getElementsByTagName('jdipNS:DISPLAY')[0])
        svg_node.removeChild(xml_map.getElementsByTagName('jdipNS:ORDERDRAWING')[0])
        svg_node.removeChild(xml_map.getElementsByTagName('jdipNS:PROVINCE_DATA')[0])
        self.xml_map = xml_map.toxml()

    def _add_unit(self, xml_map, unit, power_name, is_dislodged):
        """ Adds a unit to the map
            :param xml_map: The xml map being generated
            :param unit: The unit to add (e.g. 'A PAR')
            :param power_name: The name of the power owning the unit (e.g. 'FRANCE')
            :param is_dislodged: Boolean. Indicates if the unit is dislodged
            :return: Nothing
        """
        unit_type, loc = unit.split()
        symbol = FLEET if unit_type == 'F' else ARMY
        loc_x = _offset(self.metadata['coord'][loc][('unit', 'disl')[is_dislodged]][0], -11.5)
        loc_y = _offset(self.metadata['coord'][loc][('unit', 'disl')[is_dislodged]][1], - 10.)
        node = xml_map.createElement('use')
        node.setAttribute('x', loc_x)
        node.setAttribute('y', loc_y)
        node.setAttribute('height', self.metadata['symbol_size'][symbol][0])
        node.setAttribute('width', self.metadata['symbol_size'][symbol][1])
        node.setAttribute('xlink:href', '#{}{}'.format(('', 'Dislodged')[is_dislodged], symbol))
        node.setAttribute('class', 'unit{}'.format(power_name.lower()))

        # Inserting
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' \
                    and _attr(child_node, 'id') == ['UnitLayer', 'DislodgedUnitLayer'][is_dislodged]:
                child_node.appendChild(node)
                break
        return xml_map

    def _add_supply_center(self, xml_map, loc, power_name):
        """ Adds a supply center to the map
            :param xml_map: The xml map being generated
            :param loc: The province where to add the SC (e.g. 'PAR')
            :param power_name: The name of the power owning the SC or None
            :return: Nothing
        """
        symbol = 'SupplyCenter'
        loc_x = _offset(self.metadata['coord'][loc]['sc'][0], -8.5)
        loc_y = _offset(self.metadata['coord'][loc]['sc'][1], -11.)
        node = xml_map.createElement('use')
        node.setAttribute('x', loc_x)
        node.setAttribute('y', loc_y)
        node.setAttribute('height', self.metadata['symbol_size'][symbol][0])
        node.setAttribute('width', self.metadata['symbol_size'][symbol][1])
        node.setAttribute('xlink:href', '#{}'.format(symbol))
        if power_name:
            node.setAttribute('class', 'sc{}'.format(power_name.lower()))
        else:
            node.setAttribute('class', 'scnopower')

        # Inserting
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'SupplyCenterLayer':
                child_node.appendChild(node)
                break
        return xml_map

    def _set_influence(self, xml_map, loc, power_name, has_supply_center=False):
        """ Sets the influence on the map
            :param xml_map: The xml map being generated
            :param loc: The province being influenced (e.g. 'PAR')
            :param power_name: The name of the power influencing the province
            :param has_supply_center: Boolean flag to acknowledge we are modifying a loc with a SC
            :return: Nothing
        """
        loc = loc.upper()[:3]
        if loc in self.game.map.scs and not has_supply_center:
            return xml_map
        if self.game.map.area_type(loc) not in ['LAND', 'COAST']:
            return xml_map

        # Inserting
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'MapLayer':
                for map_node in child_node.childNodes:
                    if map_node.nodeName == 'path' and _attr(map_node, 'id') == '_{}'.format(loc.lower()):
                        if power_name:
                            map_node.setAttribute('class', power_name.lower())
                        else:
                            map_node.setAttribute('class', 'nopower')
                        return xml_map

        # Returning
        return xml_map

    @staticmethod
    def _set_current_phase(xml_map, current_phase):
        """ Sets the phase text at the bottom right of the the map
            :param xml_map: The xml map being generated
            :param current_phase: The current phase (e.g. 'S1901M)
            :return: Nothing
        """
        current_phase = 'FINAL' if current_phase[0] == '?' else current_phase
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'text' and _attr(child_node, 'id') == 'CurrentPhase':
                child_node.childNodes[0].nodeValue = current_phase
                return xml_map
        return xml_map

    @staticmethod
    def _set_note(xml_map, note_1, note_2):
        """ Sets a note at the top left of the map
            :param xml_map: The xml map being generated
            :param note_1: The text to display on the first line
            :param note_2: The text to display on the second line
            :return: Nothing
        """
        note_1 = note_1 or ' '
        note_2 = note_2 or ' '
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'text' and _attr(child_node, 'id') == 'CurrentNote':
                child_node.childNodes[0].nodeValue = note_1
            if child_node.nodeName == 'text' and _attr(child_node, 'id') == 'CurrentNote2':
                child_node.childNodes[0].nodeValue = note_2
        return xml_map

    def _issue_hold_order(self, xml_map, loc, power_name):
        """ Adds a hold order to the map
            :param xml_map: The xml map being generated
            :param loc: The province where the unit is holding (e.g. 'PAR')
            :param power_name: The name of the power owning the unit
            :return: Nothing
        """
        # Calculating polygon coord
        polygon_coord = []
        loc_x = _offset(self.metadata['coord'][loc]['unit'][0], 8.5)
        loc_y = _offset(self.metadata['coord'][loc]['unit'][1], 9.5)
        for offset in [(13.8, -33.3), (33.3, -13.8), (33.3, 13.8), (13.8, 33.3), (-13.8, 33.3), (-33.3, 13.8),
                       (-33.3, -13.8), (-13.8, -33.3)]:
            polygon_coord += [_offset(loc_x, offset[0]) + ',' + _offset(loc_y, offset[1])]

        # Building polygon
        g_node = xml_map.createElement('g')

        poly_1 = xml_map.createElement('polygon')
        poly_1.setAttribute('stroke-width', '10')
        poly_1.setAttribute('class', 'varwidthshadow')
        poly_1.setAttribute('points', ' '.join(polygon_coord))

        poly_2 = xml_map.createElement('polygon')
        poly_2.setAttribute('stroke-width', '6')
        poly_2.setAttribute('class', 'varwidthorder')
        poly_2.setAttribute('points', ' '.join(polygon_coord))
        poly_2.setAttribute('stroke', self.metadata['color'][power_name])

        g_node.appendChild(poly_1)
        g_node.appendChild(poly_2)

        # Inserting
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer1':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def _issue_support_hold_order(self, xml_map, loc, dest_loc, power_name):
        """ Issues a support hold order
            :param xml_map: The xml map being generated
            :param loc: The location of the unit sending support (e.g. 'BER')
            :param dest_loc: The location where the unit is holding from (e.g. 'PAR')
            :param power_name: The power name issuing the move order
            :return: Nothing
        """
        loc_x = _offset(self.metadata['coord'][loc]['unit'][0], 10)
        loc_y = _offset(self.metadata['coord'][loc]['unit'][1], 10)
        dest_loc_x = _offset(self.metadata['coord'][dest_loc]['unit'][0], 10)
        dest_loc_y = _offset(self.metadata['coord'][dest_loc]['unit'][1], 10)

        # Adjusting destination
        delta_x = float(dest_loc_x) - float(loc_x)
        delta_y = float(dest_loc_y) - float(loc_y)
        vector_length = (delta_x ** 2. + delta_y ** 2.) ** 0.5
        dest_loc_x = str(round(float(loc_x) + (vector_length - 35.) / vector_length * delta_x, 2))
        dest_loc_y = str(round(float(loc_y) + (vector_length - 35.) / vector_length * delta_y, 2))

        # Getting polygon coordinates
        polygon_coord = []
        poly_loc_x = _offset(self.metadata['coord'][dest_loc]['unit'][0], 8.5)
        poly_loc_y = _offset(self.metadata['coord'][dest_loc]['unit'][1], 9.5)
        for offset in [(15.9, -38.3), (38.3, -15.9), (38.3, 15.9), (15.9, 38.3), (-15.9, 38.3), (-38.3, 15.9),
                       (-38.3, -15.9), (-15.9, -38.3)]:
            polygon_coord += [_offset(poly_loc_x, offset[0]) + ',' + _offset(poly_loc_y, offset[1])]

        # Creating nodes
        g_node = xml_map.createElement('g')

        shadow_line = xml_map.createElement('line')
        shadow_line.setAttribute('x1', loc_x)
        shadow_line.setAttribute('y1', loc_y)
        shadow_line.setAttribute('x2', dest_loc_x)
        shadow_line.setAttribute('y2', dest_loc_y)
        shadow_line.setAttribute('class', 'shadowdash')

        support_line = xml_map.createElement('line')
        support_line.setAttribute('x1', loc_x)
        support_line.setAttribute('y1', loc_y)
        support_line.setAttribute('x2', dest_loc_x)
        support_line.setAttribute('y2', dest_loc_y)
        support_line.setAttribute('class', 'supportorder')
        support_line.setAttribute('stroke', self.metadata['color'][power_name])

        shadow_poly = xml_map.createElement('polygon')
        shadow_poly.setAttribute('class', 'shadowdash')
        shadow_poly.setAttribute('points', ' '.join(polygon_coord))

        support_poly = xml_map.createElement('polygon')
        support_poly.setAttribute('class', 'supportorder')
        support_poly.setAttribute('points', ' '.join(polygon_coord))
        support_poly.setAttribute('stroke', self.metadata['color'][power_name])

        # Inserting
        g_node.appendChild(shadow_line)
        g_node.appendChild(support_line)
        g_node.appendChild(shadow_poly)
        g_node.appendChild(support_poly)

        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer2':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def _issue_move_order(self, xml_map, src_loc, dest_loc, power_name):
        """ Issues a move order
            :param xml_map: The xml map being generated
            :param src_loc: The location where the unit is moving from (e.g. 'PAR')
            :param dest_loc: The location where the unit is moving to (e.g. 'MAR')
            :param power_name: The power name issuing the move order
            :return: Nothing
        """
        if self.game.get_current_phase()[-1] == 'R':
            src_loc_x = _offset(self.metadata['coord'][src_loc]['unit'][0], -2.5)
            src_loc_y = _offset(self.metadata['coord'][src_loc]['unit'][1], -2.5)
        else:
            src_loc_x = _offset(self.metadata['coord'][src_loc]['unit'][0], 10)
            src_loc_y = _offset(self.metadata['coord'][src_loc]['unit'][1], 10)
        dest_loc_x = _offset(self.metadata['coord'][dest_loc]['unit'][0], 10)
        dest_loc_y = _offset(self.metadata['coord'][dest_loc]['unit'][1], 10)

        # Adjusting destination
        delta_x = float(dest_loc_x) - float(src_loc_x)
        delta_y = float(dest_loc_y) - float(src_loc_y)
        vector_length = (delta_x ** 2. + delta_y ** 2.) ** 0.5
        dest_loc_x = str(round(float(src_loc_x) + (vector_length - 30.) / vector_length * delta_x, 2))
        dest_loc_y = str(round(float(src_loc_y) + (vector_length - 30.) / vector_length * delta_y, 2))

        # Creating nodes
        g_node = xml_map.createElement('g')

        line_with_shadow = xml_map.createElement('line')
        line_with_shadow.setAttribute('x1', src_loc_x)
        line_with_shadow.setAttribute('y1', src_loc_y)
        line_with_shadow.setAttribute('x2', dest_loc_x)
        line_with_shadow.setAttribute('y2', dest_loc_y)
        line_with_shadow.setAttribute('class', 'varwidthshadow')
        line_with_shadow.setAttribute('stroke-width', '10')

        line_with_arrow = xml_map.createElement('line')
        line_with_arrow.setAttribute('x1', src_loc_x)
        line_with_arrow.setAttribute('y1', src_loc_y)
        line_with_arrow.setAttribute('x2', dest_loc_x)
        line_with_arrow.setAttribute('y2', dest_loc_y)
        line_with_arrow.setAttribute('class', 'varwidthorder')
        line_with_arrow.setAttribute('stroke', self.metadata['color'][power_name])
        line_with_arrow.setAttribute('stroke-width', '6')
        line_with_arrow.setAttribute('marker-end', 'url(#arrow)')

        # Inserting
        g_node.appendChild(line_with_shadow)
        g_node.appendChild(line_with_arrow)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer1':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def _issue_support_move_order(self, xml_map, loc, src_loc, dest_loc, power_name):
        """ Issues a support move order
            :param xml_map: The xml map being generated
            :param loc: The location of the unit sending support (e.g. 'BER')
            :param src_loc: The location where the unit is moving from (e.g. 'PAR')
            :param dest_loc: The location where the unit is moving to (e.g. 'MAR')
            :param power_name: The power name issuing the move order
            :return: Nothing
        """
        loc_x = _offset(self.metadata['coord'][loc]['unit'][0], 10)
        loc_y = _offset(self.metadata['coord'][loc]['unit'][1], 10)
        src_loc_x = _offset(self.metadata['coord'][src_loc]['unit'][0], 10)
        src_loc_y = _offset(self.metadata['coord'][src_loc]['unit'][1], 10)
        dest_loc_x = _offset(self.metadata['coord'][dest_loc]['unit'][0], 10)
        dest_loc_y = _offset(self.metadata['coord'][dest_loc]['unit'][1], 10)

        # Adjusting destination
        delta_x = float(dest_loc_x) - float(src_loc_x)
        delta_y = float(dest_loc_y) - float(src_loc_y)
        vector_length = (delta_x ** 2. + delta_y ** 2.) ** 0.5
        dest_loc_x = str(round(float(src_loc_x) + (vector_length - 30.) / vector_length * delta_x, 2))
        dest_loc_y = str(round(float(src_loc_y) + (vector_length - 30.) / vector_length * delta_y, 2))

        # Creating nodes
        g_node = xml_map.createElement('g')

        path_with_shadow = xml_map.createElement('path')
        path_with_shadow.setAttribute('class', 'shadowdash')
        path_with_shadow.setAttribute('d', 'M {x},{y} C {src_x},{src_y} {src_x},{src_y} {dest_x},{dest_y}'
                                      .format(x=loc_x,
                                              y=loc_y,
                                              src_x=src_loc_x,
                                              src_y=src_loc_y,
                                              dest_x=dest_loc_x,
                                              dest_y=dest_loc_y))

        path_with_arrow = xml_map.createElement('path')
        path_with_arrow.setAttribute('class', 'supportorder')
        path_with_arrow.setAttribute('stroke', self.metadata['color'][power_name])
        path_with_arrow.setAttribute('marker-end', 'url(#arrow)')
        path_with_arrow.setAttribute('d', 'M {x},{y} C {src_x},{src_y} {src_x},{src_y} {dest_x},{dest_y}'
                                     .format(x=loc_x,
                                             y=loc_y,
                                             src_x=src_loc_x,
                                             src_y=src_loc_y,
                                             dest_x=dest_loc_x,
                                             dest_y=dest_loc_y))

        # Inserting
        g_node.appendChild(path_with_shadow)
        g_node.appendChild(path_with_arrow)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer2':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def _issue_convoy_order(self, xml_map, loc, src_loc, dest_loc, power_name):
        """ Issues a convoy order
            :param xml_map: The xml map being generated
            :param loc: The location of the unit convoying (e.g. 'BER')
            :param src_loc: The location where the unit being convoyed is moving from (e.g. 'PAR')
            :param dest_loc: The location where the unit being convoyed is moving to (e.g. 'MAR')
            :param power_name: The power name issuing the convoy order
            :return: Nothing
        """
        loc_x = _offset(self.metadata['coord'][loc]['unit'][0], 10)
        loc_y = _offset(self.metadata['coord'][loc]['unit'][1], 10)
        src_loc_x = _offset(self.metadata['coord'][src_loc]['unit'][0], 10)
        src_loc_y = _offset(self.metadata['coord'][src_loc]['unit'][1], 10)
        dest_loc_x = _offset(self.metadata['coord'][dest_loc]['unit'][0], 10)
        dest_loc_y = _offset(self.metadata['coord'][dest_loc]['unit'][1], 10)

        # Adjusting starting arrow (from convoy to start location)
        # This is to avoid the end of the arrow conflicting with the convoy triangle
        src_delta_x = float(src_loc_x) - float(loc_x)
        src_delta_y = float(src_loc_y) - float(loc_y)
        src_vector_length = (src_delta_x ** 2. + src_delta_y ** 2.) ** 0.5
        src_loc_x_1 = str(round(float(loc_x) + (src_vector_length - 30.) / src_vector_length * src_delta_x, 2))
        src_loc_y_1 = str(round(float(loc_y) + (src_vector_length - 30.) / src_vector_length * src_delta_y, 2))

        # Adjusting destination arrow (from start location to destination location)
        # This is to avoid the start of the arrow conflicting with the convoy triangle
        dest_delta_x = float(src_loc_x) - float(dest_loc_x)
        dest_delta_y = float(src_loc_y) - float(dest_loc_y)
        dest_vector_length = (dest_delta_x ** 2. + dest_delta_y ** 2.) ** 0.5
        src_loc_x_2 = str(round(float(dest_loc_x) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_x, 2))
        src_loc_y_2 = str(round(float(dest_loc_y) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_y, 2))

        # Adjusting destination arrow (from start location to destination location)
        # This is to avoid the start of the arrow conflicting with the convoy triangle
        dest_delta_x = float(dest_loc_x) - float(src_loc_x)
        dest_delta_y = float(dest_loc_y) - float(src_loc_y)
        dest_vector_length = (dest_delta_x ** 2. + dest_delta_y ** 2.) ** 0.5
        dest_loc_x = str(round(float(src_loc_x) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_x, 2))
        dest_loc_y = str(round(float(src_loc_y) + (dest_vector_length - 30.) / dest_vector_length * dest_delta_y, 2))

        # Getting convoy triangle coordinates
        triangle_coord = []
        triangle_loc_x = _offset(self.metadata['coord'][src_loc]['unit'][0], 10)
        triangle_loc_y = _offset(self.metadata['coord'][src_loc]['unit'][1], 10)
        for offset in [(0, -38.3), (33.2, 19.1), (-33.2, 19.1)]:
            triangle_coord += [_offset(triangle_loc_x, offset[0]) + ',' + _offset(triangle_loc_y, offset[1])]

        # Creating nodes
        g_node = xml_map.createElement('g')

        src_shadow_line = xml_map.createElement('line')
        src_shadow_line.setAttribute('x1', loc_x)
        src_shadow_line.setAttribute('y1', loc_y)
        src_shadow_line.setAttribute('x2', src_loc_x_1)
        src_shadow_line.setAttribute('y2', src_loc_y_1)
        src_shadow_line.setAttribute('class', 'shadowdash')

        dest_shadow_line = xml_map.createElement('line')
        dest_shadow_line.setAttribute('x1', src_loc_x_2)
        dest_shadow_line.setAttribute('y1', src_loc_y_2)
        dest_shadow_line.setAttribute('x2', dest_loc_x)
        dest_shadow_line.setAttribute('y2', dest_loc_y)
        dest_shadow_line.setAttribute('class', 'shadowdash')

        src_convoy_line = xml_map.createElement('line')
        src_convoy_line.setAttribute('x1', loc_x)
        src_convoy_line.setAttribute('y1', loc_y)
        src_convoy_line.setAttribute('x2', src_loc_x_1)
        src_convoy_line.setAttribute('y2', src_loc_y_1)
        src_convoy_line.setAttribute('class', 'convoyorder')
        src_convoy_line.setAttribute('stroke', self.metadata['color'][power_name])

        dest_convoy_line = xml_map.createElement('line')
        dest_convoy_line.setAttribute('x1', src_loc_x_2)
        dest_convoy_line.setAttribute('y1', src_loc_y_2)
        dest_convoy_line.setAttribute('x2', dest_loc_x)
        dest_convoy_line.setAttribute('y2', dest_loc_y)
        dest_convoy_line.setAttribute('class', 'convoyorder')
        dest_convoy_line.setAttribute('stroke', self.metadata['color'][power_name])
        dest_convoy_line.setAttribute('marker-end', 'url(#arrow)')

        shadow_poly = xml_map.createElement('polygon')
        shadow_poly.setAttribute('class', 'shadowdash')
        shadow_poly.setAttribute('points', ' '.join(triangle_coord))

        convoy_poly = xml_map.createElement('polygon')
        convoy_poly.setAttribute('class', 'convoyorder')
        convoy_poly.setAttribute('points', ' '.join(triangle_coord))
        convoy_poly.setAttribute('stroke', self.metadata['color'][power_name])

        # Inserting
        g_node.appendChild(src_shadow_line)
        g_node.appendChild(dest_shadow_line)
        g_node.appendChild(src_convoy_line)
        g_node.appendChild(dest_convoy_line)
        g_node.appendChild(shadow_poly)
        g_node.appendChild(convoy_poly)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'OrderLayer':
                for layer_node in child_node.childNodes:
                    if layer_node.nodeName == 'g' and _attr(layer_node, 'id') == 'Layer2':
                        layer_node.appendChild(g_node)
                        return xml_map

        # Returning
        return xml_map

    def _issue_build_order(self, xml_map, unit_type, loc, power_name):
        """ Adds a build army/fleet order to the map
            :param xml_map: The xml map being generated
            :param unit_type: The unit type to build ('A' or 'F')
            :param loc: The province where the army is to be built (e.g. 'PAR')
            :param power_name: The name of the power building the unit
            :return: Nothing
        """
        loc_x = _offset(self.metadata['coord'][loc]['unit'][0], -11.5)
        loc_y = _offset(self.metadata['coord'][loc]['unit'][1], - 10.)
        build_loc_x = _offset(self.metadata['coord'][loc]['unit'][0], -20.5)
        build_loc_y = _offset(self.metadata['coord'][loc]['unit'][1], -20.5)

        # Symbols
        symbol = ARMY if unit_type == 'A' else FLEET
        build_symbol = 'BuildUnit'

        # Creating nodes
        g_node = xml_map.createElement('g')

        symbol_node = xml_map.createElement('use')
        symbol_node.setAttribute('x', loc_x)
        symbol_node.setAttribute('y', loc_y)
        symbol_node.setAttribute('height', self.metadata['symbol_size'][symbol][0])
        symbol_node.setAttribute('width', self.metadata['symbol_size'][symbol][1])
        symbol_node.setAttribute('xlink:href', '#{}'.format(symbol))
        symbol_node.setAttribute('class', 'unit{}'.format(power_name.lower()))

        build_node = xml_map.createElement('use')
        build_node.setAttribute('x', build_loc_x)
        build_node.setAttribute('y', build_loc_y)
        build_node.setAttribute('height', self.metadata['symbol_size'][build_symbol][0])
        build_node.setAttribute('width', self.metadata['symbol_size'][build_symbol][1])
        build_node.setAttribute('xlink:href', '#{}'.format(build_symbol))

        # Inserting
        g_node.appendChild(build_node)
        g_node.appendChild(symbol_node)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'HighestOrderLayer':
                child_node.appendChild(g_node)
                return xml_map

        # Returning
        return xml_map

    def _issue_disband_order(self, xml_map, loc):
        """ Adds a disband order to the map
            :param xml_map: The xml map being generated
            :param loc: The province where the unit is disbanded (e.g. 'PAR')
            :return: Nothing
        """
        if self.game.get_current_phase()[-1] == 'R':
            loc_x = _offset(self.metadata['coord'][loc]['unit'][0], -29.)
            loc_y = _offset(self.metadata['coord'][loc]['unit'][1], -27.5)
        else:
            loc_x = _offset(self.metadata['coord'][loc]['unit'][0], -16.5)
            loc_y = _offset(self.metadata['coord'][loc]['unit'][1], -15.)

        # Symbols
        symbol = 'RemoveUnit'

        # Creating nodes
        g_node = xml_map.createElement('g')
        symbol_node = xml_map.createElement('use')
        symbol_node.setAttribute('x', loc_x)
        symbol_node.setAttribute('y', loc_y)
        symbol_node.setAttribute('height', self.metadata['symbol_size'][symbol][0])
        symbol_node.setAttribute('width', self.metadata['symbol_size'][symbol][1])
        symbol_node.setAttribute('xlink:href', '#{}'.format(symbol))

        # Inserting
        g_node.appendChild(symbol_node)
        for child_node in xml_map.getElementsByTagName('svg')[0].childNodes:
            if child_node.nodeName == 'g' and _attr(child_node, 'id') == 'HighestOrderLayer':
                child_node.appendChild(g_node)
                return xml_map

        # Returning
        return xml_map
