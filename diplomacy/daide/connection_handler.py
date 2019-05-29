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
""" Tornado connection handler class, used internally to manage data received by server application. """
import logging
import uuid

from tornado import gen
from tornado.concurrent import Future
from tornado.iostream import StreamClosedError
import diplomacy.daide as daide
from diplomacy.daide.messages import DaideMessage, MessageType
import diplomacy.daide.notifications
from diplomacy.daide.notification_managers import translate_notification
from diplomacy.daide.requests import RequestBuilder
import diplomacy.daide.request_managers
import diplomacy.daide.responses
from diplomacy.daide.utils import bytes_to_str
from diplomacy.utils import exceptions

LOGGER = logging.getLogger(__name__)

class ConnectionHandler():
    """ ConnectionHandler class. Properties:
        - server: server object representing running server.
    """
    _NAME_VARIANT_PREFIX = "DAIDE"
    _NAME_VARIANTS_POOL = []
    _USED_NAME_VARIANTS = []

    def __init__(self):
        self.stream = None
        self.server = None
        self.game_id = None
        self.token = None
        self._name_variant = None
        self._socket_no = None
        self._local_addr = ('::1', 0, 0, 0)
        self._remote_addr = ('::1', 0, 0, 0)

        self.message_mapping = {
            MessageType.INITIAL: self._on_initial_message,
            MessageType.DIPLOMACY: self._on_diplomacy_message,
            MessageType.FINAL: self._on_final_message,
            MessageType.ERROR: self._on_error_message
        }

    def initialize(self, stream, server, game_id):
        """ Initialize the connection handler.
            :param server: a Server object.
            :type server: diplomacy.Server
        """
        self.stream = stream
        self.server = server
        self.game_id = game_id
        stream.set_close_callback(self.on_connection_close)
        self._socket_no = self.stream.socket.fileno()
        self._local_addr = stream.socket.getsockname()
        self._remote_addr = stream.socket.getpeername()

    @property
    def local_addr(self):
        return self._local_addr

    @property
    def remote_addr(self):
        return self._remote_addr

    def get_name_variant(self):
        if self._name_variant is None:
            self._name_variant = self._NAME_VARIANTS_POOL.pop(0) if self._NAME_VARIANTS_POOL \
                                 else len(self._USED_NAME_VARIANTS)
            self._USED_NAME_VARIANTS.append(self._name_variant)
        return self._NAME_VARIANT_PREFIX + str(self._name_variant)

    def release_name_variant(self):
        self._USED_NAME_VARIANTS.remove(self._name_variant)
        self._NAME_VARIANTS_POOL.append(self._name_variant)
        self._name_variant = None

    @gen.coroutine
    def close_connection(self):
        try:
            message = daide.messages.DiplomacyMessage()
            message.content = bytes(daide.responses.TurnOffResponse())
            yield self.write_message(message)
            self.stream.close()
        except StreamClosedError:
            LOGGER.error('Stream is closed.')

    def on_connection_close(self):
        """ Invoked when the socket is closed (see parent method).
            Detach this connection handler from server users.
        """
        self.release_name_variant()
        self.server.users.remove_connection(self, remove_tokens=False)
        LOGGER.info("Removed connection. Remaining %d connection(s).", self.server.users.count_connections())

    @gen.coroutine
    def read_stream(self):
        messages = []
        in_message = None

        # TODO: add validation checks
        in_message = yield DaideMessage.from_stream(self.stream)

        if in_message and in_message.is_valid:
            message_handler = self.message_mapping.get(in_message.message_type, None)
            # TODO: raise if None

            if gen.is_coroutine_function(message_handler):
                messages = yield message_handler(in_message)
            else:
                messages = message_handler(in_message)
        elif in_message:
            err_message = daide.messages.ErrorMessage()
            err_message.error_code = in_message.error_code
            messages = [err_messages]

        for message in messages:
            yield self.write_message(message)

    # Added for compatibility with WebSocketHandler interface
    def write_message(self, message, binary=True):
        future = None

        if isinstance(message, daide.notifications.DaideNotification):
            LOGGER.info('[{}] notification:[{}]'.format(self._socket_no, bytes_to_str(bytes(message))))
            notification = message
            message = daide.messages.DiplomacyMessage()
            message.content = bytes(notification)

        if isinstance(message, DaideMessage):
            future = self.stream.write(bytes(message))
        else:
            future = Future()
            future.set_result(None)

        return future

    def translate_notification(self, notification):
        """ Translate a notification to a DAIDE notification.
            :param notification: a notification object to pass to handler function.
                See diplomacy.communication.notifications for possible notifications.
            :return: either None or an array of daide notifications.
                See module diplomacy.daide.notifications for possible daide notifications.
        """
        return translate_notification(self.server, notification, self)

    def _on_initial_message(self, in_message):
        LOGGER.info('[{}] initial message'.format(self._socket_no))
        return [daide.messages.RepresentationMessage()]

    @gen.coroutine
    def _on_diplomacy_message(self, in_message):
        messages = []
        responses = []
        request = RequestBuilder.from_bytes(in_message.content)

        try:
            LOGGER.info('[{}] request:[{}]'.format(self._socket_no, bytes_to_str(in_message.content)))
            request.game_id = self.game_id
            responses = yield daide.request_managers.handle_request(self.server, request, self)
        except exceptions.ResponseException as exc:
            responses = [daide.responses.REJ(bytes(request))]

        if responses:
            # TODO: add try except
            for response in responses:
                response_bytes = bytes(response)
                LOGGER.info('[{}] response:[{}]'.format(self._socket_no, bytes_to_str(response_bytes)))
                message = daide.messages.DiplomacyMessage()
                message.content = response_bytes
                messages.append(message)

        return messages

    def _on_final_message(self, in_message):
        LOGGER.info('[{}] final message'.format(self._socket_no))
        self.stream.close()
        return []

    def _on_error_message(self, in_message):
        LOGGER.error('[{}] error [{d}]'.format(self._socket_no, in_message.error_code))
        return []
