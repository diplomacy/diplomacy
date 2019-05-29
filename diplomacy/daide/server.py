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
import logging
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from diplomacy.daide.connection_handler import ConnectionHandler

LOGGER = logging.getLogger(__name__)

class Server(TCPServer):
    def __init__(self, master_server, game_id):
        super(Server, self).__init__()
        self._master_server = master_server
        self._game_id = game_id
        self._registered_connections = {}

    @property
    def master_server(self):
        return self._master_server

    @property
    def game_id(self):
        return self._game_id

    def stop(self):
        for _, connection_handler in self._registered_connections.items():
            connection_handler.close_connection()
        super(Server, self).stop()

    @gen.coroutine
    def handle_stream(self, stream, address):
        LOGGER.info("Connection from client [{}]".format(address))

        handler = ConnectionHandler()
        handler.initialize(stream, self._master_server, self._game_id)
        self._registered_connections[stream] = handler

        try:
            while not handler.stream.closed():
                yield handler.read_stream()

        except StreamClosedError:
            LOGGER.error("[{}] disconnected".format(address))

        del self._registered_connections[stream]
