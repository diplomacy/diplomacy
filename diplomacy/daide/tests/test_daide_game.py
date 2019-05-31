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
import random
import socket

from tornado import gen
from tornado.concurrent import Future
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

DaideCom = namedtuple("DaideCom", ["client_id", "request", "resp_notifs"])
ClientRequest = namedtuple("ClientRequest", ["client", "request"])

LOGGER = logging.getLogger(os.path.basename(__file__))
LOGGER.setLevel(logging.INFO)

HOSTNAME = 'localhost'
FILE_FOLDER_NAME = os.path.abspath(os.path.dirname(__file__))

def is_port_opened(port, hostname=HOSTNAME):
    """ Checks if the specified port is opened
        :param port: The port to check
        :param hostname: The hostname to check, defaults to '127.0.0.1'
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((hostname, port))
    if result == 0:
        return True
    return False

class ClientComsSimulator():
    """ Represents a client's coms """
    def __init__(self, client_id):
        """ Constructor
            :param client_id: the id
        """
        self._id = client_id
        self._stream = None
        self._resp_notif_future = None
        self._is_game_joined = False

    @property
    def stream(self):
        """ Returns the stream """
        return self._stream

    @property
    def is_game_joined(self):
        """ Returns if the client has joinded the game """
        return self._is_game_joined

    def group_resp_notifs_coms(self, coms):
        """ Gruops the client's response / notifications communications into the same entry
            :param coms: the communications
            :return: the communications with the client's response / notifications grouped
        """
        resp_notif_idx = 0
        while resp_notif_idx < len(coms):
            resp_notifs_com = coms[resp_notif_idx]

            if resp_notifs_com.client_id != self._id or resp_notifs_com.request:
                resp_notif_idx += 1
                continue

            next_resp_notif_idx = resp_notif_idx + 1
            while next_resp_notif_idx < len(coms):
                com = coms[next_resp_notif_idx]

                if com.client_id != self._id:
                    next_resp_notif_idx += 1
                    continue

                if com.request:
                    break

                resp_notifs_com.resp_notifs.extend(com.resp_notifs)
                coms.pop(next_resp_notif_idx)

            resp_notif_idx += 1

        return coms

    def pop_next_request(self, coms):
        """ Pop the next request from a DAIDE communications list
            :return: The next request along with the updated list of communications
                     or None and the updated list of communications
        """
        com = next(iter(coms), None)
        request = None

        while com and com.client_id == self._id:
            if com.request:
                request = com.request
                coms[0] = DaideCom(com.client_id, '', com.resp_notifs)
                LOGGER.info("[%d:%d] preparing to send request [%s]", self._id, self.stream.socket.fileno()+1, request)
                break
            elif com.resp_notifs:
                break
            else:
                coms.pop(0)
                com = next(iter(coms), None)

        return request, coms

    def pop_next_resp_notif(self, coms):
        """ Pop the next response or notifcation from a DAIDE communications list
            :return: The next response or notifcation along with the updated list of communications
                     or None and the updated list of communications
        """
        com = next(iter(coms), None)
        resp_notif = None

        while com and com.client_id == self._id:
            if com.request:
                break
            elif com.resp_notifs:
                resp_notif = com.resp_notifs.pop(0)
                LOGGER.info("[%d:%d] waiting for resp_notif [%s]", self._id, self.stream.socket.fileno()+1, resp_notif)
                break
            else:
                coms.pop(0)
                com = next(iter(coms), None)

        return resp_notif, coms

    @gen.coroutine
    def connect(self, game_port):
        """ Connect to the DAIDE server
            :param game_port: the DAIDE game's port
        """
        self._stream = yield TCPClient().connect('localhost', game_port)
        # LOGGER.info("Connected to %d", port)
        message = daide.messages.InitialMessage()
        yield self._stream.write(bytes(message))
        yield daide.messages.DaideMessage.from_stream(self._stream)

    @gen.coroutine
    def send_request(self, request):
        """ Sends a request
            :param request: the request to send
        """
        if self._resp_notif_future is not None:
            yield self._resp_notif_future
            self._resp_notif_future = None
        message = daide.messages.DiplomacyMessage()
        message.content = daide.utils.str_to_bytes(request)
        # Give a little breathing room between each read and writes
        yield gen.sleep(0.25)
        yield self._stream.write(bytes(message))

    @gen.coroutine
    def validate_resp_notif(self, expected_resp_notifs):
        """ Validate that expected response / notifications are received regardless of the order
            :param expected_resp_notifs: the response / notifications to receive
        """
        while expected_resp_notifs:
            # Give a little breathing room between each read and writes
            yield gen.sleep(0)
            resp_notif_message = yield daide.messages.DaideMessage.from_stream(self._stream)

            resp_notif = daide.utils.bytes_to_str(resp_notif_message.content)
            if Token(from_bytes=resp_notif_message.content[:2]) == daide.tokens.HLO:
                resp_notif = resp_notif.split(' ')
                resp_notif[5] = expected_resp_notifs[0].split(' ')[5]
                resp_notif = ' '.join(resp_notif)
                self._is_game_joined = True

            LOGGER.info("[%d:%d] Received reply [%s]", self._id, self.stream.socket.fileno()+1, str(resp_notif))
            assert resp_notif in expected_resp_notifs
            expected_resp_notifs.remove(resp_notif)

    @gen.coroutine
    def execute_iteration(self, coms):
        """ Execute a single communication iteration
            :param coms:
            :return:
        """
        request, coms = self.pop_next_request(coms)

        if request is not None:
            yield self.send_request(request)

        expected_resp_notifs = []
        expected_resp_notif, coms = self.pop_next_resp_notif(coms)

        while expected_resp_notif is not None:
            expected_resp_notifs.append(expected_resp_notif)
            expected_resp_notif, coms = self.pop_next_resp_notif(coms)

        self._resp_notif_future = self.validate_resp_notif(expected_resp_notifs)

        return coms

