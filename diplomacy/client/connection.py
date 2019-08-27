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
""" Connection object, handling an internal websocket tornado connection. """
import logging
import weakref
from typing import Dict
from datetime import timedelta

from tornado import gen, ioloop
from tornado.concurrent import Future
from tornado.iostream import StreamClosedError
from tornado.locks import Event
from tornado.websocket import websocket_connect, WebSocketClosedError

import ujson as json

from diplomacy.client import notification_managers
from diplomacy.client.client_utils.reconnection import Reconnection
from diplomacy.client.response_managers import handle_response
from diplomacy.client.client_utils.request_future_context import RequestFutureContext
from diplomacy.communication import notifications, requests, responses
from diplomacy.utils import exceptions, strings, constants

LOGGER = logging.getLogger(__name__)

class Connection:
    """ Connection class. Properties:
        - hostname: hostname to connect (e.g. 'localhost')
        - port: port to connect (e.g. 8888)
        - use_ssl: boolean telling if connection should be securized (True) or not (False).
        - url (auto): websocket url to connect (generated with hostname and port)
        - connection: a tornado websocket connection object
        - connection_count: number of successful connections from this Connection object.
            Used to check if message callbacks is already launched (if count > 0).
        - connection_lock: a tornado lock used to access tornado websocket connection object
        - is_connecting: a tornado Event used to keep connection status.
            No request can be sent while is_connecting.
            If connected, Synchronize requests can be sent immediately even if is_reconnecting.
            Other requests must wait full reconnection.
        - is_reconnecting: a tornado Event used to keep re-connection status.
            Non-synchronize request cannot be sent while is_reconnecting.
            If reconnected, all requests can be sent.
        - channels: a WeakValueDictionary mapping channel token to Channel object.
        - requests_waiting_responses: a dictionary mapping a request ID to the context of a
            request **sent**. Contains requests that are waiting for a server response.
        - unknown_tokens: a set of unknown tokens. We can safely ignore them, as the server has been notified.
    """
    __slots__ = ['hostname', 'port', 'use_ssl', 'connection', 'is_connecting', 'is_reconnecting',
                 'connection_count', 'channels', 'requests_waiting_responses', 'unknown_tokens']

    def __init__(self, hostname, port, use_ssl=False):
        self.hostname = hostname
        self.port = port
        self.use_ssl = bool(use_ssl)

        self.connection = None
        self.is_connecting = Event()
        self.is_reconnecting = Event()

        self.connection_count = 0

        self.channels = weakref.WeakValueDictionary()  # {token => Channel}

        self.requests_waiting_responses = {}  # type: Dict[str, RequestFutureContext]
        self.unknown_tokens = set()

        # When connection is created, we are not yet connected, but reconnection does not matter
        # (we consider we are reconnected).
        self.is_reconnecting.set()

    url = property(lambda self: '%s://%s:%d' % ('wss' if self.use_ssl else 'ws', self.hostname, self.port))

    @gen.coroutine
    def _connect(self):
        """ Create (force) a tornado websocket connection. Try NB_CONNECTION_ATTEMPTS attempts,
            waiting for ATTEMPT_DELAY_SECONDS seconds between 2 attempts.
            Raise an exception if it cannot connect.
        """

        # We are connecting.
        self.is_connecting.clear()

        # Create a connection (currently using websockets).
        self.connection = None
        for attempt_index in range(constants.NB_CONNECTION_ATTEMPTS):
            try:
                future_connection = websocket_connect(self.url)
                self.connection = yield gen.with_timeout(
                    timedelta(seconds=constants.ATTEMPT_DELAY_SECONDS), future_connection)
                break
            except (gen.TimeoutError, ConnectionAbortedError, ConnectionError,
                    ConnectionRefusedError, ConnectionResetError) as ex:
                if attempt_index + 1 == constants.NB_CONNECTION_ATTEMPTS:
                    raise ex
                LOGGER.warning('Connection failing (attempt %d), retrying.', attempt_index + 1)
                yield gen.sleep(constants.ATTEMPT_DELAY_SECONDS)

        if not self.connection_count:
            # Start receiving messages as soon as we are connected.
            ioloop.IOLoop.current().add_callback(self._handle_socket_messages)

        # We are connected.
        self.connection_count += 1
        self.is_connecting.set()

        LOGGER.info('Connection succeeds.')

    @gen.coroutine
    def _reconnect(self):
        """ Reconnect. """
        LOGGER.info('Trying to reconnect.')
        # We are reconnecting.
        self.is_reconnecting.clear()
        yield self._connect()
        # We will be reconnected when method Reconnection.sync_done() will finish.
        Reconnection(self).reconnect()

    def write_request(self, request_context):
        """ Write a request into internal connection object.
            :param request_context: context of request to send.
            :type request_context: RequestFutureContext
        """
        if request_context.write_future:
            return request_context.write_future
        future = request_context.write_future = Future()
        future.add_done_callback(self.generate_written_callback(request_context))
        request = request_context.request
        self.requests_waiting_responses[request_context.request_id] = request_context

        def on_message_written(write_future):
            """ 3) Writing returned, set future as done (with writing result)
            or with writing exception. """
            exception = write_future.exception()
            if exception is not None:
                future.set_exception(exception)
            else:
                future.set_result(write_future.result())

        def on_connected(reconnected_future):
            """ 2) Send request. """
            exception = reconnected_future.exception()
            if exception is not None:
                LOGGER.error('Fatal (re)connection error occurred while sending a request.')
                future.set_exception(exception)
            else:
                try:
                    if self.connection is None:
                        raise WebSocketClosedError()
                    write_future = self.connection.write_message(request.json())
                except (WebSocketClosedError, StreamClosedError) as exc:
                    future.set_exception(exc)
                else:
                    write_future.add_done_callback(on_message_written)

        # 1)    Synchronize requests just wait for connection.
        #       Other requests wait for reconnection (which also implies connection).
        if isinstance(request, requests.Synchronize):
            self.is_connecting.wait().add_done_callback(on_connected)
        else:
            self.is_reconnecting.wait().add_done_callback(on_connected)

        return future

    @gen.coroutine
    def connect(self):
        """ Effectively connect this object. """
        LOGGER.info('Trying to connect.')
        yield self._connect()

    def _on_socket_message(self, socket_message):
        """ Manage given socket_message (string),
            that may be a string representation of either a request or a notification.
        """

        # Check response format and run callback (if defined).
        try:
            json_message = json.loads(socket_message)
        except ValueError:
            LOGGER.exception('Unable to parse JSON from a socket message.')
            return

        if not isinstance(json_message, dict):
            LOGGER.error("Unable to convert a JSON string to a dictionary.")
            return
        request_id = json_message.get(strings.REQUEST_ID, None)
        notification_id = json_message.get(strings.NOTIFICATION_ID, None)

        if request_id:
            if request_id not in self.requests_waiting_responses:
                LOGGER.error('Unknown request %s.', request_id)
                LOGGER.error(', '.join(self.requests_waiting_responses))
                exit(-1)
                return
            request_context = self.requests_waiting_responses.pop(request_id)  # type: RequestFutureContext
            try:
                response = responses.parse_dict(json_message)
                managed_data = handle_response(request_context, response)
                request_context.future.set_result(managed_data)
            except exceptions.ResponseException as ex:
                LOGGER.error('Error received for request %s: %s', request_context.request.name, ex)
                LOGGER.debug('Full request was: %s', request_context.request.to_dict())
                request_context.future.set_exception(ex)

        elif notification_id:
            notification = notifications.parse_dict(json_message)
            if notification.token not in self.channels:
                if notification.token not in self.unknown_tokens:
                    LOGGER.error('Unknown notification: %s', notification.name)
                    self._handle_unknown_token(notification.token)
                return
            notification_managers.handle_notification(self, notification)
        else:
            LOGGER.error('Unknown socket message.')

    @gen.coroutine
    def _handle_socket_messages(self):
        """ Main looping method used to received connection messages. """
        while True:
            msg = yield self.connection.read_message()
            if msg is None:
                # Reconnect.
                LOGGER.error('Disconnected.')
                yield self._reconnect()
            else:
                # Check response format and run callback (if defined).
                self._on_socket_message(msg)

    def _handle_unknown_token(self, token):
        """ Notify server about an unknown channel token.
            This is likely because the channel has gone out of scope.
            :param token: token to notify server with.
        """
        # Send notification request without waiting any server response. Ignore errors if any.
        try:
            self.unknown_tokens.add(token)
            self.connection.write_message(requests.UnknownToken(token=token).json())
        except (WebSocketClosedError, StreamClosedError):
            pass

    # Public methods.
    @gen.coroutine
    def get_daide_port(self, game_id):
        """ Send a GetDaidePort request.
            :param game_id: game id
            :return: int. the game DAIDE port
        """
        request = requests.GetDaidePort(game_id=game_id)
        return (yield self.send(request))

    @gen.coroutine
    def authenticate(self, username, password, create_user=False):
        """ Send a SignIn request.
            :param username: username
            :param password: password
            :param create_user: boolean indicating if you want to create a user or login to and existing user.
            :return: a Channel object representing the authentication.
        """
        request = requests.SignIn(username=username, password=password, create_user=create_user)
        return (yield self.send(request))

    def send(self, request, for_game=None):
        """ Send a request.
            :param request: request object.
            :param for_game: (optional) NetworkGame object (required for game requests).
            :return: a Future that returns the response handler result of this request.
        """
        request_future = Future()
        request_context = RequestFutureContext(
            request=request, future=request_future, connection=self, game=for_game)

        self.write_request(request_context)
        return gen.with_timeout(
            timedelta(seconds=constants.REQUEST_TIMEOUT_SECONDS), request_future)

    def generate_written_callback(self, request_context):
        """ Generate and return the callback to call when a request is effectively written on
        socket.

        :param request_context: context of request to write
        :return: callback to call
        :type request_context: RequestFutureContext
        :rtype: callable
        """

        def callback(msg_future):
            """ Called when request is effectively written on socket.

                - If no exception occurs, do nothing.
                - Else if exception is a websockets error or a stream closed error, then
                  do nothing again and silently wait for reconnection.
                - Else, it's a fatal exception. Request won't receive response anymore,
                  and exception must be transferred to request future.
            """
            request_context.write_future = None
            exception = msg_future.exception()
            if exception:
                if isinstance(exception, (WebSocketClosedError, StreamClosedError)):
                    LOGGER.info('Socket error when writing request %s, waiting for reconnection.',
                                request_context.request_id)
                else:
                    # Fatal error while writing request. Request cannot be sent.
                    del self.requests_waiting_responses[request_context.request_id]
                    LOGGER.error('Fatal error occurred while writing a request.')
                    request_context.future.set_exception(exception)

        return callback

@gen.coroutine
def connect(hostname, port):
    """ Connect to given hostname and port.
        :param hostname: a hostname
        :param port: a port
        :return: a Connection object connected.
        :rtype: Connection
    """
    connection = Connection(hostname, port)
    yield connection.connect()
    return connection
