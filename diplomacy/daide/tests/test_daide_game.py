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
""" Tests for complete DAIDE games """
from collections import namedtuple
import logging
import os

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

from diplomacy import Server
import diplomacy.daide as daide
from diplomacy.daide.tokens import Token
from diplomacy.server.server_game import ServerGame
from diplomacy.client.connection import connect
from diplomacy.utils import common, strings
from diplomacy.utils.subject_split import PhaseSplit
DaideCom = namedtuple("DaideCom", ["client_id", "request", "resp_notif"])

LOGGER = logging.getLogger(os.path.basename(__file__))
LOGGER.setLevel(logging.INFO)

HOSTNAME = 'localhost'
PORTS_POOL = [9500+i for i in range(0, 200, 2)]
FILE_FOLDER_NAME = os.path.abspath(os.path.dirname(__file__))

class ClientsComsSimulator():
    def __init__(self, port, csv_file):
        with open(csv_file, "r") as file:
            content = file.read()

        content = [line.split(',') for line in content.split('\n') if not line.startswith('#')]

        self._port = port
        self._coms = [DaideCom(int(line[0]), line[1], line[2:]) for line in content if line[0]]
        self._client_streams = {}

    @property
    def coms(self):
        return self._coms

    @gen.coroutine
    def run(self):
        while self._coms:
            request, stream = yield self._get_next_request_and_stream()

            if request:
                LOGGER.info("Sending request [%s]", str(request))
                message = daide.messages.DiplomacyMessage()
                message.content = daide.utils.str_to_bytes(request)
                yield stream.write(bytes(message))

            expected_resp_notif, stream = yield self._get_next_resp_notif_and_stream()

            while expected_resp_notif:
                resp_notif_message = yield daide.messages.DaideMessage.from_stream(stream)
                if resp_notif_message.message_type != daide.messages.MessageType.DIPLOMACY:
                    continue
                resp_notif = daide.utils.bytes_to_str(resp_notif_message.content)
                if Token(from_bytes=resp_notif_message.content[:2]) == daide.tokens.HLO:
                    resp_notif = resp_notif.split(' ')
                    resp_notif[5] = expected_resp_notif.split(' ')[5]
                    resp_notif = ' '.join(resp_notif)
                LOGGER.info("Received reply [%s] for request [%s]", str(resp_notif), str(request))
                assert resp_notif == expected_resp_notif
                expected_resp_notif, stream = yield self._get_next_resp_notif_and_stream()

    @gen.coroutine
    def _get_client_stream(self, client_id):
        stream = self._client_streams.get(client_id, None)
        if not stream:
            stream = yield TCPClient().connect('localhost', self._port)
            LOGGER.info("Connected to %d", self._port)
            # Set TCP_NODELAY / disable Nagle's Algorithm.
            stream.set_nodelay(True)
            message = daide.messages.InitialMessage()
            yield stream.write(bytes(message))
            self._client_streams[client_id] = stream
        return stream

    @gen.coroutine
    def _get_next_request_and_stream(self):
        """ Pop the next request from a DAIDE communications list
            :return: The next request along with the updated list of communications
                     or None and the updated list of communications
        """
        com = next(iter(self._coms), None)
        request = None
        stream = None
        while com:
            if com.request:
                request = com.request
                stream = yield self._get_client_stream(com.client_id)
                self._coms[0] = DaideCom(com.client_id, '', com.resp_notif)
                break
            elif com.resp_notif:
                break
            else:
                self._coms.pop(0)
                com = next(iter(self._coms), None)
        return request, stream

    @gen.coroutine
    def _get_next_resp_notif_and_stream(self):
        """ Pop the next response or notifcation from a DAIDE communications list
            :return: The next response or notifcation along with the updated list of communications
                     or None and the updated list of communications
        """
        com = next(iter(self._coms), None)
        resp_notif = None
        stream = None
        while com:
            if com.request:
                break
            elif com.resp_notif:
                resp_notif = com.resp_notif.pop(0)
                stream = yield self._get_client_stream(com.client_id)
                break
            else:
                self._coms.pop(0)
                com = next(iter(self._coms), None)
        return resp_notif, stream