class ClientsComsSimulator():
    """ Represents multi clients's coms """
    def __init__(self, game_port, nb_clients, csv_file):
        """ Constructor
            :param game_port: the port of the game
            :param nb_clients: the number of clients
            :param csv_file: the csv containing the communications in chronological order
        """
        with open(csv_file, "r") as file:
            content = file.read()

        content = [line.split(',') for line in content.split('\n') if not line.startswith('#')]

        self._game_port = game_port
        self._nb_clients = nb_clients
        self._coms = [DaideCom(int(line[0]), line[1], line[2:]) for line in content if line[0]]
        self._clients = {}
        self._streams_resp_notif_futures = {}

    @gen.coroutine
    def execute(self, future):
        """ Executes the communications between clients
           :param future: the future to update when the execution is completed
        """
        try:
            while self._coms:
                try:
                    next_com = next(iter(self._coms))
                except StopIteration:
                    break

                if next_com.client_id not in self._clients and len(self._clients) < self._nb_clients:
                    client = ClientComsSimulator(next_com.client_id)
                    yield client.connect(self._game_port)
                    self._coms = client.group_resp_notifs_coms(self._coms)
                    self._clients[next_com.client_id] = client

                for client in self._clients.values():
                    self._coms = yield client.execute_iteration(self._coms)

        except StreamClosedError as err:
            LOGGER.error("Stream closed: %s", err)

        assert not self._coms

        future.set_result(None)

def run_game_data(nb_daide_clients, rules, csv_file):
    """ Start a server and a client to test DAIDE communications
        :param port: The port of the DAIDE server
        :param csv_file: the csv file containing the list of DAIDE communications
    """
    server = Server()
    io_loop = IOLoop()
    io_loop.make_current()
    common.Tornado.stop_loop_on_callback_error(io_loop)

    @gen.coroutine
    def coroutine_func():
        """ Concrete call to main function. """
        port = random.randint(9000, 9999)

        while is_port_opened(port):
            port = random.randint(9000, 9999)

        server.start(port=port)

        daide_port = port - 1000
        nb_regular_players = min(1, 7 - nb_daide_clients)
        server_game = ServerGame(map_name='standard', n_controls=nb_daide_clients + nb_regular_players, rules=rules)
        server_game.server = server

        # Register game on server.
        server.add_new_game(server_game)

        server.start_new_daide_server(server_game.game_id, port=daide_port)

        user_game = None
        if nb_regular_players:
            username = 'user'
            password = 'password'
            connection = yield connect(HOSTNAME, port)
            user_channel = yield connection.authenticate(username, password,
                                                         create_user=not server.users.has_user(username, password))
            user_game = yield user_channel.join_game(game_id=server_game.game_id, power_name='AUSTRIA')

        coms_simulator = ClientsComsSimulator(daide_port, nb_daide_clients, csv_file)
        daide_future = Future()
        coms_simulator.execute(daide_future)

        for _ in range(3 + nb_daide_clients):
            if daide_future.done() or server_game.count_controlled_powers() == nb_daide_clients + nb_regular_players:
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

    try:
        io_loop.run_sync(coroutine_func)

    finally:
        server.stop_daide_server(None)
        if server.backend.http_server:
            server.backend.http_server.stop()

        io_loop.stop()
        io_loop.clear_current()
        io_loop.close()

        server = None
        Server.__cache__.clear()

def test_game_reject_map():
    """ Test a game where the client rejects the map """
    run_game_data(1, ['NO_PRESS', 'IGNORE_ERRORS', 'POWER_CHOICE'],
                  os.path.join(FILE_FOLDER_NAME, "game_data_1_reject_map.csv"))

def test_game_1():
    """ Test a complete 1 player game """
    run_game_data(1, ['NO_PRESS', 'IGNORE_ERRORS', 'POWER_CHOICE'],
                  os.path.join(FILE_FOLDER_NAME, "game_data_1.csv"))

def test_game_history():
    """ Test a complete 1 player game and validate the full history (except last phase) """
    run_game_data(1, ['NO_PRESS', 'IGNORE_ERRORS', 'POWER_CHOICE'],
                  os.path.join(FILE_FOLDER_NAME, "game_data_1_history.csv"))

def test_game_7():
    """ Test a complete 7 players game """
    run_game_data(7, ['NO_PRESS', 'IGNORE_ERRORS', 'POWER_CHOICE'],
                  os.path.join(FILE_FOLDER_NAME, "game_data_7.csv"))

def test_game_7_press():
    """ Test a complete 7 players game with press """
    run_game_data(7, ['IGNORE_ERRORS', 'POWER_CHOICE'],
                  os.path.join(FILE_FOLDER_NAME, "game_data_7_press.csv"))
