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
""" Server -> Client responses sent by server when it received a request. """
import inspect

from diplomacy.engine.game import Game
from diplomacy.utils import common, parsing, strings
from diplomacy.utils.scheduler_event import SchedulerEvent
from diplomacy.utils.exceptions import ResponseException
from diplomacy.utils.network_data import NetworkData
from diplomacy.utils.game_phase_data import GamePhaseData

class _AbstractResponse(NetworkData):
    """ Base response object """
    __slots__ = ['request_id']
    header = {
        strings.REQUEST_ID: str,
        strings.NAME: str,
    }
    id_field = strings.REQUEST_ID

    def __init__(self, **kwargs):
        self.request_id = None
        super(_AbstractResponse, self).__init__(**kwargs)

class Error(_AbstractResponse):
    """ Error response sent when an error occurred on server-side while handling a request. """
    __slots__ = ['message']
    params = {
        strings.MESSAGE: str
    }

    def __init__(self, **kwargs):
        self.message = None
        super(Error, self).__init__(**kwargs)

class Ok(_AbstractResponse):
    """ Ok response sent by default after handling a request. """
    __slots__ = []

class NoResponse(_AbstractResponse):
    """ Indicates that no responses are required """
    __slots__ = []

    def __bool__(self):
        """ This response always evaluate to false """
        return False

class DataGameSchedule(_AbstractResponse):
    """ Response with info about current scheduling for a game. """
    __slots__ = ['game_id', 'phase', 'schedule']
    params = {
        'game_id': str,
        'phase': str,
        'schedule': parsing.JsonableClassType(SchedulerEvent)
    }

    def __init__(self, **kwargs):
        self.game_id = ''
        self.phase = ''
        self.schedule = None  # type: SchedulerEvent
        super(DataGameSchedule, self).__init__(**kwargs)

class DataGameInfo(_AbstractResponse):
    """ Response containing information about a game, to be used when no entire game object is required. """
    __slots__ = ['game_id', 'phase', 'timestamp', 'map_name', 'rules', 'status', 'n_players', 'n_controls',
                 'deadline', 'registration_password', 'observer_level', 'controlled_powers',
                 'timestamp_created']
    params = {
        strings.GAME_ID: str,
        strings.PHASE: str,
        strings.TIMESTAMP: int,
        strings.TIMESTAMP_CREATED: int,
        strings.MAP_NAME: parsing.OptionalValueType(str),
        strings.OBSERVER_LEVEL: parsing.OptionalValueType(
            parsing.EnumerationType((strings.MASTER_TYPE, strings.OMNISCIENT_TYPE, strings.OBSERVER_TYPE))),
        strings.CONTROLLED_POWERS: parsing.OptionalValueType(parsing.SequenceType(str)),
        strings.RULES: parsing.OptionalValueType(parsing.SequenceType(str)),
        strings.STATUS: parsing.OptionalValueType(parsing.EnumerationType(strings.ALL_GAME_STATUSES)),
        strings.N_PLAYERS: parsing.OptionalValueType(int),
        strings.N_CONTROLS: parsing.OptionalValueType(int),
        strings.DEADLINE: parsing.OptionalValueType(int),
        strings.REGISTRATION_PASSWORD: parsing.OptionalValueType(bool)
    }

    def __init__(self, **kwargs):
        self.game_id = None  # type: str
        self.phase = None  # type: str
        self.timestamp = None  # type: int
        self.timestamp_created = None  # type: int
        self.map_name = None  # type: str
        self.observer_level = None  # type: str
        self.controlled_powers = None  # type: list
        self.rules = None  # type: list
        self.status = None  # type: str
        self.n_players = None  # type: int
        self.n_controls = None  # type: int
        self.deadline = None  # type: int
        self.registration_password = None  # type: bool
        super(DataGameInfo, self).__init__(**kwargs)

class DataPossibleOrders(_AbstractResponse):
    """ Response containing a dict of all possibles orders per location and a dict of all orderable locations per power
        for a game phase.
    """
    __slots__ = ['possible_orders', 'orderable_locations']
    params = {
        # {location => [orders]}
        strings.POSSIBLE_ORDERS: parsing.DictType(str, parsing.SequenceType(str)),
        # {power name => [locations]}
        strings.ORDERABLE_LOCATIONS: parsing.DictType(str, parsing.SequenceType(str)),
    }
    def __init__(self, **kwargs):
        self.possible_orders = {}
        self.orderable_locations = {}
        super(DataPossibleOrders, self).__init__(**kwargs)

class UniqueData(_AbstractResponse):
    """ Response containing only 1 field named `data`.
        `params` must have exactly one field named DATA.
    """
    __slots__ = ['data']

    @classmethod
    def validate_params(cls):
        assert len(cls.params) == 1 and strings.DATA in cls.params

    def __init__(self, **kwargs):
        self.data = None
        super(UniqueData, self).__init__(**kwargs)

class DataToken(UniqueData):
    """ Unique data containing a token. """
    __slots__ = []
    params = {
        strings.DATA: str
    }

class DataMaps(UniqueData):
    """ Unique data containing maps info. """
    __slots__ = []
    params = {
        # {map_id => {'powers': [power names], 'supply centers' => [supply centers], 'loc_type' => {loc => type}}}
        strings.DATA: dict
    }

class DataPowerNames(UniqueData):
    """ Unique data containing a list of power names. """
    __slots__ = []
    params = {
        strings.DATA: parsing.SequenceType(str)
    }

class DataGames(UniqueData):
    """ Unique data containing a list of game info objects. """
    __slots__ = []
    params = {
        strings.DATA: parsing.SequenceType(parsing.JsonableClassType(DataGameInfo))  # list of game info.
    }

class DataPort(UniqueData):
    """ Unique data containing a DAIDE port. """
    __slots__ = []
    params = {
        strings.DATA: int   # DAIDE port
    }

class DataTimeStamp(UniqueData):
    """ Unique data containing a timestamp. """
    __slots__ = []
    params = {
        strings.DATA: int  # microseconds
    }

class DataGamePhases(UniqueData):
    """ Unique data containing a list of GamePhaseData objects. """
    __slots__ = []
    params = {
        strings.DATA: parsing.SequenceType(parsing.JsonableClassType(GamePhaseData))
    }

class DataGame(UniqueData):
    """ Unique data containing a Game object. """
    __slots__ = []
    params = {
        strings.DATA: parsing.JsonableClassType(Game)
    }

class DataSavedGame(UniqueData):
    """ Unique data containing a game saved in JSON format. """
    __slots__ = []
    params = {
        strings.DATA: dict
    }

class DataGamesToPowerNames(UniqueData):
    """ Unique data containing a dict of game IDs associated to sequences of power names. """
    __slots__ = []
    params = {
        strings.DATA: parsing.DictType(str, parsing.SequenceType(str))
    }

def parse_dict(json_response):
    """ Parse a JSON dictionary expected to represent a response.
        Raise an exception if either:
        - parsing failed
        - response received is an Error response. In such case, a ResponseException is raised
          with the error message.
        :param json_response: a JSON dict.
        :return: a Response class instance.
    """
    assert isinstance(json_response, dict), 'Response parser expects a dict.'
    name = json_response.get(strings.NAME, None)
    if name is None:
        raise ResponseException()
    expected_class_name = common.snake_case_to_upper_camel_case(name)
    response_class = globals()[expected_class_name]
    assert inspect.isclass(response_class) and issubclass(response_class, _AbstractResponse)
    response_object = response_class.from_dict(json_response)
    if isinstance(response_object, Error):
        raise ResponseException('%s: %s' % (response_object.name, response_object.message))
    return response_object
