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
""" Utility class to save all data related to one game phase (phase name, state, messages and orders). """
from diplomacy.engine.message import Message
from diplomacy.utils import common, strings, parsing
from diplomacy.utils.jsonable import Jsonable
from diplomacy.utils.sorted_dict import SortedDict

MESSAGES_TYPE = parsing.IndexedSequenceType(
    parsing.DictType(int, parsing.JsonableClassType(Message), SortedDict.builder(int, Message)), 'time_sent')

class GamePhaseData(Jsonable):
    """ Small class to represent data for a game phase:
        phase name, state, orders, orders results and messages for this phase.
    """
    __slots__ = ['name', 'state', 'orders', 'results', 'messages']

    model = {
        strings.NAME: str,
        strings.STATE: dict,
        strings.ORDERS: parsing.DictType(str, parsing.OptionalValueType(parsing.SequenceType(str))),
        strings.RESULTS: parsing.DictType(str, parsing.SequenceType(parsing.StringableType(common.StringableCode))),
        strings.MESSAGES: MESSAGES_TYPE,
    }

    def __init__(self, name, state, orders, results, messages):
        """ Constructor. """
        self.name = ''
        self.state = {}
        self.orders = {}
        self.results = {}
        self.messages = {}
        super(GamePhaseData, self).__init__(name=name, state=state, orders=orders, results=results, messages=messages)
