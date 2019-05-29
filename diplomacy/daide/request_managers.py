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

import random
import uuid
from tornado import gen
from tornado.concurrent import Future
import diplomacy.communication.requests as internal_requests
import diplomacy.communication.responses as internal_responses
import diplomacy.daide as daide
import diplomacy.daide.clauses
import diplomacy.daide.requests
import diplomacy.daide.responses
from diplomacy.daide.settings import MAX_LVL
import diplomacy.daide.tokens
from diplomacy.daide.user_additions import UserAdditions
import diplomacy.daide.utils
from diplomacy.engine.message import Message
import diplomacy.server.request_managers as internal_request_managers
from diplomacy.utils import errors as err, exceptions, results as res, strings

@gen.coroutine
def on_name_request(server, request, connection_handler, game):
    username = connection_handler.get_name_variant() + request.client_name

    try:
        server.assert_token(connection_handler.token, connection_handler)
    except:
        connection_handler.token = None

    if not connection_handler.token:
        user_exists = server.users.has_username(username)

        sign_in_request = internal_requests.SignIn(
            username=username,
            password='1234',
            create_user=not user_exists
        )

        try:
            token_response = yield internal_request_managers.handle_request(server, sign_in_request, connection_handler)
            connection_handler.token = token_response.data
            if not server.users.get_daide_user_additions(username):
                user_additions = UserAdditions(passcode=random.randint(1, 8191), client_name=request.client_name,
                                               client_version=request.client_version)
                server.users.set_daide_user_additions(username, user_additions)
                server.save_data()
        except exceptions.UserException as e:
            return [daide.responses.REJ(bytes(request))]

    # find next available power
    power_name = [power_name for power_name, power in game.powers.items() if not power.is_controlled()]
    if not power_name:
        return [daide.responses.REJ(bytes(request))]

    return [daide.responses.YES(bytes(request)), daide.responses.MAP(game.map.name)]

def on_observer_request(server, request, connection_handler, game):
    # No DAIDE observeres allowed
    return [daide.responses.REJ(bytes(request))]

@gen.coroutine
def on_i_am_request(server, request, connection_handler, game):
    power_name, passcode = request.power_name, request.passcode

    # find user
    is_user_found = False
    for username, user_additions in server.users.daide_users_additions.items():
        is_passcode_valid = user_additions.passcode == passcode
        is_user_found = game.is_controlled_by(power_name, username) if is_passcode_valid else False
        if is_user_found:
            break

    if not is_user_found:
        return [daide.responses.REJ(bytes(request))]

    try:
        server.assert_token(connection_handler.token, connection_handler)
    except:
        connection_handler.token = None

    if not connection_handler.token:
        sign_in_request = internal_requests.SignIn(
            username=username,
            password='1234',
            create_user=False
        )

        try:
            token_response = yield internal_request_managers.handle_request(server, sign_in_request, connection_handler)
            connection_handler.token = token_response.data
        except exceptions.UserException as e:
            return [daide.responses.REJ(bytes(request))]

    join_game_request = internal_requests.JoinGame(
        game_id=game.game_id,
        power_name=power_name,
        registration_password=None,
        token=connection_handler.token
    )

    join_game_response = yield internal_request_managers.handle_request(server, join_game_request, connection_handler)

    return [daide.responses.YES(bytes(request))]

def on_hello_request(server, request, connection_handler, game):
    _, user_additions, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    # User not in game
    if not user_additions or not power_name:
        return [daide.responses.REJ(bytes(request))]

    passcode = user_additions.passcode
    level = MAX_LVL
    deadline = game.deadline
    rules = game.rules

    return [daide.responses.HLO(power_name, passcode, level, deadline, rules)]

def on_map_request(server, request, connection_handler, game):
    return [daide.responses.MAP(game.map.name)]

def on_map_definition_request(server, request, connection_handler, game):
    return [daide.responses.MDF(game.map_name)]

def on_supply_centre_ownership_request(server, request, connection_handler, game):
    return [daide.responses.SCO(game.powers.values(), game.map_name)]

def on_current_position_request(server, request, connection_handler, game):
    return [daide.responses.NOW(game.map.phase_abbr(game.phase), game.powers)]

