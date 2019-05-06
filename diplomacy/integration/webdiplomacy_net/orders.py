# ==============================================================================
# Copyright 2019 - Philip Paquette. All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains the property of the authors
#   listed above. The intellectual and technical concepts contained herein are proprietary
#   and may be covered by U.S. and Foreign Patents, patents in process, and are protected
#   by trade secret or copyright law. Dissemination of this information or reproduction of
#   this material is strictly forbidden unless prior written permission is obtained.
# ==============================================================================
""" Orders - Contains utilities to convert orders between string format and webdiplomacy.net format """
import logging
from diplomacy import Map
from diplomacy.integration.webdiplomacy_net.utils import CACHE

# Constants
LOGGER = logging.getLogger(__name__)


class Order():
    """ Class to convert order from string representation to dictionary (webdiplomacy.net) representation """

    def __init__(self, order, map_id=None, map_name=None, phase_type=None):
        """ Constructor
            :param order: An order (either as a string 'A PAR H' or as a dictionary)
            :param map_id: Optional. The map id of the map where orders are submitted (webdiplomacy format)
            :param map_name: Optional. The map name of the map where orders are submitted.
            :param phase_type: Optional. The phase type ('M', 'R', 'A') to disambiguate orders to send.
        """
        self.map_name = 'standard'
        self.phase_type = 'M'
        self.order_str = ''
        self.order_dict = {}

        # Detecting the map name
        if map_id is not None:
            if map_id not in CACHE['ix_to_map']:
                raise ValueError('Map with id %s is not supported.' % map_id)
            self.map_name = CACHE['ix_to_map'][map_id]
        elif map_name is not None:
            if map_name not in CACHE['map_to_ix']:
                raise ValueError('Map with name %s is not supported.' % map_name)
            self.map_name = map_name

        # Detecting the phase type
        if isinstance(phase_type, str) and phase_type in 'MRA':
            self.phase_type = phase_type

        # Building the order
        if isinstance(order, str):
            self._build_from_string(order)
        elif isinstance(order, dict):
            self._build_from_dict(order)
        else:
            raise ValueError('Expected order to be a string or a dictionary.')

    def _build_from_string(self, order):
        """ Builds this object from a string
            :type order: str
        """
        # pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
        words = order.split()

        # --- Wait / Waive ---
        # [{"id": "56", "unitID": null, "type": "Wait", "toTerrID": "", "fromTerrID": "", "viaConvoy": ""}]
        if len(words) == 1 and words[0] == 'WAIVE':
            self.order_str = 'WAIVE'
            self.order_dict = {'terrID': None,
                               'unitType': '',
                               'type': 'Wait',
                               'toTerrID': '',
                               'fromTerrID': '',
                               'viaConvoy': ''}
            return

        # Validating
        if len(words) < 3:
            LOGGER.error('Unable to parse the order "%s". Require at least 3 words', order)
            return

        short_unit_type, loc_name, order_type = words[:3]
        if short_unit_type not in 'AF':
            LOGGER.error('Unable to parse the order "%s". Valid unit types are "A" and "F".', order)
            return
        if order_type not in 'H-SCRBD':
            LOGGER.error('Unable to parse the order "%s". Valid order types are H-SCRBD', order)
            return
        if loc_name not in CACHE[self.map_name]['loc_to_ix']:
            LOGGER.error('Received invalid loc "%s" for map "%s".', loc_name, self.map_name)
            return

        # Extracting territories
        unit_type = {'A': 'Army', 'F': 'Fleet'}[short_unit_type]
        terr_id = CACHE[self.map_name]['loc_to_ix'][loc_name]

        # --- Hold ---
        # {"id": "76", "unitID": "19", "type": "Hold", "toTerrID": "", "fromTerrID": "", "viaConvoy": ""}
        if order_type == 'H':
            self.order_str = '%s %s H' % (short_unit_type, loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Hold',
                               'toTerrID': '',
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Move ---
        # {"id": "73", "unitID": "16", "type": "Move", "toTerrID": "25", "fromTerrID": "", "viaConvoy": "Yes",
        # "convoyPath": ["22", "69"]},
        # {"id": "74", "unitID": "17", "type": "Move", "toTerrID": "69", "fromTerrID": "", "viaConvoy": "No"}
        elif order_type == '-':
            if len(words) < 4:
                LOGGER.error('[Move] Unable to parse the move order "%s". Require at least 4 words', order)
                LOGGER.error(order)
                return

            # Building map
            map_object = Map(self.map_name)
            fleets_in_convoy = set()
            convoy_path = []

            # Getting destination
            to_loc_name = words[3]
            to_terr_id = CACHE[self.map_name]['loc_to_ix'].get(to_loc_name, None)

            # Deciding if this move is doable by convoy or not
            if unit_type != 'Army':
                via_flag = ''
            else:
                reachable_by_land = map_object.abuts('A', loc_name, '-', to_loc_name)
                via_convoy = bool(words[-1] == 'VIA') or not reachable_by_land
                via_flag = ' VIA' if via_convoy else ''

                # Finding at least one possible convoy path from src to dest
                for nb_fleets in map_object.convoy_paths:
                    for start_loc, fleet_locs, dest_locs in map_object.convoy_paths[nb_fleets]:
                        if start_loc != loc_name or to_loc_name not in dest_locs:
                            continue
                        fleets_in_convoy |= fleet_locs
                        break
                    if fleets_in_convoy:
                        break

                # Converting to list of ints
                if fleets_in_convoy:
                    convoy_path = [terr_id] + [CACHE[self.map_name]['loc_to_ix'][loc] for loc in fleets_in_convoy]

            if to_loc_name is None:
                LOGGER.error('[Move] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return

            self.order_str = '%s %s - %s%s' % (short_unit_type, loc_name, to_loc_name, via_flag)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Move',
                               'toTerrID': to_terr_id,
                               'fromTerrID': '',
                               'viaConvoy': 'Yes' if via_flag else 'No'}
            if convoy_path:
                self.order_dict['convoyPath'] = [-1]

        # --- Support hold ---
        # {"id": "73", "unitID": "16", "type": "Support hold", "toTerrID": "24", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'S' and '-' not in words:
            if len(words) < 5:
                LOGGER.error('[Support H] Unable to parse the support hold order "%s". Require at least 5 words', order)
                LOGGER.error(order)
                return

            # Getting supported unit
            to_loc_name = words[4][:3]
            to_terr_id = CACHE[self.map_name]['loc_to_ix'].get(to_loc_name, None)

            if to_loc_name is None:
                LOGGER.error('[Support H] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return

            self.order_str = '%s %s S %s' % (short_unit_type, loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Support hold',
                               'toTerrID': to_terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Support move ---
        # {"id": "73", "unitID": "16", "type": "Support move", "toTerrID": "24", "fromTerrID": "69", "viaConvoy": ""}
        elif order_type == 'S':
            if len(words) < 6:
                LOGGER.error('Unable to parse the support move order "%s". Require at least 6 words', order)
                return

            # Building map
            map_object = Map(self.map_name)
            fleets_in_convoy = set()
            convoy_path = []

            # Getting supported unit
            move_index = words.index('-')
            to_loc_name = words[move_index + 1][:3]                         # Removing coast from dest
            from_loc_name = words[move_index - 1]
            to_terr_id = CACHE[self.map_name]['loc_to_ix'].get(to_loc_name, None)
            from_terr_id = CACHE[self.map_name]['loc_to_ix'].get(from_loc_name, None)

            if to_loc_name is None:
                LOGGER.error('[Support M] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return
            if from_loc_name is None:
                LOGGER.error('[Support M] Received invalid from loc "%s" for map "%s".', from_terr_id, self.map_name)
                LOGGER.error(order)
                return

            # Deciding if we are support a move by convoy or not
            if words[move_index - 2] != 'F' and map_object.area_type(from_loc_name) == 'COAST':

                # Finding at least one possible convoy path from src to dest
                for nb_fleets in map_object.convoy_paths:
                    for start_loc, fleet_locs, dest_locs in map_object.convoy_paths[nb_fleets]:
                        if start_loc != from_loc_name or to_loc_name not in dest_locs:
                            continue
                        fleets_in_convoy |= fleet_locs
                        break
                    if fleets_in_convoy:
                        break

                # Converting to list of ints
                if fleets_in_convoy:
                    convoy_path = [from_terr_id] + [CACHE[self.map_name]['loc_to_ix'][loc] for loc in fleets_in_convoy]

            self.order_str = '%s %s S %s - %s' % (short_unit_type, loc_name, from_loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Support move',
                               'toTerrID': to_terr_id,
                               'fromTerrID': from_terr_id,
                               'viaConvoy': ''}
            if convoy_path:
                self.order_dict['convoyPath'] = [-1]

        # --- Convoy ---
        # {"id": "79", "unitID": "22", "type": "Convoy", "toTerrID": "24", "fromTerrID": "20", "viaConvoy": "",
        # "convoyPath": ["20", "69"]}
        elif order_type == 'C':
            if len(words) < 6:
                LOGGER.error('[Convoy] Unable to parse the convoy order "%s". Require at least 6 words', order)
                LOGGER.error(order)
                return

            # Building map
            map_object = Map(self.map_name)
            fleets_in_convoy = set()
            convoy_path = []

            # Getting supported unit
            move_index = words.index('-')
            to_loc_name = words[move_index + 1]
            from_loc_name = words[move_index - 1]
            to_terr_id = CACHE[self.map_name]['loc_to_ix'].get(to_loc_name, None)
            from_terr_id = CACHE[self.map_name]['loc_to_ix'].get(from_loc_name, None)

            if to_loc_name is None:
                LOGGER.error('[Convoy] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return
            if from_loc_name is None:
                LOGGER.error('[Convoy] Received invalid from loc "%s" for map "%s".', from_terr_id, self.map_name)
                LOGGER.error(order)
                return

            # Finding at least one possible convoy path from src to dest
            for nb_fleets in map_object.convoy_paths:
                for start_loc, fleet_locs, dest_locs in map_object.convoy_paths[nb_fleets]:
                    if start_loc != from_loc_name or to_loc_name not in dest_locs:
                        continue
                    fleets_in_convoy |= fleet_locs
                    break
                if fleets_in_convoy:
                    break

            # Converting to list of ints
            if fleets_in_convoy:
                convoy_path = [from_terr_id] + [CACHE[self.map_name]['loc_to_ix'][loc] for loc in fleets_in_convoy]

            self.order_str = '%s %s C A %s - %s' % (short_unit_type, loc_name, from_loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Convoy',
                               'toTerrID': to_terr_id,
                               'fromTerrID': from_terr_id,
                               'viaConvoy': ''}
            if convoy_path:
                self.order_dict['convoyPath'] = [-1]

        # --- Retreat ---
        # {"id": "152", "unitID": "18", "type": "Retreat", "toTerrID": "75", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'R':
            if len(words) < 4:
                LOGGER.error('[Retreat] Unable to parse the move order "%s". Require at least 4 words', order)
                LOGGER.error(order)
                return

            # Getting destination
            to_loc_name = words[3]
            to_terr_id = CACHE[self.map_name]['loc_to_ix'].get(to_loc_name, None)

            if to_loc_name is None:
                return

            self.order_str = '%s %s R %s' % (short_unit_type, loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Retreat',
                               'toTerrID': to_terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Disband (R phase) ---
        # {"id": "152", "unitID": "18", "type": "Disband", "toTerrID": "", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'D' and self.phase_type == 'R':
            loc_name = loc_name[:3]
            terr_id = CACHE[self.map_name]['loc_to_ix'][loc_name]
            self.order_str = '%s %s D' % (short_unit_type, loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Disband',
                               'toTerrID': '',
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Build Army ---
        # [{"id": "56", "unitID": null, "type": "Build Army", "toTerrID": "37", "fromTerrID": "", "viaConvoy": ""}]
        elif order_type == 'B' and short_unit_type == 'A':
            self.order_str = 'A %s B' % loc_name
            self.order_dict = {'terrID': terr_id,
                               'unitType': 'Army',
                               'type': 'Build Army',
                               'toTerrID': terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # -- Build Fleet ---
        # [{"id": "56", "unitID": null, "type": "Build Fleet", "toTerrID": "37", "fromTerrID": "", "viaConvoy": ""}]
        elif order_type == 'B' and short_unit_type == 'F':
            self.order_str = 'F %s B' % loc_name
            self.order_dict = {'terrID': terr_id,
                               'unitType': 'Fleet',
                               'type': 'Build Fleet',
                               'toTerrID': terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # Disband (A phase)
        # {"id": "152", "unitID": null, "type": "Destroy", "toTerrID": "18", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'D':
            loc_name = loc_name[:3]
            terr_id = CACHE[self.map_name]['loc_to_ix'][loc_name]
            self.order_str = '%s %s D' % (short_unit_type, loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Destroy',
                               'toTerrID': terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

    def _build_from_dict(self, order):
        """ Builds this object from a dictionary
            :type order: dict
        """
        # pylint: disable=too-many-return-statements
        terr_id = order.get('terrID', None)
        unit_type = order.get('unitType', None)
        order_type = order.get('type', None)
        to_terr_id = order.get('toTerrID', '')
        from_terr_id = order.get('fromTerrID', '')
        via_convoy = order.get('viaConvoy', '')

        # Using to_terr_id if terr_id is None
        terr_id = terr_id if terr_id is not None else to_terr_id

        # Overriding unit type for builds
        if order_type == 'Build Army':
            unit_type = 'Army'
        elif order_type == 'Build Fleet':
            unit_type = 'Fleet'
        elif order_type in ('Destroy', 'Wait') and unit_type not in ('Army', 'Fleet'):
            unit_type = '?'

        # Validating order
        if unit_type not in ('Army', 'Fleet', '?'):
            LOGGER.error('Received invalid unit type "%s". Expected "Army" or "Fleet".', unit_type)
            return
        if order_type not in ('Hold', 'Move', 'Support hold', 'Support move', 'Convoy', 'Retreat', 'Disband',
                              'Build Army', 'Build Fleet', 'Wait', 'Destroy'):
            LOGGER.error('Received invalid order type "%s".', order_type)
            return
        if terr_id not in CACHE[self.map_name]['ix_to_loc'] and terr_id is not None:
            LOGGER.error('Received invalid loc "%s" for map "%s".', terr_id, self.map_name)
            return
        if via_convoy not in ('Yes', 'No', '', None):
            LOGGER.error('Received invalid via convoy "%s". Expected "Yes" or "No" or "".', via_convoy)
            return

        # Extracting locations
        loc_name = CACHE[self.map_name]['ix_to_loc'].get(terr_id, None)
        to_loc_name = CACHE[self.map_name]['ix_to_loc'].get(to_terr_id, None)
        from_loc_name = CACHE[self.map_name]['ix_to_loc'].get(from_terr_id, None)

        # Building order
        # --- Hold ---
        # {"id": "76", "unitID": "19", "type": "Hold", "toTerrID": "", "fromTerrID": "", "viaConvoy": ""}
        if order_type == 'Hold':
            self.order_str = '%s %s H' % (unit_type[0], loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Hold',
                               'toTerrID': '',
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Move ---
        # {"id": "73", "unitID": "16", "type": "Move", "toTerrID": "25", "fromTerrID": "", "viaConvoy": "Yes",
        # "convoyPath": ["22", "69"]},
        # {"id": "74", "unitID": "17", "type": "Move", "toTerrID": "69", "fromTerrID": "", "viaConvoy": "No"}
        elif order_type == 'Move':
            if to_loc_name is None:
                LOGGER.error('[Move] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return

            # We don't need to set the "convoyPath" property if we are converting from an order_dict
            via_flag = ' VIA' if via_convoy == 'Yes' else ''
            self.order_str = '%s %s - %s%s' % (unit_type[0], loc_name, to_loc_name, via_flag)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Move',
                               'toTerrID': to_terr_id,
                               'fromTerrID': '',
                               'viaConvoy': via_convoy}

        # --- Support hold ---
        # {"id": "73", "unitID": "16", "type": "Support hold", "toTerrID": "24", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'Support hold':
            if to_loc_name is None:
                LOGGER.error('[Support H] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return
            self.order_str = '%s %s S %s' % (unit_type[0], loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Support hold',
                               'toTerrID': to_terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Support move ---
        # {"id": "73", "unitID": "16", "type": "Support move", "toTerrID": "24", "fromTerrID": "69", "viaConvoy": ""}
        elif order_type == 'Support move':
            if to_loc_name is None:
                LOGGER.error('[Support M] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return
            if from_loc_name is None:
                LOGGER.error('[Support M] Received invalid from loc "%s" for map "%s".', from_terr_id, self.map_name)
                LOGGER.error(order)
                return
            self.order_str = '%s %s S %s - %s' % (unit_type[0], loc_name, from_loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Support move',
                               'toTerrID': to_terr_id,
                               'fromTerrID': from_terr_id,
                               'viaConvoy': ''}

        # --- Convoy ---
        # {"id": "79", "unitID": "22", "type": "Convoy", "toTerrID": "24", "fromTerrID": "20", "viaConvoy": "",
        # "convoyPath": ["20", "69"]}
        elif order_type == 'Convoy':
            if to_loc_name is None:
                LOGGER.error('[Convoy] Received invalid to loc "%s" for map "%s".', to_terr_id, self.map_name)
                LOGGER.error(order)
                return
            if from_loc_name is None:
                LOGGER.error('[Convoy] Received invalid from loc "%s" for map "%s".', from_terr_id, self.map_name)
                LOGGER.error(order)
                return

            # We don't need to set the "convoyPath" property if we are converting from an order_dict
            self.order_str = '%s %s C A %s - %s' % (unit_type[0], loc_name, from_loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Convoy',
                               'toTerrID': to_terr_id,
                               'fromTerrID': from_terr_id,
                               'viaConvoy': ''}

        # --- Retreat ---
        # {"id": "152", "unitID": "18", "type": "Retreat", "toTerrID": "75", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'Retreat':
            if to_loc_name is None:
                return
            self.order_str = '%s %s R %s' % (unit_type[0], loc_name, to_loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Retreat',
                               'toTerrID': to_terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Disband ---
        # {"id": "152", "unitID": "18", "type": "Disband", "toTerrID": "", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'Disband':
            self.order_str = '%s %s D' % (unit_type[0], loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Disband',
                               'toTerrID': '',
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Build Army ---
        # [{"id": "56", "unitID": null, "type": "Build Army", "toTerrID": "37", "fromTerrID": "", "viaConvoy": ""}]
        elif order_type == 'Build Army':
            self.order_str = 'A %s B' % loc_name
            self.order_dict = {'terrID': terr_id,
                               'unitType': 'Army',
                               'type': 'Build Army',
                               'toTerrID': terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Build Fleet ---
        # [{"id": "56", "unitID": null, "type": "Build Fleet", "toTerrID": "37", "fromTerrID": "", "viaConvoy": ""}]
        elif order_type == 'Build Fleet':
            self.order_str = 'F %s B' % loc_name
            self.order_dict = {'terrID': terr_id,
                               'unitType': 'Fleet',
                               'type': 'Build Fleet',
                               'toTerrID': terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # --- Wait / Waive ---
        # [{"id": "56", "unitID": null, "type": "Wait", "toTerrID": "", "fromTerrID": "", "viaConvoy": ""}]
        elif order_type == 'Wait':
            self.order_str = 'WAIVE'
            self.order_dict = {'terrID': None,
                               'unitType': '',
                               'type': 'Wait',
                               'toTerrID': '',
                               'fromTerrID': '',
                               'viaConvoy': ''}

        # Disband (A phase)
        # {"id": "152", "unitID": null, "type": "Destroy", "toTerrID": "18", "fromTerrID": "", "viaConvoy": ""}
        elif order_type == 'Destroy':
            self.order_str = '%s %s D' % (unit_type[0], loc_name)
            self.order_dict = {'terrID': terr_id,
                               'unitType': unit_type,
                               'type': 'Destroy',
                               'toTerrID': terr_id,
                               'fromTerrID': '',
                               'viaConvoy': ''}

    def __bool__(self):
        """ Returns True if an order was parsed, False otherwise """
        return bool(self.order_str != '')

    def __str__(self):
        """ Returns the string representation of the order """
        return self.order_str

    def to_string(self):
        """ Returns the string representation of the order """
        return self.order_str

    def to_norm_string(self):
        """ Returns a normalized order string """
        if self.order_str[-2:] == ' D':
            order_str = '? ' + self.order_str[2:]
        else:
            order_str = self.order_str
        return order_str\
            .replace(' S A ', ' S ')\
            .replace(' S F ', ' S ') \
            .replace(' C A ', ' C ') \
            .replace(' C F ', ' C ') \
            .replace(' VIA', '')

    def to_dict(self):
        """ Returns the dictionary representation of the order """
        return self.order_dict
