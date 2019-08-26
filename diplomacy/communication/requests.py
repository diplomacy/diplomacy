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
""" Client -> Server requests.
    Notes:
        If an error occurred on server-side while handling a request, client will receive
        a ResponseException containing message about handling error. Request exceptions
        are currently not more typed on client-side.
"""
import inspect
import logging

from diplomacy.engine.message import Message
from diplomacy.utils import common, exceptions, parsing, strings
from diplomacy.utils.network_data import NetworkData
from diplomacy.utils.parsing import OptionalValueType
from diplomacy.utils.sorted_dict import SortedDict

LOGGER = logging.getLogger(__name__)

class _AbstractRequest(NetworkData):
    """ Abstract request class.

        Field request_id is auto-filled if not defined.

        Field name is auto-filled with snake case version of request class name.

        Field re_sent is False by default. It should be set to True if request is re-sent by client
        (currently done by Connection object when reconnecting).

        Timestamp field is auto-set with current local timestamp if not defined.
        For game request Synchronize, timestamp should be game latest timestamp instead
        (see method NetworkGame.synchronize()).
    """

    __slots__ = ['request_id', 're_sent']
    header = {
        strings.REQUEST_ID: str,
        strings.NAME: str,
        strings.RE_SENT: parsing.DefaultValueType(bool, False),
    }
    params = {}
    id_field = strings.REQUEST_ID
    level = None

    def __init__(self, **kwargs):
        self.request_id = None  # type: str
        self.re_sent = None  # type: bool
        super(_AbstractRequest, self).__init__(**kwargs)

    @classmethod
    def validate_params(cls):
        """ Hack: we just use it to validate level. """
        assert cls.level is None or cls.level in strings.ALL_COMM_LEVELS

class _AbstractChannelRequest(_AbstractRequest):
    """ Abstract class representing a channel request.
        Token field is automatically filled by a Channel object before sending request.
    """

    __slots__ = ['token']
    header = parsing.update_model(_AbstractRequest.header, {
        strings.TOKEN: str
    })
    level = strings.CHANNEL

    def __init__(self, **kwargs):
        self.token = None  # type: str
        super(_AbstractChannelRequest, self).__init__(**kwargs)

class _AbstractGameRequest(_AbstractChannelRequest):
    """ Abstract class representing a game request.
        Game ID, game role and phase fields are automatically filled by a NetworkGame object before sending request.
    """

    __slots__ = ['game_id', 'game_role', 'phase']

    header = parsing.extend_model(_AbstractChannelRequest.header, {
        strings.GAME_ID: str,
        strings.GAME_ROLE: str,
        strings.PHASE: str,  # Game short phase.
    })
    level = strings.GAME

    # Game request class flag to indicate if this type of game request depends on game phase.
    # If True, phase indicated in request must match current game phase.
    phase_dependent = True

    def __init__(self, **kwargs):
        self.game_id = None  # type: str
        self.game_role = None  # type: str
        self.phase = None  # type: str
        super(_AbstractGameRequest, self).__init__(**kwargs)

    # Return "address" of request sender inside related game (ie. channel token + game role).
    # Used by certain request managers to skip sender when notify related game.
    # See request managers in diplomacy.server.request_managers.
    address_in_game = property(lambda self: (self.game_role, self.token))

# ====================
# Connection requests.
# ====================

class GetDaidePort(_AbstractRequest):
    """ Get game DAIDE port """
    __slots__ = ['game_id']
    params = {
        strings.GAME_ID: str
    }

    def __init__(self, **kwargs):
        self.game_id = None
        super(GetDaidePort, self).__init__(**kwargs)

class SignIn(_AbstractRequest):
    """ SignIn request.
        Expected response: responses.DataToken
        Expected response handler result: diplomacy.client.channel.Channel
    """
    __slots__ = ['username', 'password', 'create_user']
    params = {
        strings.USERNAME: str,
        strings.PASSWORD: str,
        strings.CREATE_USER: bool
    }

    def __init__(self, **kwargs):
        self.username = None
        self.password = None
        self.create_user = None
        super(SignIn, self).__init__(**kwargs)

# =================
# Channel requests.
# =================