def on_history_request(server, request, connection_handler, game):
    # TODO: implement
    raise NotImplementedError

@gen.coroutine
# def on_submit_orders_request(server, request, connection_handler, game):
#     _, user_additions, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
#     token = server.users.connection_handler_to_tokens.get(connection_handler, None)
#
#     if request.phase and not request.phase == game.get_current_phase():
#         return [daide.responses.REJ(bytes(request))]
#
#     power_name = user_additions.power_name
#
#     initial_power_orders = game.get_power(power_name).orders
#     initial_game_errors = game.errors[:]
#     # initial_game_results = game.results[:]
#
#     responses = []
#
#     # Parsing
#     lead_token, request_bytes = parse_bytes(daide.clauses.SingleToken, bytes(request))
#     _, request_bytes = parse_bytes(daide.clauses.Turn, request_bytes, on_error='ignore')
#
#     if game.phase_type == 'R':
#         retreated = []
#         while request_bytes:
#             daide_order, request_bytes = parse_bytes(daide.clauses.Order, request_bytes)
#             order = str(daide_order)
#
#             order, error = game._valid_retreat_order(power, order, order.split(), retreated)
#             if order and not error:
#                 # Marking unit as retreated
#                 retreated.append(' '.join(order.split()[:2]))
#             else if not order and not error:
#                 error = err.GAME_UNRECOGNIZED_ORDER_DATA % order
#
#             responses.append(daide.responses.THX(daide_order, [error.code if error else res.OK.code]))
#     elif game.phase_type == 'A':
#         game._update_adjust_orders(power, orders, expand=expand, replace=replace)
#     else:
#         game._update_orders(power, orders, expand=expand, replace=replace)
#
#     request.game_id = game.game_id
#     request.token = token
#     # TODO: check if this should be wrapped in try except or if the request
#     # should be considered to have failed in whole as soon as an exception
#     # is raised
#     set_orders_response = yield internal_request_managers.handle_request(server, set_orders_request, connection_handler)
#
#     responses.append(daide.responses.MIS(game.get_current_phase(), game.get_power(power_name)))
#
#     return responses

def on_submit_orders_request(server, request, connection_handler, game):
    _, user_additions, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    if request.phase and not request.phase == game.get_current_phase():
        return [daide.responses.REJ(bytes(request))]

    request.token = token

    power = game.get_power(power_name)
    initial_power_adjusts = power.adjust[:]
    initial_power_orders = [] # power.orders.copy()
    initial_game_errors = game.error[:]
    # initial_game_results = game.results[:]

    responses = []

    # Parsing
    lead_token, request_bytes = daide.clauses.parse_bytes(daide.clauses.SingleToken, bytes(request))
    _, request_bytes = daide.clauses.parse_bytes(daide.clauses.Turn, request_bytes, on_error='ignore')

    # Validate each order individually
    while request_bytes:
        daide_order, request_bytes = daide.clauses.parse_bytes(daide.clauses.Order, request_bytes)
        order = str(daide_order)

        set_orders_request = internal_requests.SetOrders(
            power_name=request.power_name,
            orders=[order],
            game_id=request.game_id,
            game_role=request.power_name,
            phase=request.phase,
            token=request.token
        )
        # TODO: check if this should be wrapped in try except or if the request
        # should be considered to have failed in whole as soon as an exception
        # is raised
        set_orders_response = yield internal_request_managers.handle_request(server, set_orders_request, connection_handler)

        new_power_adjusts = [adjust for adjust in power.adjust if adjust not in initial_power_adjusts]
        new_power_orders = {id: val for id, val in power.orders.items() if id not in initial_power_orders}
        new_game_errors = [error.code for error in game.error if error not in initial_game_errors]
        # new_game_results = [result.id for result in game.results[:] if result not in initial_game_results]

        if not new_power_adjusts and not new_power_orders and not new_game_errors:
            new_game_errors.append((err.GAME_ORDER_NOT_ALLOWED % order).code)

        responses.append(daide.responses.THX(bytes(daide_order), new_game_errors))

    set_orders_request = internal_requests.SetOrders(
        power_name=request.power_name,
        orders=request.orders,
        game_id=request.game_id,
        game_role=request.power_name,
        phase=request.phase,
        token=request.token
    )
    set_orders_response = yield internal_request_managers.handle_request(server, set_orders_request, connection_handler)

    responses.append(daide.responses.MIS(game.get_current_phase(), power))

    return responses

