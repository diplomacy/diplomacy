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
""" Contains the base API class """
from abc import ABCMeta, abstractmethod
import logging
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

# Constants
LOGGER = logging.getLogger(__name__)

class BaseAPI(metaclass=ABCMeta):
    """ Base API class """

    def __init__(self, api_key, connect_timeout=30, request_timeout=60):
        """ Constructor
            :param api_key: The API key to use for sending API requests
            :param connect_timeout: The maximum amount of time to wait for the connection to be established
            :param request_timeout: The maximum amount of time to wait for the request to be processed
        """
        self.api_key = api_key
        self.http_client = AsyncHTTPClient()
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout

    @gen.coroutine
    @abstractmethod
    def list_games_with_players_in_cd(self):
        """ Lists the game on the standard map where a player is in CD and the bots needs to submit orders
            :return: List of GameIdCountryId tuples  [(game_id, country_id), (game_id, country_id)]
        """
        raise NotImplementedError()

    @gen.coroutine
    @abstractmethod
    def list_games_with_missing_orders(self):
        """ Lists of the game on the standard where the user has not submitted orders yet.
            :return: List of GameIdCountryId tuples  [(game_id, country_id), (game_id, country_id)]
        """
        raise NotImplementedError()

    @gen.coroutine
    @abstractmethod
    def get_game_and_power(self, game_id, country_id, max_phases=None):
        """ Returns the game and the power we are playing
            :param game_id: The id of the game object (integer)
            :param country_id: The id of the country for which we want the game state (integer)
            :param max_phases: Optional. If set, improve speed by generating game only using the last 'x' phases.
            :return: A tuple consisting of
                    1) The diplomacy.Game object from the game state or None if an error occurred
                    2) The power name (e.g. 'FRANCE') referred to by country_id
        """
        raise NotImplementedError()

    @gen.coroutine
    @abstractmethod
    def set_orders(self, game, power_name, orders, wait=None):
        """ Submits orders back to the server
            :param game: A diplomacy.Game object representing the current state of the game
            :param power_name: The name of the power submitting the orders (e.g. 'FRANCE')
            :param orders: A list of strings representing the orders (e.g. ['A PAR H', 'F BRE - MAO'])
            :param wait: Optional. If True, sets ready=False, if False sets ready=True.
            :return: True for success, False for failure
            :type game: diplomacy.Game
        """
        raise NotImplementedError()
