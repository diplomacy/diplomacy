""" Class performing reconnection work for a given connection. """
import logging
from diplomacy.communication import requests
from diplomacy.utils import exceptions, strings

LOGGER = logging.getLogger(__name__)

class Reconnection:
    """ Reconnection class.

    TODO Reconnection is still bugged.
    TODO Update this documentation.
    """

    __slots__ = ['connection', 'games_phases', 'n_expected_games', 'n_synchronized_games',
                 'requests_to_send']

    def __init__(self, connection):
        """ Initialize reconnection data/
            :param connection: connection to reconnect.
            :type connection: Connection
        """
        self.connection = connection
        self.games_phases = {}
        self.n_expected_games = 0
        self.n_synchronized_games = 0
        self.requests_to_send = {}

    def reconnect(self):
        """ Perform concrete reconnection work. """

        LOGGER.debug('Trying to synchronize, with %d remaining requests',
                     len(self.connection.requests_waiting_responses))

        # Remove all previous synchronisation requests, and mark all remaining request as re-sent.
        for context in self.connection.requests_waiting_responses.values():
            if isinstance(context.request, requests.Synchronize):
                context.future.set_exception(exceptions.DiplomacyException(
                    'Sync request invalidated for game ID %s.' % context.request.game_id))
            else:
                context.request.re_sent = True
                self.requests_to_send[context.request.request_id] = context
        self.connection.requests_waiting_responses.clear()

        # Count games to synchronize.
        for channel in self.connection.channels.values():
            for game_instance_set in channel.game_id_to_instances.values():
                for game in game_instance_set.get_games():
                    self.games_phases.setdefault(game.game_id, {})[game.role] = None
                    self.n_expected_games += 1

        if self.n_expected_games:
            # Synchronize games.
            for channel in self.connection.channels.values():
                for game_instance_set in channel.game_id_to_instances.values():
                    for game in game_instance_set.get_games():
                        game.synchronize().add_done_callback(self.generate_sync_callback(game))
        else:
            # No game to sync, finish sync now.
            self.sync_done()

    def generate_sync_callback(self, game):
        """ Generate callback to call when response to sync request is received for given game.
            :param game: game
            :return: a callback.
            :type game: diplomacy.client.network_game.NetworkGame
        """

        def on_sync(future):
            """ Callback. If exception occurs, print it as logging error.
            Else, register server response, and move forward to final
            reconnection work if all games received sync responses.
            """
            exception = future.exception()
            if exception is not None:
                LOGGER.error(str(exception))
            else:
                self.games_phases[game.game_id][game.role] = future.result()
                self.n_synchronized_games += 1
                if self.n_synchronized_games == self.n_expected_games:
                    self.sync_done()

        return on_sync

    def sync_done(self):
        """ Final reconnection work. Remove obsolete game requests and send remaining requests. """

        # All sync requests sent have finished.
        # Remove all obsolete game requests from connection.
        # A game request is obsolete if it's phase-dependent
        # and if its phase does not match current game phase.

        request_to_send_updated = {}
        for context in self.requests_to_send.values():  # type: RequestFutureContext
            keep = True
            if context.request.level == strings.GAME and context.request.phase_dependent:
                request_phase = context.request.phase
                server_phase = self.games_phases[context.request.game_id][context.request.game_role].phase
                if request_phase != server_phase:
                    # Request is obsolete.
                    context.future.set_exception(exceptions.DiplomacyException(
                        'Game %s: request %s: request phase %s does not match current server game phase %s.'
                        % (context.request.game_id, context.request.name, request_phase, server_phase)))
                    keep = False
            if keep:
                request_to_send_updated[context.request.request_id] = context

        LOGGER.debug('Keep %d/%d old requests to send.',
                     len(request_to_send_updated), len(self.requests_to_send))

        # Send requests.
        for request_to_send in request_to_send_updated.values():  # type: RequestFutureContext
            self.connection.write_request(request_to_send)

        # We are reconnected.
        self.connection.is_reconnecting.set()
        LOGGER.info('Done reconnection work.')