class CreateGame(_AbstractChannelRequest):
    """ CreateGame request.
        Expected response: responses.DataGame
        Expected response handler result: diplomacy.client.network_game.NetworkGame
    """
    __slots__ = ['game_id', 'power_name', 'state', 'map_name', 'rules', 'n_controls', 'deadline',
                 'registration_password']
    params = {
        strings.GAME_ID: parsing.OptionalValueType(str),
        strings.N_CONTROLS: parsing.OptionalValueType(int),
        strings.DEADLINE: parsing.DefaultValueType(int, 300),  # 300 seconds. Must be >= 0.
        strings.REGISTRATION_PASSWORD: parsing.OptionalValueType(str),
        strings.POWER_NAME: parsing.OptionalValueType(str),
        strings.STATE: parsing.OptionalValueType(dict),
        strings.MAP_NAME: parsing.DefaultValueType(str, 'standard'),
        strings.RULES: parsing.OptionalValueType(parsing.SequenceType(str, sequence_builder=set)),
    }

    def __init__(self, **kwargs):
        self.game_id = ''
        self.n_controls = 0
        self.deadline = 0
        self.registration_password = ''
        self.power_name = ''
        self.state = {}
        self.map_name = ''
        self.rules = set()
        super(CreateGame, self).__init__(**kwargs)

class DeleteAccount(_AbstractChannelRequest):
    """ DeleteAccount request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['username']
    params = {
        strings.USERNAME: OptionalValueType(str)
    }

    def __init__(self, **kwargs):
        self.username = None
        super(DeleteAccount, self).__init__(**kwargs)

class GetDummyWaitingPowers(_AbstractChannelRequest):
    """ GetDummyWaitingPowers request.
        Expected response: response.DataGamesToPowerNames
        Expected response handler result: {dict mapping game IDs to lists of dummy powers names}
    """
    __slots__ = ['buffer_size']
    params = {
        strings.BUFFER_SIZE: int,
    }

    def __init__(self, **kwargs):
        self.buffer_size = 0
        super(GetDummyWaitingPowers, self).__init__(**kwargs)

class GetAvailableMaps(_AbstractChannelRequest):
    """ GetAvailableMaps request.
        Expected response: responses.DataMaps
        Expected response handler result: {map name => [map power names]}
    """
    __slots__ = []

class GetPlayablePowers(_AbstractChannelRequest):
    """ GetPlayablePowers request.
        Expected response: responses.DataPowerNames
        Expected response handler result: [power names]
    """
    __slots__ = ['game_id']
    params = {
        strings.GAME_ID: str
    }

    def __init__(self, **kwargs):
        self.game_id = None
        super(GetPlayablePowers, self).__init__(**kwargs)

class JoinGame(_AbstractChannelRequest):
    """ JoinGame request.
        Expected response: responses.DataGame
        Expected response handler result: diplomacy.client.network_game.NetworkGame
    """
    __slots__ = ['game_id', 'power_name', 'registration_password']
    params = {
        strings.GAME_ID: str,
        strings.POWER_NAME: parsing.OptionalValueType(str),
        strings.REGISTRATION_PASSWORD: parsing.OptionalValueType(str)
    }

    def __init__(self, **kwargs):
        self.game_id = None
        self.power_name = None
        self.registration_password = None
        super(JoinGame, self).__init__(**kwargs)

class JoinPowers(_AbstractChannelRequest):
    """ JoinPowers request to join many powers of a game with one query.
        Useful to control many powers while still working only with 1 client game instance.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['game_id', 'power_names', 'registration_password']
    params = {
        strings.GAME_ID: str,
        strings.POWER_NAMES: parsing.SequenceType(str, sequence_builder=set),
        strings.REGISTRATION_PASSWORD: parsing.OptionalValueType(str)
    }

    def __init__(self, **kwargs):
        self.game_id = None
        self.power_names = None
        self.registration_password = None
        super(JoinPowers, self).__init__(**kwargs)

class ListGames(_AbstractChannelRequest):
    """ ListGames request.
        Expected response: responses.DataGames
        Expected response handler result: responses.DataGames
    """
    __slots__ = ['game_id', 'status', 'map_name', 'include_protected', 'for_omniscience']
    params = {
        strings.STATUS: OptionalValueType(parsing.EnumerationType(strings.ALL_GAME_STATUSES)),
        strings.MAP_NAME: OptionalValueType(str),
        strings.INCLUDE_PROTECTED: parsing.DefaultValueType(bool, True),
        strings.FOR_OMNISCIENCE: parsing.DefaultValueType(bool, False),
        strings.GAME_ID: OptionalValueType(str),
    }

    def __init__(self, **kwargs):
        self.game_id = None
        self.status = None
        self.map_name = None
        self.include_protected = None
        self.for_omniscience = None
        super(ListGames, self).__init__(**kwargs)

