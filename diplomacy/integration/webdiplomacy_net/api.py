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
""" Contains an API class to send requests to webdiplomacy.net """
import logging
import os
from socket import herror, gaierror, timeout
from urllib.parse import urlencode, urlparse, parse_qs
from tornado import gen
from tornado.httpclient import HTTPRequest
from tornado.simple_httpclient import HTTPTimeoutError, HTTPStreamClosedError
import ujson as json
from diplomacy.integration.base_api import BaseAPI
from diplomacy.integration.webdiplomacy_net.game import state_dict_to_game_and_power
from diplomacy.integration.webdiplomacy_net.orders import Order
from diplomacy.integration.webdiplomacy_net.utils import CACHE, GameIdCountryId

# Constants
LOGGER = logging.getLogger(__name__)
HTTP_ERRORS = (herror, gaierror, timeout, HTTPTimeoutError, HTTPStreamClosedError,
               ConnectionResetError, ConnectionRefusedError, OSError)
API_USER_AGENT = 'KestasBot / Philip Paquette v1.0'
API_WEBDIPLOMACY_NET = os.environ.get('API_WEBDIPLOMACY', 'https://webdiplomacy.net/api.php')

class API(BaseAPI):
    """ API to interact with webdiplomacy.net """

    @gen.coroutine
    def list_my_games(self, status=None, missing_orders=None, messages_after=None, press_type=None,
                      variant_id=None, anonymous=None, scoring=None, player_type=None):
        """ Lists my games that meet the provided criteria
            All arguments are optional.

            :param status: One of, or list of 'Playing', 'Defeated', 'Left', 'Won', 'Drawn', 'Survived', 'Resigned'
            :param missing_orders: Boolean. Indicates that we only want games where orders are missing.
            :param messages_after: Integer. Indicates we only want games where a msg was received after this timestamp
            :param press_type: One of, or list of "Regular", "PublicPressOnly", "NoPress", "RulebookPress"
            :param variant_id: One of, or list of variant ids
            :param anonymous: Boolean. Indicates that we only want games where players are anonymous
            :param scoring: One of, or list of 'WTA', 'PPSC', 'Unranked', 'SOS'
            :param player_type: One of, or list of 'Members', 'Mixed', 'MembersVsBots'
            :return: List of :class:`.GameIdCountryId` tuples  [(game_id, country_id), (game_id, country_id)]
        """
        # pylint: disable=too-many-arguments,too-many-return-statements
        params = {'route': 'players/my_games'}
        return_val = []

        # Building parameters
        if status is not None:
            status = [status] if not isinstance(status, list) else status
            valid_status = ('Playing', 'Defeated', 'Left', 'Won', 'Drawn', 'Survived', 'Resigned')
            for this_status in status:
                if this_status not in valid_status:
                    LOGGER.error('ERROR - The argument status "%s" is not recognized.', status)
                    return return_val
            params['status'] = ','.join(status)

        if missing_orders is not None:
            if not isinstance(missing_orders, bool):
                LOGGER.error('ERROR - The argument missing_orders must be a boolean.')
                return return_val
            params['missing_orders'] = 'Yes' if missing_orders else 'No'

        if messages_after is not None:
            if not isinstance(messages_after, int):
                LOGGER.error('ERROR - The argument messages_after must be a boolean.')
                return return_val
            params['messages_after'] = messages_after

        if press_type is not None:
            press_type = [press_type] if not isinstance(press_type, list) else press_type
            valid_press_type = ('Regular', 'PublicPressOnly', 'NoPress', 'RulebookPress')
            for this_press_type in press_type:
                if this_press_type not in valid_press_type:
                    LOGGER.error('ERROR - The argument press type "%s" is not recognized.', press_type)
                    return return_val
            params['press_type'] = ','.join(press_type)

        if variant_id is not None:
            variant_id = [variant_id] if not isinstance(variant_id, list) else variant_id
            for this_variant_id in variant_id:
                if not isinstance(this_variant_id, int):
                    LOGGER.error('ERROR - The argument variant_ids "%s" must be int or list of ints.', variant_id)
                    return return_val
            params['variant_id'] = ','.join([str(variant) for variant in variant_id])

        if anonymous is not None:
            if not isinstance(anonymous, bool):
                LOGGER.error('ERROR - The argument anonymous must be a boolean.')
                return return_val
            params['anonymous'] = 'Yes' if anonymous else 'No'

        if scoring is not None:
            scoring = [scoring] if not isinstance(scoring, list) else scoring
            valid_scoring = ('WTA', 'PPSC', 'Unranked', 'SOS')
            for this_scoring in scoring:
                if this_scoring not in valid_scoring:
                    LOGGER.error('ERROR - The argument scoring "%s" is not recognized.', scoring)
                    return return_val
            params['scoring'] = ','.join(scoring)

        if player_type is not None:
            player_type = [player_type] if not isinstance(player_type, list) else player_type
            valid_player_type = ('Members', 'Mixed', 'MembersVsBots')
            for this_player_type in player_type:
                if this_player_type not in valid_player_type:
                    LOGGER.error('ERROR - The argument player_type "%s" is not recognized.', player_type)
                    return return_val
            params['player_type'] = ','.join(player_type)

        # Sending request
        list_games_players = yield self._send_get_request(self._build_url(params))
        if list_games_players is None:
            return return_val

        # Returning
        for game_player in list_games_players:
            return_val += [GameIdCountryId(game_id=game_player['gameID'], country_id=game_player['countryID'])]
        return return_val

    @gen.coroutine
    def list_games_with_players_in_cd(self):
        """ Lists the game on the standard map where a player is in CD (civil disorder)
            and the bots needs to submit orders

            :return: List of :class:`.GameIdCountryId` tuples  [(game_id, country_id), (game_id, country_id)]
        """
        # Sending request
        list_games_players = yield self._send_get_request(self._build_url({'route': 'players/cd'}))
        if list_games_players is None:
            return []

        # Returning
        return_val = []
        for game_player in list_games_players:
            return_val += [GameIdCountryId(game_id=game_player['gameID'], country_id=game_player['countryID'])]
        return return_val

    @gen.coroutine
    def list_games_with_missing_orders(self):
        """ Lists of the game on the standard where the user has not submitted orders yet.

            :return: List of :class:`.GameIdCountryId` tuples  [(game_id, country_id), (game_id, country_id)]
        """
        # Sending request
        list_games_players = yield self._send_get_request(self._build_url({'route': 'players/missing_orders'}))
        if list_games_players is None:
            return []

        # Returning
        return_val = []
        for game_player in list_games_players:
            return_val += [GameIdCountryId(game_id=game_player['gameID'], country_id=game_player['countryID'])]
        return return_val

    @gen.coroutine
    def get_game_and_power(self, game_id, country_id, max_phases=None):
        """ Returns the game and the power we are playing

            :param game_id: The id of the game object (integer)
            :param country_id: The id of the country for which we want the game state (integer)
            :param max_phases: Optional. If set, improve speed by generating game only using the last 'x' phases.
            :type game_id: int
            :type country_id: int
            :type max_phases: int | None, optional
            :return: A tuple consisting of

                #. The diplomacy.Game object from the game state or None if an error occurred
                #. The power name (e.g. 'FRANCE') referred to by country_id
        """
        # pylint: disable=arguments-differ
        # Sending request
        state_dict = yield self._send_get_request(self._build_url({'route': 'game/status',
                                                                   'gameID': game_id,
                                                                   'countryID': country_id}))
        if state_dict is None:
            return None, None

        # Returning
        game, power_name = state_dict_to_game_and_power(state_dict, country_id, max_phases=max_phases)
        return game, power_name

    @gen.coroutine
    def send_message(self, game, sender, recipient, message):
        """ Sends a message to another power

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param sender: The name of the power sending the message.
            :param recipient: The name of the power receiving the message (or 'GLOBAL')
            :param message: The actual message content to send.
            :return: A boolean that indicates if the message was successfully sent or not
            :type game: diplomacy.Game
            :type sender: str
            :type recipient: str
            :type message: str
            :rtype: bool
        """
        # Logging message
        LOGGER.info('[%s/%s/%s] - Sending message to %s: %s',
                    game.game_id, game.get_current_phase(), sender, recipient, message)

        # Getting other info
        game_id = int(game.game_id)
        sender_id = CACHE[game.map_name]['power_to_ix'].get(sender, -1)
        recipient_id = CACHE[game.map_name]['power_to_ix'].get(recipient, -1)

        # Sending request
        url = self._build_url({'route': 'game/message'})
        body = {'gameID': game_id,
                'fromCountryID': sender_id,
                'toCountryID': recipient_id,
                'message': message}
        body = json.dumps(body).encode('utf-8')

        # Sending request
        response = yield self._send_post_request(url, body)
        if response is None:
            return False

        # Returning
        success, reason = response.get('success', 'No'), response.get('reason', '')
        if success == 'No':
            LOGGER.warning('WARNING during "%s". Unable to send message. Reason: %s', 'game/message', reason)
            return False
        return True

    @gen.coroutine
    def set_orders(self, game, power_name, orders, wait=None):
        """ Submits orders back to the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power submitting the orders (e.g. 'FRANCE')
            :param orders: A list of strings representing the orders (e.g. ['A PAR H', 'F BRE - MAO'])
            :param wait: Optional. If True, sets ready=False, if False sets ready=True.
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type orders: List[str]
            :type wait: bool | None, optional
            :rtype: bool
        """
        if game is None:
            return False

        # Logging orders
        LOGGER.info('[%s/%s/%s] - Submitting orders: %s', game.game_id, game.get_current_phase(), power_name, orders)

        # Converting orders to dict
        orders_obj = [Order(order, map_name=game.map_name, phase_type=game.phase_type, game=game) for order in orders]

        # Recording submitted orders
        submitted_orders = self._extract_norm_order_per_unit(orders_obj)            # {unit: normalized_order}

        # Getting other info
        game_id = int(game.game_id)
        country_id = CACHE[game.map_name]['power_to_ix'].get(power_name, -1)
        current_phase = game.get_current_phase()
        turn, phase = self._get_turn_phase(game, current_phase)

        # Building request
        url = self._build_url({'route': 'game/orders'})
        body = {'gameID': game_id,
                'turn': turn,
                'phase': phase,
                'countryID': country_id,
                'orders': [order.to_dict() for order in orders_obj if order]}
        if wait is not None:
            body['ready'] = 'Yes' if not wait else 'No'
        body = json.dumps(body).encode('utf-8')

        # Sending request
        response = yield self._send_post_request(url, body)
        if response is None:
            return False

        # No orders set - Was only setting the ready flag
        if not orders:
            return True

        # Validating
        orders_obj = [Order(order, map_name=game.map_name, phase_type=game.phase_type) for order in response]
        all_orders_set = True

        # Recording received orders
        received_orders = self._extract_norm_order_per_unit(orders_obj)             # {unit: normalized_order}

        # Logging different orders
        for unit in submitted_orders:
            if submitted_orders[unit] != received_orders.get(unit, ''):
                all_orders_set = False
                LOGGER.warning('[%s/%s/%s]. Submitted: "%s" - Server has: "%s".',
                               game.game_id, game.get_current_phase(), power_name,
                               submitted_orders[unit], received_orders.get(unit, ''))

        # Returning status
        return all_orders_set

    @gen.coroutine
    def set_vote(self, game, power_name, vote_type, vote_value):
        """ Submits a vote to the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power sending the vote (e.g. 'FRANCE')
            :param vote_type: One of 'Draw', 'Pause', 'Cancel', 'Concede'
            :param vote_value: A boolean that indicates to vote for, or to remove the vote
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type vote_type: str
            :type vote_value: bool
            :rtype: bool
        """
        if vote_type not in ('Draw', 'Pause', 'Cancel', 'Concede'):
            LOGGER.error('"%s" is not a valid vote type. Valid values are: Draw,Pause,Cancel,Concede', vote_type)
            return False

        # Logging vote
        current_phase = game.get_current_phase()
        LOGGER.info('[%s/%s/%s] - Voting %s: %s', game.game_id, current_phase, power_name, vote_type, vote_value)

        # Getting other info
        game_id = int(game.game_id)
        country_id = CACHE[game.map_name]['power_to_ix'].get(power_name, -1)

        # Building request
        url = self._build_url({'route': 'game/vote'})
        body = {'gameID': game_id,
                'countryID': country_id,
                'vote': vote_type,
                'value': 'Yes' if vote_value else 'No'}
        body = json.dumps(body).encode('utf-8')

        # Sending request
        response = yield self._send_post_request(url, body)
        if response is None:
            return False

        # Returning
        response_vote_type, response_vote_value = response.get('vote', ''), response.get('value', '')
        return bool(response_vote_type == vote_type and response_vote_value == ('Yes' if vote_value else 'No'))

    @gen.coroutine
    def set_draw_vote(self, game, power_name, vote_value):
        """ Submits a draw vote to the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power sending the vote (e.g. 'FRANCE')
            :param vote_value: A boolean that indicates to vote for, or to remove the vote
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type vote_value: bool
            :rtype: bool
        """
        return (yield self.set_vote(game, power_name, 'Draw', vote_value))

    @gen.coroutine
    def set_pause_vote(self, game, power_name, vote_value):
        """ Submits a pause vote to the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power sending the vote (e.g. 'FRANCE')
            :param vote_value: A boolean that indicates to vote for, or to remove the vote
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type vote_value: bool
            :rtype: bool
        """
        return (yield self.set_vote(game, power_name, 'Pause', vote_value))

    @gen.coroutine
    def set_cancel_vote(self, game, power_name, vote_value):
        """ Submits a cancel vote to the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power sending the vote (e.g. 'FRANCE')
            :param vote_value: A boolean that indicates to vote for, or to remove the vote
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type vote_value: bool
            :rtype: bool
        """
        return (yield self.set_vote(game, power_name, 'Cancel', vote_value))

    @gen.coroutine
    def set_concede_vote(self, game, power_name, vote_value):
        """ Submits a concede vote to the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power sending the vote (e.g. 'FRANCE')
            :param vote_value: A boolean that indicates to vote for, or to remove the vote
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type vote_value: bool
            :rtype: bool
        """
        return (yield self.set_vote(game, power_name, 'Concede', vote_value))

    @gen.coroutine
    def set_ready(self, game, power_name, ready):
        """ Sets the wait/ready flag on the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power setting the wait/ready flag (e.g. 'FRANCE')
            :param ready: Boolean that indicates we are ready to process if everyone is ready
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type ready: bool
            :rtype: bool
        """
        return (yield self.set_wait(game, power_name, wait=not ready))

    @gen.coroutine
    def set_wait(self, game, power_name, wait):
        """ Sets the wait/ready flag on the server

            :param game: A :class:`diplomacy.engine.game.Game` object representing the current state of the game
            :param power_name: The name of the power setting the wait/ready flag (e.g. 'FRANCE')
            :param wait: Boolean that indicates we want to wait before processing (i.e. True = not ready)
            :return: True for success, False for failure
            :type game: diplomacy.Game
            :type power_name: str
            :type wait: bool
            :rtype: bool
        """
        # Logging orders
        current_phase = game.get_current_phase()
        LOGGER.info('[%s/%s/%s] - Setting ready flag to: %s', game.game_id, current_phase, power_name, not wait)

        # Getting other info
        game_id = int(game.game_id)
        country_id = CACHE[game.map_name]['power_to_ix'].get(power_name, -1)
        turn, phase = self._get_turn_phase(game, current_phase)

        # Building request
        url = self._build_url({'route': 'game/ready'})
        body = {'gameID': game_id,
                'turn': turn,
                'phase': phase,
                'countryID': country_id,
                'ready': 'No' if wait else 'Yes'}
        body = json.dumps(body).encode('utf-8')

        # Sending request
        response = yield self._send_post_request(url, body)
        if response is None:
            return False

        # Returning
        ready_response = response.get('Ready', None)
        return bool(ready_response == ('No' if wait else 'Yes'))

    # ---- Helper methods ----
    @staticmethod
    def _build_url(params):
        """ Computes a URL with the params encoded

            :param params: A dictionary of parameters to encode (e.g. {'route': 'players/cd'})
            :return: A URL with the base API url and the parameters encoded
        """
        return '%s?%s' % (API_WEBDIPLOMACY_NET, urlencode(params))

    @staticmethod
    def _extract_norm_order_per_unit(orders_obj):
        """ Computes the normalized order for each unit
            This is used to make sure that the orders submitted are the same that the orders received

            :param orders_obj: A list of :class:.Order:() objects
            :return: A dictionary with units as keys and their corresponding normalized order as value
        """
        orders_per_unit = {}
        for order in orders_obj:
            unit = ' '.join(order.to_string().split()[:2])
            if order.to_string()[-2:] == ' D':
                unit = '? ' + unit[2:]
            orders_per_unit[unit] = order.to_norm_string()
        return orders_per_unit

    @staticmethod
    def _get_turn_phase(game, current_phase):
        """ Breaks the current_phase (e.g. 'S1901M') into the turn and phase used by webdiplomacy.net

            :param current_phase: The current phase (e.g. 'S1901M' or 'COMPLETED')
            :return: A tuple of turn, phase where turn is an integer, and phase is 'Diplomacy', 'Retreats', 'Builds'
        """
        if current_phase != 'COMPLETED':
            season, current_year, phase_type = current_phase[0], int(current_phase[1:5]), current_phase[5]
            nb_years = current_year - game.map.first_year
            turn = 2 * nb_years + (0 if season == 'S' else 1)
            phase = {'M': 'Diplomacy', 'R': 'Retreats', 'A': 'Builds'}[phase_type]
        else:
            turn = -1
            phase = 'Diplomacy'

        # Returning
        return turn, phase

    @gen.coroutine
    def _send_get_request(self, url):
        """ Helper method to send a get request to the API endpoint

            :param url: The URL where the send the GET request
            :return: The decoded JSON in the response.body, or None if an error occurred
            :rtype: dict | None
        """
        # To debug using PHPSTORM - Set header['Cookie'] = 'XDEBUG_SESSION=PHPSTORM;'
        route = parse_qs(urlparse(url).query).get('route', [url])[0]

        # Sending request
        try:
            http_request = HTTPRequest(url=url,
                                       method='GET',
                                       headers={'Authorization': 'Bearer %s' % self.api_key},
                                       connect_timeout=self.connect_timeout,
                                       request_timeout=self.request_timeout,
                                       user_agent=API_USER_AGENT)
            response = yield self.http_client.fetch(http_request, raise_error=False)
        except HTTP_ERRORS as err:
            LOGGER.error('Unable to connect to server. Error raised is: "%s"', repr(err))
            return None

        # Error Occurred
        if response.code != 200:
            LOGGER.warning('ERROR during "%s". Error code: %d. Body: %s.', route, response.code, response.body)
            return None

        # No response received from the server - Maybe a connection timeout?
        if not response.body:
            LOGGER.warning('WARNING during "%s". No response body received. Is the server OK?', route)
            return None

        # Otherwise, validating that received orders are the same as submitted orders
        try:
            response_dict = json.loads(response.body.decode('utf-8'))
        except (TypeError, ValueError):
            LOGGER.warning('ERROR during "%s". Unable to load JSON: %s.', route, response.body.decode('utf-8'))
            return None

        # Returning
        return response_dict

    @gen.coroutine
    def _send_post_request(self, url, body):
        """ Helper method to send a post request to the API endpoint

            :param url: The URL where the send the POST request
            :param body: The body of the POST request
            :return: The decoded JSON in the response.body, or None if an error occurred
            :rtype: dict | None
        """
        # To debug using PHPSTORM - Set header['Cookie'] = 'XDEBUG_SESSION=PHPSTORM;'
        route = parse_qs(urlparse(url).query).get('route', [url])[0]

        # Sending request
        try:
            http_request = HTTPRequest(url=url,
                                       method='POST',
                                       body=body,
                                       headers={'Authorization': 'Bearer %s' % self.api_key},
                                       connect_timeout=self.connect_timeout,
                                       request_timeout=self.request_timeout,
                                       user_agent=API_USER_AGENT)
            response = yield self.http_client.fetch(http_request, raise_error=False)
        except HTTP_ERRORS as err:
            LOGGER.error('Unable to connect to server. Error raised is: "%s"', repr(err))
            return None

        # Error Occurred
        if response.code != 200:
            LOGGER.warning('ERROR during "%s". Error code: %d. Body: %s.', route, response.code, response.body)
            return None

        # No response received from the server - Maybe a connection timeout?
        if not response.body:
            LOGGER.warning('WARNING during "%s". No response body received. Is the server OK?', route)
            return None

        # Otherwise, validating that received orders are the same as submitted orders
        try:
            response_dict = json.loads(response.body.decode('utf-8'))
        except (TypeError, ValueError):
            LOGGER.warning('ERROR during "%s". Unable to load JSON: %s.', route, response.body.decode('utf-8'))
            return None

        # Returning
        return response_dict
