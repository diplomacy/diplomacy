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

import diplomacy.communication.notifications as notifications
import diplomacy.daide as daide
import diplomacy.daide.notifications
from diplomacy.daide.settings import MAX_LVL
import diplomacy.daide.utils
from diplomacy.utils import results as res, strings, subject_split

def on_game_processed_notification(server, notification, connection_handler, game):
    _, _, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
    previous_phase_data = notification.previous_phase_data
    previous_state = previous_phase_data.state
    phase_data = notification.current_phase_data
    state = phase_data.state

    notifs = []

    # ORD notifications
    for order in previous_phase_data.orders[power_name]:
        previous_phase = subject_split.PhaseSplit.split(previous_state['name'])

        order = subject_split.OrderSplit.split(order)
        results = None

        # WAIVE
        if len(order) == 1:
            order.command = ' '.join([power_name, order.command])
            results = [res.OK]
        else:
            results = previous_phase_data.results[order.unit]
            order.unit = ' '.join([power_name, order.unit])

        if order.additional_unit:
            order.additional_unit = ' '.join([power_name, order.additional_unit])

        order_bytes = daide.clauses.parse_order_to_bytes(previous_phase.type, order)
        notifs.append(daide.notifications.ORD(previous_phase.in_str, order_bytes, [result.code for result in results]))

    if state['status'] == strings.ACTIVE:
        phase = subject_split.PhaseSplit.split(state['name'])

        # SCO notification
        # TODO: get map_name from somewhere else than game if possible
        notifs.append(daide.notifications.SCO(state['centers'], game.map_name))

        # NOW notification
        units = {power_name: [unit for unit in units if not unit.startswith('*')] for power_name, units in state['units'].items()}
        retreats = state['retreats'].copy()
        notifs.append(daide.notifications.NOW(phase.in_str, units, retreats))

        # TME notification
        # TODO: get deadline from somewhere else than game if possible
        notifs.append(daide.notifications.TME(game.deadline))

    # TODO
    elif state['status'] == strings.COMPLETED:
        if game.has_draw_vote():
            notifs.append(daide.notifications.DRW())
        else:
            winners = [power_name for power_name, units in state['units'].items() if units]
            if len(winners) == 1:
                notifs.append(daide.notifications.SLO(winners[0]))

    #     notifs.append(daide.notifications.SMR())
        notifs.append(daide.notifications.OFF())

    return notifs

def on_game_status_update_notification(server, notification, connection_handler, game):
    _, user_additions, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
    notifs = []

    if notification.status == strings.ACTIVE and game.get_current_phase() == 'S1901M':
        phase = subject_split.PhaseSplit.split(game.get_current_phase())

        # HLO notification
        passcode = user_additions.passcode
        level = MAX_LVL
        deadline = game.deadline
        rules = game.rules
        notifs.append(daide.notifications.HLO(power_name, passcode, level, deadline, rules))

        # SCO notification
        power_centers = {power.name: power.centers for power in game.powers.values()}
        notifs.append(daide.notifications.SCO(power_centers, game.map_name))

        # NOW notification
        units = {power.name: power.units for power in game.powers.values()}
        retreats = {power.name: power.retreats for power in game.powers.values()}
        notifs.append(daide.notifications.NOW(phase.in_str, units, retreats))

        # TME notification
        notifs.append(daide.notifications.TME(game.deadline))

    # TODO
    elif notification.status == strings.COMPLETED:
        notifs.append(daide.notifications.OFF())

    elif notification.status == strings.CANCELED:
        notifs.append(daide.notifications.OFF())

    return notifs

def on_game_message_received_notification(server, notification, connection_handler, game):
    _, user_additions, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
    notifs = []

    message = notification.message

    notifs.append(daide.notifications.FRM(message.sender, [message.recipient], message.message))

    return notifs

MAPPING = {
    notifications.GameProcessed: on_game_processed_notification,
    notifications.GameStatusUpdate: on_game_status_update_notification,
    notifications.GameMessageReceived: on_game_message_received_notification
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
