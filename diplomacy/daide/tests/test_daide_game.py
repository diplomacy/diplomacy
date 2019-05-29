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
from collections import namedtuple
import logging
import os
import sys

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

from diplomacy import Server
import diplomacy.daide as daide
import diplomacy.daide.messages
import diplomacy.daide.responses
from diplomacy.daide.tokens import Token
import diplomacy.daide.utils
from diplomacy.server.server_game import ServerGame
from diplomacy.client.connection import connect
from diplomacy.utils import common, strings
from diplomacy.utils.subject_split import PhaseSplit

DAIDECom = namedtuple("DAIDECom", ["request", "resp_notif"])

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)

@gen.coroutine
def _read_data(stream):
    # Read 4 bytes.
    header = yield stream.read_bytes(4)

    # Convert from network order to int.
    length = _UNPACK_INT(header)[0]

    data = yield stream.read_bytes(length)
    return data.decode()

def get_next_request(daide_coms):
    daide_com = next(iter(daide_coms), None)
    request = None
    while daide_com:
        if daide_com.request:
            request = daide_com.request
            daide_coms[0] = DAIDECom('', daide_com.resp_notif)
            break
        elif daide_com.resp_notif:
            break
        else:
            daide_coms.pop(0)
            daide_com = next(iter(daide_coms), None)
    return request, daide_coms

def get_next_resp_notif(daide_coms):
    daide_com = next(iter(daide_coms), None)
    resp_notif = None
    while daide_com:
        if daide_com.request:
            break
        elif daide_com.resp_notif:
            resp_notif = daide_com.resp_notif.pop(0)
            break
        else:
            daide_coms.pop(0)
            daide_com = next(iter(daide_coms), None)
    return resp_notif, daide_coms

@gen.coroutine
def daide_client(port, data_file):
    daide_coms = ()
    
    try:
        with open(data_file, "r") as file:
            content = file.read()

        content = [line.split(',') for line in content.split('\n') if not line.startswith('#')]
        daide_coms = [DAIDECom(line[0], line[1:]) for line in content]

        stream = yield TCPClient().connect('localhost', port)
        logging.info("Connected to %d", port)

        # Set TCP_NODELAY / disable Nagle's Algorithm.
        stream.set_nodelay(True)

        message = daide.messages.InitialMessage()
        yield stream.write(bytes(message))

        while True:
            request, daide_coms = get_next_request(daide_coms)

            if not request:
                break

            logging.info("Sending request [{}]".format(request))
            message = daide.messages.DiplomacyMessage()
            message.content = daide.utils.str_to_bytes(request)
            yield stream.write(bytes(message))

            expected_resp_notif, daide_coms = get_next_resp_notif(daide_coms)

            while expected_resp_notif:
                resp_notif_message = yield daide.messages.DaideMessage.from_stream(stream)
                if resp_notif_message.message_type != daide.messages.MessageType.DIPLOMACY:
                    continue
                resp_notif = daide.utils.bytes_to_str(resp_notif_message.content)
                if Token(from_bytes=resp_notif_message.content[:2]) == daide.tokens.HLO:
                    resp_notif = resp_notif.split(' ')
                    resp_notif[5] = expected_resp_notif.split(' ')[5]
                    resp_notif = ' '.join(resp_notif)
                logging.info("Received reply [{}] for request [{}]".format(resp_notif, request))
                assert resp_notif == expected_resp_notif
                expected_resp_notif, daide_coms = get_next_resp_notif(daide_coms)

    except StreamClosedError as exc:
        logger.error("Error connecting to %d: %s", port, exc)

    assert len(daide_coms) == 0

def run_game_data(data_file):
    hostname = 'localhost'
    port = 9456
    daide_port = 9500

    io_loop = IOLoop()
    io_loop.make_current()
    common.Tornado.stop_loop_on_callback_error(io_loop)

    server = Server()

    @gen.coroutine
    def coroutine_func():
        """ Concrete call to main function. """
        server_game = ServerGame(map_name='standard', n_controls=2, rules=['NO_PRESS', 'IGNORE_ERRORS', 'POWER_CHOICE'])
        server_game.server = server

        # Register game on server.
        server.add_new_game(server_game)

        server.start_new_daide_server(server_game.game_id, port=daide_port)

        username = 'user'
        password = 'password'
        connection = yield connect(hostname, port)
        user_channel = yield connection.authenticate(username, password,
                                                     create_user=not server.users.has_user(username, password))
        user_game = yield user_channel.join_game(game_id=server_game.game_id, power_name='AUSTRIA')

        daide_future = daide_client(daide_port, data_file)

        for attempt_idx in range(4):
            if server_game.count_controlled_powers() == 2:
                break
            yield gen.sleep(2.5)
        else:
            raise RuntimeError()

        try:
            phase = PhaseSplit.split(server_game.get_current_phase())

            while not daide_future.done() and server_game.status == strings.ACTIVE:
                yield user_game.wait()
                yield user_game.set_orders(orders=[])
                yield user_game.no_wait()

                while not daide_future.done() and phase.in_str == server_game.get_current_phase():
                    yield gen.sleep(2.5)

                if server_game.status != strings.ACTIVE:
                    break

                phase = PhaseSplit.split(server_game.get_current_phase())
        except Exception as exception:
            logging.error('Exception: {}'.format(exception))

        server.stop_daide_server(server_game.game_id)

        yield daide_future

        io_loop.stop()

    io_loop.add_callback(coroutine_func)
    server.start(port=port, io_loop=io_loop)

def test_request_manager_no_notification():
    run_game_data("game_data_no_notification.csv")