def on_missing_orders_request(server, request, connection_handler, game):
    _, _, _, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)
    if not power_name:
        return [daide.responses.REJ(bytes(request))]
    return [daide.responses.MIS(game.get_current_phase(), game.get_power(power_name))]

@gen.coroutine
def on_go_flag_request(server, request, connection_handler, game):
    _, _, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    set_wait_flag_request = internal_requests.SetWaitFlag(
        power_name=power_name,
        wait=False,
        game_id=request.game_id,
        game_role=power_name,
        phase=game.get_current_phase(),
        token=token
    )
    set_wait_flag_response = yield internal_request_managers.handle_request(server, set_wait_flag_request, connection_handler)

    if not game.get_power(power_name).order_is_set:
        set_orders_request = internal_requests.SetOrders(
            power_name=power_name,
            orders=[],
            game_id=request.game_id,
            game_role=power_name,
            phase=game.get_current_phase(),
            token=token
        )
        set_orders_response = yield internal_request_managers.handle_request(server, set_orders_request,
                                                                             connection_handler)

    return [daide.responses.YES(bytes(request))]

def on_time_to_deadline_request(server, request, connection_handler, game):
    return [daide.responses.REJ(bytes(request))]

@gen.coroutine
def on_draw_request(server, request, connection_handler, game):
    _, _, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    vote_request = internal_requests.Vote(
        power_name=power_name,
        vote=strings.YES,
        game_role=power_name,
        phase=game.get_current_phase(),
        game_id=game.game_id,
        token=token
    )
    vote_response = yield internal_request_managers.handle_request(server, vote_request, connection_handler)

    return [daide.responses.YES(bytes(request))]

@gen.coroutine
def on_send_message_request(server, request, connection_handler, game):
    _, _, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    message = ' '.join([str(daide.tokens.Token(from_bytes=(request.message_bytes[i], request.message_bytes[i+1])))
                        for i in range(0, len(request.message_bytes), 2)])

    for receipient_power_name in request.powers:
        game_message = Message(
            sender=power_name,
            recipient=receipient_power_name,
            phase=game.get_current_phase(),
            message=message
        )
        send_game_message_request = internal_requests.SendGameMessage(
            power_name=power_name,
            message=game_message,
            game_role=power_name,
            phase=game.get_current_phase(),
            game_id=game.game_id,
            token=token
        )
        send_game_message_response = \
            yield internal_request_managers.handle_request(server, send_game_message_request, connection_handler)

    return [daide.responses.YES(bytes(request))]

@gen.coroutine
def on_not_request(server, request, connection_handler, game):
    _, _, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    response = None
    not_request = request.request

    if isinstance(not_request, daide.requests.SUB):
        if not_request.orders:
            # cancel one order
            pass
        else:
            clear_orders_request = internal_requests.ClearOrders(
                power_name=power_name,
                game_id=game.game_id,
                game_role=power_name,
                phase=game.get_current_phase(),
                token=token
            )
            clear_orders_response = yield internal_request_managers.handle_request(server, clear_orders_request, connection_handler)
            response = daide.responses.YES(bytes(request))

    elif isinstance(not_request, daide.requests.GOF):
        set_wait_flag_request = internal_requests.SetWaitFlag(
            power_name=power_name,
            wait=True,
            game_id=game.game_id,
            game_role=power_name,
            phase=game.get_current_phase(),
            token=token
        )
        set_wait_flag_response = yield internal_request_managers.handle_request(server, set_wait_flag_request, connection_handler)

        response = daide.responses.YES(bytes(request))

    elif isinstance(not_request, daide.requests.TME):
        response = daide.responses.REJ(bytes(request))

    elif isinstance(not_request, daide.requests.DRW):
        vote_request = internal_requests.Vote(
            power_name=power_name,
            vote=strings.NEUTRAL,
            game_role=power_name,
            phase=game.get_current_phase(),
            game_id=game.game_id,
            token=token
        )
        vote_response = yield internal_request_managers.handle_request(server, vote_request, connection_handler)

        response = daide.responses.YES(bytes(request))

    return [response if response else daide.responses.REJ(bytes(request))]