class GetGamesInfo(_AbstractChannelRequest):
    """ Request used to get info for a given list of game IDs.
        Expected response: responses.DataGames
        Expected response handler result: responses.DataGames
    """
    __slots__ = ['games']
    params = {
        strings.GAMES: parsing.SequenceType(str)
    }
    def __init__(self, **kwargs):
        self.games = []
        super(GetGamesInfo, self).__init__(**kwargs)

class Logout(_AbstractChannelRequest):
    """ Logout request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = []

class UnknownToken(_AbstractChannelRequest):
    """ Request to tell server that a channel token is unknown.
        Expected response: Nothing - Client does not even wait for a server response.
        Expected response handler result: None
    """
    __slots__ = []

class SetGrade(_AbstractChannelRequest):
    """ SetGrade request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['grade', 'grade_update', 'username', 'game_id']
    params = {
        strings.GRADE: parsing.EnumerationType(strings.ALL_GRADES),
        strings.GRADE_UPDATE: parsing.EnumerationType(strings.ALL_GRADE_UPDATES),
        strings.USERNAME: str,
        strings.GAME_ID: parsing.OptionalValueType(str),
    }

    def __init__(self, **kwargs):
        self.grade = None
        self.grade_update = None
        self.username = None
        self.game_id = None
        super(SetGrade, self).__init__(**kwargs)

# ==============
# Game requests.
# ==============

class ClearCenters(_AbstractGameRequest):
    """ ClearCenters request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['power_name']
    params = {
        strings.POWER_NAME: parsing.OptionalValueType(str),
    }

    def __init__(self, **kwargs):
        self.power_name = None  # type: str
        super(ClearCenters, self).__init__(**kwargs)

class ClearOrders(_AbstractGameRequest):
    """ ClearOrders request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['power_name']
    params = {
        strings.POWER_NAME: parsing.OptionalValueType(str),
    }

    def __init__(self, **kwargs):
        self.power_name = None  # type: str
        super(ClearOrders, self).__init__(**kwargs)

class ClearUnits(_AbstractGameRequest):
    """ ClearUnits request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['power_name']
    params = {
        strings.POWER_NAME: parsing.OptionalValueType(str),
    }

    def __init__(self, **kwargs):
        self.power_name = None  # type: str
        super(ClearUnits, self).__init__(**kwargs)

class DeleteGame(_AbstractGameRequest):
    """ DeleteGame request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = []
    phase_dependent = False

class GetAllPossibleOrders(_AbstractGameRequest):
    """ GetAllPossibleOrders request.
        Expected response: response.DataPossibleOrders
        Expected response handler result: response.DataPossibleOrders
    """
    __slots__ = []

class GetPhaseHistory(_AbstractGameRequest):
    """ Get a list of game phase data from game history for given phases interval.
        A phase can be either None, a phase name (string) or a phase index (integer).
        Expected response: responses.DataGamePhases
        Expected response handler result: [GamePhaseData objects]
    """
    __slots__ = ['from_phase', 'to_phase']
    params = {
        strings.FROM_PHASE: parsing.OptionalValueType(parsing.SequenceOfPrimitivesType([str, int])),
        strings.TO_PHASE: parsing.OptionalValueType(parsing.SequenceOfPrimitivesType([str, int])),
    }
    phase_dependent = False

    def __init__(self, **kwargs):
        self.from_phase = ''
        self.to_phase = ''
        super(GetPhaseHistory, self).__init__(**kwargs)

class LeaveGame(_AbstractGameRequest):
    """ LeaveGame request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = []

class ProcessGame(_AbstractGameRequest):
    """ ProcessGame request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = []

class QuerySchedule(_AbstractGameRequest):
    """ Query server for info about current scheduling for a game.
        Expected response: response.DataGameSchedule
        Expected response handler result: response.DataGameSchedule
    """
    __slots__ = []

class SaveGame(_AbstractGameRequest):
    """ Get game saved format in JSON.
        Expected response: response.DataSavedGame
        Expected response handler result: response.DataSavedGame
    """
    __slots__ = []

class SendGameMessage(_AbstractGameRequest):
    """ SendGameMessage request.
        Expected response: responses.DataTimeStamp
        Expected response handler result: None
    """
    __slots__ = ['message']
    params = {
        strings.MESSAGE: parsing.JsonableClassType(Message)
    }

    def __init__(self, **kwargs):
        self.message = None  # type: Message
        super(SendGameMessage, self).__init__(**kwargs)

