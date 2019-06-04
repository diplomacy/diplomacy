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

# =================
# Request managers.
# =================
""" DAIDE Notification managers """
import diplomacy.communication.notifications as notifications
import diplomacy.daide as daide
from diplomacy.daide.settings import MAX_LVL
from diplomacy.server.user import DaideUser
from diplomacy.utils import order_results as res, strings, splitter

def _build_active_notfications(current_phase, powers, map_name, deadline):
    """ Build the list of notifications corresponding to an active game state
        :param current_phase: the current phase
        :param powers: the list of game's powers
        :param map_name: the map name
        :param deadline: the deadline of the game
        :return: list of notifications
    """
    notififcations = []

    # SCO notification
    power_centers = {power.name: power.centers for power in powers}
    notififcations.append(daide.notifications.SCO(power_centers, map_name))

    # NOW notification
    units = {power.name: power.units for power in powers}
    retreats = {power.name: power.retreats for power in powers}
    notififcations.append(daide.notifications.NOW(current_phase, units, retreats))

    # TME notification
    notififcations.append(daide.notifications.TME(deadline))

    return notififcations

def _build_completed_notfications(server_users, has_draw_vote, powers, state_history):
    """ Build the list of notifications corresponding to a completed game state
        :param server_users: the instance of `diplomacy.server.users` of the game's server
        :param has_draw_vote: true if the game has completed due to a draw vote
        :param powers: the list of game's powers
        :param state_history: the states history of the game
        :return: list of notifications
    """
    notififcations = []

    if has_draw_vote:
        notififcations.append(daide.notifications.DRW())
    else:
        winners = [power.name for power in powers if power.units]
        if len(winners) == 1:
            notififcations.append(daide.notifications.SLO(winners[0]))

    last_phase = splitter.PhaseSplitter(state_history.last_value()['name'])
    daide_users = [server_users.get_user(power.get_controller()) for power in powers]
    daide_users = [daide_user if isinstance(daide_user, DaideUser) else None for daide_user in daide_users]
    powers_year_of_elimnation = {power.name: None for power in powers}
    for phase, state in state_history.items():
        eliminated_powers = [power_name for power_name, units in state['units'].items()
                             if not powers_year_of_elimnation[power_name] and
                             all(unit.startswith('*') for unit in units)]
        for power_name in eliminated_powers:
            powers_year_of_elimnation[power_name] = splitter.PhaseSplitter(phase.value).year

    years_of_elimnation = powers_year_of_elimnation.values()

    notififcations.append(daide.notifications.SMR(last_phase.input_str, powers,
                                                  daide_users, years_of_elimnation))
    notififcations.append(daide.notifications.OFF())

    return notififcations

def on_processed_notification(server, notification, connection_handler, game):
    """ Build the list of notificaitons for a game processed event
        :param server: server which receives the request
        :param notification: internal notification
        :param connection_handler: connection handler from which the request was sent
        :param game: the game
        :return: list of notificaitons
    """
    _, _, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
    previous_phase_data = notification.previous_phase_data
    previous_state = previous_phase_data.state
    previous_phase = splitter.PhaseSplitter(previous_state['name'])

    notifs = []

    # ORD notifications
    for order in previous_phase_data.orders[power_name]:
        order = splitter.OrderSplitter(order)
        results = None

        # WAIVE
        if len(order) == 1:
            order.command = ' '.join([power_name, order.command])
            results = [res.OK]
        else:
            results = previous_phase_data.results[order.unit]
            order.unit = ' '.join([power_name, order.unit])

        if order.supported_unit:
            order.supported_unit = ' '.join([power_name, order.supported_unit])

        order_bytes = daide.clauses.parse_order_to_bytes(previous_phase.phase_type, order)
        notifs.append(daide.notifications.ORD(previous_phase.input_str, order_bytes, [result.code for result in results]))

    if game.status == strings.ACTIVE:
        notifs += _build_active_notfications(game.get_current_phase(), game.powers.values(),
                                             game.map_name, game.deadline)

    elif game.status == strings.COMPLETED:
        notifs += _build_completed_notfications(server.users, game.has_draw_vote(),
                                                game.powers.values(), game.state_history)

    return notifs

def on_status_update_notification(server, notification, connection_handler, game):
    """ Build the list of notificaitons for a status update event
        :param server: server which receives the request
        :param notification: internal notification
        :param connection_handler: connection handler from which the request was sent
        :param game: the game
        :return: list of notificaitons
    """
    _, daide_user, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
    notifs = []

    if notification.status == strings.ACTIVE and game.get_current_phase() == 'S1901M':
        # HLO notification
        passcode = daide_user.passcode
        level = MAX_LVL
        deadline = game.deadline
        rules = game.rules
        notifs.append(daide.notifications.HLO(power_name, passcode, level, deadline, rules))

        notifs += _build_active_notfications(game.get_current_phase(), game.powers.values(),
                                             game.map_name, game.deadline)

    elif notification.status == strings.COMPLETED:
        notifs += _build_completed_notfications(server.users, game.has_draw_vote(),
                                                game.powers.values(), game.state_history)

    elif notification.status == strings.CANCELED:
        notifs.append(daide.notifications.OFF())

    return notifs

def on_message_received_notification(server, notification, connection_handler, game):
    """ Build the list of notificaitons for a message received event
        :param server: server which receives the request
        :param notification: internal notification
        :param connection_handler: connection handler from which the request was sent
        :param game: the game
        :return: list of notificaitons
    """
    del server
    del connection_handler
    del game
    notifs = []

    message = notification.message

    notifs.append(daide.notifications.FRM(message.sender, [message.recipient], message.message))

    return notifs

MAPPING = {
    notifications.GameProcessed: on_processed_notification,
    notifications.GameStatusUpdate: on_status_update_notification,
    notifications.GameMessageReceived: on_message_received_notification
}

def translate_notification(server, notification, connection_handler):
    """ Find notification handler function for associated notification, run it and return its result.
        :param server: a Server object to pass to handler function.
        :param notification: a notification object to pass to handler function.
            See diplomacy.communication.notifications for possible notifications.
        :param connection_handler: a ConnectionHandler object to pass to handler function.
        :return: either None or an array of daide notifications.
            See module diplomacy.daide.notifications for possible daide notifications.
    """
    notification_handler_fn = MAPPING.get(type(notification), None)

    game = server.get_game(notification.game_id)

    # Game not found
    if not game or not notification_handler_fn:
        return None

    return notification_handler_fn(server, notification, connection_handler, game)
