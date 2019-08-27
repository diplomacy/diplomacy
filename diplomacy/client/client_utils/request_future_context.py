""" Helper class to store a context around a request. """
from diplomacy.client.channel import Channel
from diplomacy.client.client_utils.game_instances_set import GameInstancesSet
from diplomacy.client.network_game import NetworkGame

class RequestFutureContext:
    """ Request context class. Properties;

    - **connection**: Connection object which handle the request.
    - **game**: optional NetworkGame object associated to the request.
    - **future** : Future object to handle request response.
    - **request**: request to send.
    - **write_future**: Future object to handle request writing on socket.
    """
    __slots__ = ['request', 'future', 'connection', 'game', 'write_future']

    def __init__(self, request, future, connection, game=None):
        """ Initialize a request future context.
            :param request: a request object (see diplomacy.communication.requests about possible classes).
            :param future: a tornado Future object.
            :param connection: a diplomacy.Connection object.
            :param game: (optional) a NetworkGame object (from module diplomacy.client.network_game).
            :type request: diplomacy.communication.requests._AbstractRequest
            :type future: tornado.concurrent.Future
            :type connection: diplomacy.client.connection.Connection
            :type game: diplomacy.client.network_game.NetworkGame
        """
        self.request = request
        self.future = future
        self.connection = connection
        self.game = game
        self.write_future = None

    request_id = property(lambda self: self.request.request_id)
    token = property(lambda self: self.request.token)
    channel = property(lambda self: self.connection.channels[self.request.token])

    def new_channel(self, token):
        """ Create, store (in associated connection), and return a new channel with given token. """
        channel = Channel(self.connection, token)
        self.connection.channels[token] = channel
        return channel

    def new_game(self, received_game):
        """ Create, store (in associated connection) and return a new network game wrapping given game data.
            Returned game is already in appropriate type (observer game, omniscient game or power game).
            :param received_game: game sent by server (Game object)
            :type received_game: Game
        """
        game = NetworkGame(self.channel, received_game)
        if game.game_id not in self.channel.game_id_to_instances:
            self.channel.game_id_to_instances[game.game_id] = GameInstancesSet(game.game_id)
        self.channel.game_id_to_instances[game.game_id].add(game)
        return game

    def remove_channel(self):
        """ Remove associated channel (inferred from request token) from associated connection. """
        del self.connection.channels[self.channel.token]

    def delete_game(self):
        """ Delete local game instances corresponding to game ID in associated request. """
        assert hasattr(self.request, 'game_id')
        assert self.game is not None and self.game.game_id == self.request.game_id
        if self.request.game_id in self.channel.game_id_to_instances:
            del self.channel.game_id_to_instances[self.request.game_id]