@gen.coroutine
def daide_clients(port, csv_file):
    """ Simulate a client communicating with the server and validate server's responses and notifcations
        :param port: The port of the DAIDE server
        :param csv_file: the csv file containing the list of DAIDE communications
    """
    simulator = ClientsComsSimulator(port, csv_file)

    try:
        yield simulator.run()

    except StreamClosedError as err:
        LOGGER.error("Error connecting to %d: %s", port, err)

    assert not simulator.coms

def run_game_data(port, nb_daide_players, csv_file):
    """ Start a server and a client to test DAIDE communications
        :param port: The port of the DAIDE server
        :param csv_file: the csv file containing the list of DAIDE communications
    """
    @gen.coroutine
    def coroutine_func(server):
        """ Concrete call to main function. """
        server_port = server.backend.port
        daide_port = server_port + 1
        nb_regular_players = min(1, 7 - nb_daide_players)
        server_game = ServerGame(map_name='standard', n_controls=nb_daide_players + nb_regular_players,
                                 rules=['NO_PRESS', 'IGNORE_ERRORS', 'POWER_CHOICE'])
        server_game.server = server

        # Register game on server.
        server.add_new_game(server_game)

        server.start_new_daide_server(server_game.game_id, port=daide_port)

        user_game = None
        if nb_regular_players:
            username = 'user'
            password = 'password'
            connection = yield connect(HOSTNAME, server_port)
            user_channel = yield connection.authenticate(username, password,
                                                         create_user=not server.users.has_user(username, password))
            user_game = yield user_channel.join_game(game_id=server_game.game_id, power_name='AUSTRIA')

        daide_future = daide_clients(daide_port, csv_file)

        for _ in range(3 + nb_daide_players):
            if daide_future.done() or server_game.count_controlled_powers() == 2:
                break
            yield gen.sleep(2.5)
        else:
            raise RuntimeError()

        if user_game:
            phase = PhaseSplit(server_game.get_current_phase())

            while not daide_future.done() and server_game.status == strings.ACTIVE:
                yield user_game.wait()
                yield user_game.set_orders(orders=[])
                yield user_game.no_wait()

                while not daide_future.done() and phase.in_str == server_game.get_current_phase():
                    yield gen.sleep(2.5)

                if server_game.status != strings.ACTIVE:
                    break

                phase = PhaseSplit(server_game.get_current_phase())

        yield daide_future
        io_loop.stop()

    test_complete = False
    while not test_complete:
        try:
            io_loop = IOLoop()
            io_loop.make_current()
            common.Tornado.stop_loop_on_callback_error(io_loop)

            server = Server()
            io_loop.add_callback(coroutine_func, server)

            server.start(port=port, io_loop=io_loop)
        except IOError:
            port = PORTS_POOL.pop(0)
        finally:
            test_complete = server.backend.http_server is not None
            io_loop.stop()
            io_loop.clear_current()
            io_loop.close()
            server.stop_daide_server(None)
            if server.backend.http_server:
                server.backend.http_server.stop()
            server = None
            Server.__cache__.clear()

def test_game_reject_map():
    """ Test a game where the client rejects the map """
    run_game_data(PORTS_POOL.pop(0), 1, os.path.join(FILE_FOLDER_NAME, "game_data_1_reject_map.csv"))

def test_game_1():
    """ Test a complete 1 player game """
    run_game_data(PORTS_POOL.pop(0), 1, os.path.join(FILE_FOLDER_NAME, "game_data_1.csv"))

def test_game_history():
    """ Test a complete 1 player game and validate the full history (except last phase) """
    run_game_data(PORTS_POOL.pop(0), 1, os.path.join(FILE_FOLDER_NAME, "game_data_1_history.csv"))

def test_game_7():
    """ Test a complete 7 players game """
    run_game_data(PORTS_POOL.pop(0), 7, os.path.join(FILE_FOLDER_NAME, "game_data_7.csv"))