class SetDummyPowers(_AbstractGameRequest):
    """ SetDummyPowers request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['username', 'power_names']
    params = {
        strings.USERNAME: parsing.OptionalValueType(str),
        strings.POWER_NAMES: parsing.OptionalValueType(parsing.SequenceType(str)),
    }

    def __init__(self, **kwargs):
        self.username = None
        self.power_names = None
        super(SetDummyPowers, self).__init__(**kwargs)

class SetGameState(_AbstractGameRequest):
    """ Request to set a game state.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['state', 'orders', 'results', 'messages']
    params = {
        strings.STATE: dict,
        strings.ORDERS: parsing.DictType(str, parsing.SequenceType(str)),
        strings.RESULTS: parsing.DictType(str, parsing.SequenceType(str)),
        strings.MESSAGES: parsing.DictType(int, parsing.JsonableClassType(Message), SortedDict.builder(int, Message)),
    }

    def __init__(self, **kwargs):
        self.state = {}
        self.orders = {}
        self.results = {}
        self.messages = {}  # type: SortedDict
        super(SetGameState, self).__init__(**kwargs)

class SetGameStatus(_AbstractGameRequest):
    """ SetGameStatus request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['status']
    params = {
        strings.STATUS: parsing.EnumerationType(strings.ALL_GAME_STATUSES),
    }

    def __init__(self, **kwargs):
        self.status = None
        super(SetGameStatus, self).__init__(**kwargs)

class SetOrders(_AbstractGameRequest):
    """ SetOrders request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['power_name', 'orders', 'wait']
    params = {
        strings.POWER_NAME: parsing.OptionalValueType(str),  # required only for game master.
        strings.ORDERS: parsing.SequenceType(str),
        strings.WAIT: parsing.OptionalValueType(bool)
    }

    def __init__(self, **kwargs):
        self.power_name = None
        self.orders = None
        self.wait = None
        super(SetOrders, self).__init__(**kwargs)

class SetWaitFlag(_AbstractGameRequest):
    """ SetWaitFlag request.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['power_name', 'wait']
    params = {
        strings.POWER_NAME: parsing.OptionalValueType(str),  # required only for game master.
        strings.WAIT: bool
    }

    def __init__(self, **kwargs):
        self.power_name = None
        self.wait = None
        super(SetWaitFlag, self).__init__(**kwargs)

class Synchronize(_AbstractGameRequest):
    """ Synchronize request.
        Expected response: responses.DataGameInfo
        Expected response handler result: DataGameInfo
    """
    __slots__ = ['timestamp']
    params = {
        strings.TIMESTAMP: int
    }
    phase_dependent = False

    def __init__(self, **kwargs):
        self.timestamp = None  # type: int
        super(Synchronize, self).__init__(**kwargs)

class Vote(_AbstractGameRequest):
    """ Vote request.
        For powers only.
        Allow a power to vote about game draw for current phase.
        Expected response: responses.Ok
        Expected response handler result: None
    """
    __slots__ = ['power_name', 'vote']
    params = {
        strings.POWER_NAME: parsing.OptionalValueType(str),
        strings.VOTE: strings.ALL_VOTE_DECISIONS
    }

    def __init__(self, **kwargs):
        self.power_name = ''
        self.vote = ''
        super(Vote, self).__init__(**kwargs)

def parse_dict(json_request):
    """ Parse a JSON dictionary expected to represent a request. Raise an exception if parsing failed.
        :param json_request: JSON dictionary.
        :return: a request class instance.
        :type json_request: dict
        :rtype: _AbstractRequest | _AbstractChannelRequest | _AbstractGameRequest
    """
    name = json_request.get(strings.NAME, None)
    if name is None:
        raise exceptions.RequestException()
    expected_class_name = common.snake_case_to_upper_camel_case(name)
    request_class = globals().get(expected_class_name, None)
    if request_class is None or not inspect.isclass(request_class) or not issubclass(request_class, _AbstractRequest):
        raise exceptions.RequestException('Unknown request name %s' % expected_class_name)
    try:
        return request_class.from_dict(json_request)
    except exceptions.DiplomacyException as exc:
        LOGGER.error('%s/%s', type(exc).__name__, exc.message)
        raise exceptions.RequestException('Wrong request format')