@gen.coroutine
def on_accept_request(server, request, connection_handler, game):
    _, _, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    response = None
    accept_response = request.response_bytes

    lead_token, _ = daide.clauses.parse_bytes(daide.clauses.SingleToken, accept_response)

    if bytes(lead_token) == bytes(daide.tokens.MAP):
        if not power_name:
            # find next available power
            power_name = [power_name for power_name, power in game.powers.items() if not power.is_controlled()]
            if not power_name:
                return [daide.responses.OFF()]
            power_name = power_name[0]

            join_game_request = internal_requests.JoinGame(
                game_id=game.game_id,
                power_name=power_name,
                registration_password=None,
                token=token
            )

            join_game_response = yield internal_request_managers.handle_request(server, join_game_request,
                                                                                connection_handler)

    return [response] if response else None

def on_reject_request(server, request, connection_handler, game):
    _, _, token, power_name = daide.utils.get_user_connection(server.users, game, connection_handler)

    response = None
    reject_response = request.response_bytes

    lead_token, _ = daide.clauses.parse_bytes(daide.clauses.SingleToken, reject_response)

    if bytes(lead_token) == bytes(daide.tokens.MAP):
        response = daide.responses.OFF()

    return [response] if response else None

def on_parenthesis_error_request(server, request, connection_handler, game):
    return None

def on_syntax_error_request(server, request, connection_handler, game):
    return None

def on_admin_message_request(server, request, connection_handler, game):
    return None

# Mapping dictionary from request class to request handler function.
MAPPING = {
    daide.requests.NameRequest: on_name_request,
    daide.requests.ObserverRequest: on_observer_request,
    daide.requests.IAmRequest: on_i_am_request,
    daide.requests.HelloRequest: on_hello_request,
    daide.requests.MapRequest: on_map_request,
    daide.requests.MapDefinitionRequest: on_map_definition_request,
    daide.requests.SupplyCentreOwnershipRequest: on_supply_centre_ownership_request,
    daide.requests.CurrentPositionRequest: on_current_position_request,
    daide.requests.HistoryRequest: on_history_request,
    daide.requests.SubmitOrdersRequest: on_submit_orders_request,
    daide.requests.MissingOrdersRequest: on_missing_orders_request,
    daide.requests.GoFlagRequest: on_go_flag_request,
    daide.requests.TimeToDeadlineRequest: on_time_to_deadline_request,
    daide.requests.DrawRequest: on_draw_request,
    daide.requests.SendMessageRequest: on_send_message_request,
    daide.requests.NotRequest: on_not_request,
    daide.requests.AcceptRequest: on_accept_request,
    daide.requests.RejectRequest: on_reject_request,
    daide.requests.ParenthesisErrorRequest: on_parenthesis_error_request,
    daide.requests.SyntaxErrorRequest: on_syntax_error_request,
    daide.requests.AdminMessageRequest: on_admin_message_request
}

def handle_request(server, request, connection_handler):
    """ (coroutine) Find request handler function for associated request, run it and return its result.
        :param server: a Server object to pass to handler function.
        :param request: a request object to pass to handler function.
            See diplomacy.communication.requests for possible requests.
        :param connection_handler: a ConnectionHandler object to pass to handler function.
        :return: (future) either None or a response object.
            See module diplomacy.communication.responses for possible responses.
    """
    request_handler_fn = MAPPING.get(type(request), None)
    if not request_handler_fn:
        raise exceptions.RequestException()

    game = server.get_game(request.game_id)

    # Game not found
    if not game or game.is_game_completed or game.is_game_canceled:
        future = Future()
        future.set_result([daide.responses.REJ(bytes(request))])
        return future

    if gen.is_coroutine_function(request_handler_fn):
        # Throw the future returned by this coroutine.
        return request_handler_fn(server, request, connection_handler, game)
    # Create and return a future.
    future = Future()
    try:
        result = request_handler_fn(server, request, connection_handler, game)
        future.set_result(result)
    except exceptions.DiplomacyException as exc:
        future.set_exception(exc)

    return future
