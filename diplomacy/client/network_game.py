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
""" Game object used on client side. """
import logging

from diplomacy.client.channel import Channel
from diplomacy.communication import notifications
from diplomacy.engine.game import Game
from diplomacy.utils.exceptions import DiplomacyException

LOGGER = logging.getLogger(__name__)

def game_request_method(channel_method):
    """Create a game request method that calls channel counterpart."""

    def func(self, **kwargs):
        """ Call channel-related method to send a game request with given kwargs. """
        # NB: Channel method returns a future.
        if not self.channel:
            raise DiplomacyException('Invalid client game.')
        return channel_method(self.channel, game_object=self, **kwargs)

    return func

def callback_setting_method(notification_class):
    """ Create a callback setting method for a given notification class. """

    def func(self, notification_callback):
        """ Add given callback for this game notification class. """
        self.add_notification_callback(notification_class, notification_callback)

    return func

def callback_clearing_method(notification_class):
    """ Create a callback clearing method for a given notification class. """

    def func(self):
        """ Clear user callbacks for this game notification class. """
        self.clear_notification_callbacks(notification_class)

    return func

class NetworkGame(Game):
    """ NetworkGame class. Properties:
        - channel: associated Channel object.
        - notification_callbacks: dict mapping a notification class name to a callback to be called
          when a corresponding game notification is received.
    """
    __slots__ = ['channel', 'notification_callbacks', 'data', '__weakref__']

    def __init__(self, channel, received_game):
        """ Initialize network game object with a channel and a game object sent by server.
            :param channel: a Channel object.
            :param received_game: a Game object.
            :type channel: diplomacy.client.channel.Channel
            :type received_game: diplomacy.Game
        """
        self.channel = channel
        self.notification_callbacks = {}  # {notification_class => [callback(game, notification)]}
        self.data = None
        # Initialize parent class with Jsonable attributes from received game.
        # Received game should contain a valid `initial_state` attribute that will be used
        # to set client game state.
        super(NetworkGame, self).__init__(**{key: getattr(received_game, key) for key in received_game.get_model()})

    # ===========
    # Public API.
    # ===========

    # NB: Method get_all_possible_orders() is only local in Python code,
    # but is still a network call from web interface.
    get_phase_history = game_request_method(Channel.get_phase_history)
    leave = game_request_method(Channel.leave_game)
    send_game_message = game_request_method(Channel.send_game_message)
    set_orders = game_request_method(Channel.set_orders)

    clear_centers = game_request_method(Channel.clear_centers)
    clear_orders = game_request_method(Channel.clear_orders)
    clear_units = game_request_method(Channel.clear_units)

    wait = game_request_method(Channel.wait)
    no_wait = game_request_method(Channel.no_wait)
    vote = game_request_method(Channel.vote)
    save = game_request_method(Channel.save)

    def synchronize(self):
        """ Send a Synchronize request to synchronize this game with associated server game. """
        if not self.channel:
            raise DiplomacyException('Invalid client game.')
        return self.channel.synchronize(game_object=self, timestamp=self.get_latest_timestamp())

    # Admin / Moderator API.
    delete = game_request_method(Channel.delete_game)
    kick_powers = game_request_method(Channel.kick_powers)
    set_state = game_request_method(Channel.set_state)
    process = game_request_method(Channel.process)
    query_schedule = game_request_method(Channel.query_schedule)
    start = game_request_method(Channel.start)
    pause = game_request_method(Channel.pause)
    resume = game_request_method(Channel.resume)
    cancel = game_request_method(Channel.cancel)
    draw = game_request_method(Channel.draw)

    # ===============================
    # Notification callback settings.
    # ===============================

    add_on_cleared_centers = callback_setting_method(notifications.ClearedCenters)
    add_on_cleared_orders = callback_setting_method(notifications.ClearedOrders)
    add_on_cleared_units = callback_setting_method(notifications.ClearedUnits)
    add_on_game_deleted = callback_setting_method(notifications.GameDeleted)
    add_on_game_message_received = callback_setting_method(notifications.GameMessageReceived)
    add_on_game_processed = callback_setting_method(notifications.GameProcessed)
    add_on_game_phase_update = callback_setting_method(notifications.GamePhaseUpdate)
    add_on_game_status_update = callback_setting_method(notifications.GameStatusUpdate)
    add_on_omniscient_updated = callback_setting_method(notifications.OmniscientUpdated)
    add_on_power_orders_flag = callback_setting_method(notifications.PowerOrdersFlag)
    add_on_power_orders_update = callback_setting_method(notifications.PowerOrdersUpdate)
    add_on_power_vote_updated = callback_setting_method(notifications.PowerVoteUpdated)
    add_on_power_wait_flag = callback_setting_method(notifications.PowerWaitFlag)
    add_on_powers_controllers = callback_setting_method(notifications.PowersControllers)
    add_on_vote_count_updated = callback_setting_method(notifications.VoteCountUpdated)
    add_on_vote_updated = callback_setting_method(notifications.VoteUpdated)

    clear_on_cleared_centers = callback_clearing_method(notifications.ClearedCenters)
    clear_on_cleared_orders = callback_clearing_method(notifications.ClearedOrders)
    clear_on_cleared_units = callback_clearing_method(notifications.ClearedUnits)
    clear_on_game_deleted = callback_clearing_method(notifications.GameDeleted)
    clear_on_game_message_received = callback_clearing_method(notifications.GameMessageReceived)
    clear_on_game_processed = callback_clearing_method(notifications.GameProcessed)
    clear_on_game_phase_update = callback_clearing_method(notifications.GamePhaseUpdate)
    clear_on_game_status_update = callback_clearing_method(notifications.GameStatusUpdate)
    clear_on_omniscient_updated = callback_clearing_method(notifications.OmniscientUpdated)
    clear_on_power_orders_flag = callback_clearing_method(notifications.PowerOrdersFlag)
    clear_on_power_orders_update = callback_clearing_method(notifications.PowerOrdersUpdate)
    clear_on_power_vote_updated = callback_clearing_method(notifications.PowerVoteUpdated)
    clear_on_power_wait_flag = callback_clearing_method(notifications.PowerWaitFlag)
    clear_on_powers_controllers = callback_clearing_method(notifications.PowersControllers)
    clear_on_vote_count_updated = callback_clearing_method(notifications.VoteCountUpdated)
    clear_on_vote_updated = callback_clearing_method(notifications.VoteUpdated)

    def add_notification_callback(self, notification_class, notification_callback):
        """ Add a callback for a notification.
            :param notification_class: a notification class
            :param notification_callback: callback to add.
        """
        assert callable(notification_callback)
        if notification_class not in self.notification_callbacks:
            self.notification_callbacks[notification_class] = [notification_callback]
        else:
            self.notification_callbacks[notification_class].append(notification_callback)

    def clear_notification_callbacks(self, notification_class):
        """ Remove all user callbacks for a notification.
            :param notification_class: a notification class
        """
        self.notification_callbacks.pop(notification_class, None)

    def notify(self, notification):
        """ Notify game with given notification (call associated callbacks if defined). """
        for callback in self.notification_callbacks.get(type(notification), ()):
            callback(self, notification)
