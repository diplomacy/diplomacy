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
""" Channel
    - The channel object represents an authenticated connection over a socket.
    - It has a token that it sends with every request to authenticate itself.
"""
import logging

from tornado import gen

from diplomacy.communication import requests
from diplomacy.utils import strings

LOGGER = logging.getLogger(__name__)

def req_fn(request_class, local_req_fn=None, **request_args):
    """ Create channel request method that sends request with channel token.
        :param request_class: class of request to send with channel request method.
        :param local_req_fn: (optional) Channel method to use locally to try retrieving a data
            instead of sending a request. If provided, local_req_fn is called with request args:
            - if it returns anything else than None, then returned data is returned by channel request method.
            - else, request class is still sent and channel request method follows standard path
              (request sent, response received, response handler called and final handler result returned).
        :param request_args: arguments to pass to request class to create the request object.
        :return: a Channel method.
    """

    @gen.coroutine
    def func(self, game_object=None, **kwargs):
        """ Send an instance of request_class with given kwargs and game object.
            :param self: Channel object who sends the request.
            :param game_object: (optional) a NetworkGame object (required for game requests).
            :param kwargs: request arguments.
            :return: Data returned after response is received and handled by associated response manager.
                See module diplomacy.client.response_managers about responses management.
            :type game_object: diplomacy.client.network_game.NetworkGame
        """
        kwargs.update(request_args)
        if request_class.level == strings.GAME:
            assert game_object is not None
            kwargs[strings.TOKEN] = self.token
            kwargs[strings.GAME_ID] = game_object.game_id
            kwargs[strings.GAME_ROLE] = game_object.role
            kwargs[strings.PHASE] = game_object.current_short_phase
        else:
            assert game_object is None
            if request_class.level == strings.CHANNEL:
                kwargs[strings.TOKEN] = self.token
        if local_req_fn is not None:
            local_ret = local_req_fn(self, **kwargs)
            if local_ret is not None:
                return local_ret
        request = request_class(**kwargs)
        return (yield self.connection.send(request, game_object))

    return func

class Channel():
    """ Channel - Represents an authenticated connection over a physical socket """
    __slots__ = ['connection', 'token', 'game_id_to_instances', '__weakref__']

    def __init__(self, connection, token):
        """ Initialize a channel.
            :param connection: a Connection object.
            :param token: Channel token.
            :type connection: diplomacy.Connection
        """
        self.connection = connection
        self.token = token
        self.game_id_to_instances = {}  # {game id => GameInstances}

    def local_join_game(self, **kwargs):
        """ Look for a local game with given kwargs intended to be used to build a JoinGame request.
            Return None if no local game found, else local game found.
            Game is identified with game ID and power name (optional).
            If power name is None, we look for a "special" game (observer or omniscient game)
            loaded locally. Note that there is at most 1 special game per channel + game ID:
            either observer or omniscient, not both.
        """
        game_id = kwargs[strings.GAME_ID]
        power_name = kwargs.get(strings.POWER_NAME, None)
        if game_id in self.game_id_to_instances:
            if power_name is not None:
                return self.game_id_to_instances[game_id].get(power_name)
            return self.game_id_to_instances[game_id].get_special()
        return None

    # ===================
    # Public channel API.
    # ===================

    create_game = req_fn(requests.CreateGame)
    get_available_maps = req_fn(requests.GetAvailableMaps)
    get_playable_powers = req_fn(requests.GetPlayablePowers)
    join_game = req_fn(requests.JoinGame, local_req_fn=local_join_game)
    join_powers = req_fn(requests.JoinPowers)
    list_games = req_fn(requests.ListGames)
    get_games_info = req_fn(requests.GetGamesInfo)

    # User Account API.
    delete_account = req_fn(requests.DeleteAccount)
    logout = req_fn(requests.Logout)

    # Admin / Moderator API.
    make_omniscient = req_fn(requests.SetGrade, grade=strings.OMNISCIENT, grade_update=strings.PROMOTE)
    remove_omniscient = req_fn(requests.SetGrade, grade=strings.OMNISCIENT, grade_update=strings.DEMOTE)
    promote_administrator = req_fn(requests.SetGrade, grade=strings.ADMIN, grade_update=strings.PROMOTE)
    demote_administrator = req_fn(requests.SetGrade, grade=strings.ADMIN, grade_update=strings.DEMOTE)
    promote_moderator = req_fn(requests.SetGrade, grade=strings.MODERATOR, grade_update=strings.PROMOTE)
    demote_moderator = req_fn(requests.SetGrade, grade=strings.MODERATOR, grade_update=strings.DEMOTE)

    # ================
    # Public game API.
    # ================

    get_dummy_waiting_powers = req_fn(requests.GetDummyWaitingPowers)
    get_phase_history = req_fn(requests.GetPhaseHistory)
    leave_game = req_fn(requests.LeaveGame)
    send_game_message = req_fn(requests.SendGameMessage)
    set_orders = req_fn(requests.SetOrders)

    clear_centers = req_fn(requests.ClearCenters)
    clear_orders = req_fn(requests.ClearOrders)
    clear_units = req_fn(requests.ClearUnits)

    wait = req_fn(requests.SetWaitFlag, wait=True)
    no_wait = req_fn(requests.SetWaitFlag, wait=False)
    vote = req_fn(requests.Vote)
    save = req_fn(requests.SaveGame)
    synchronize = req_fn(requests.Synchronize)

    # Admin / Moderator API.
    delete_game = req_fn(requests.DeleteGame)
    kick_powers = req_fn(requests.SetDummyPowers)
    set_state = req_fn(requests.SetGameState)
    process = req_fn(requests.ProcessGame)
    query_schedule = req_fn(requests.QuerySchedule)
    start = req_fn(requests.SetGameStatus, status=strings.ACTIVE)
    pause = req_fn(requests.SetGameStatus, status=strings.PAUSED)
    resume = req_fn(requests.SetGameStatus, status=strings.ACTIVE)
    cancel = req_fn(requests.SetGameStatus, status=strings.CANCELED)
    draw = req_fn(requests.SetGameStatus, status=strings.COMPLETED)
