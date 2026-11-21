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

""" Tests for client response managers. """
from types import SimpleNamespace

import pytest

from diplomacy.client.response_managers import on_get_phase_history
from diplomacy.engine.game import Game
from diplomacy.engine.message import Message
from diplomacy.utils.game_phase_data import GamePhaseData


def _phase_data(name, marker, message=None):
    messages = {}
    if message is not None:
        messages[1] = Message(sender='FRANCE', recipient='GLOBAL',
                              time_sent=1, phase=name, message=message)
    return GamePhaseData(name=name, state={'marker': marker}, orders={},
                         results={}, messages=messages)


def _handle(game, phase_data):
    response = SimpleNamespace(data=phase_data)
    return on_get_phase_history(SimpleNamespace(game=game), response), response


def test_get_phase_history_skips_known_phases_and_adds_new_ones():
    game = Game()
    game.extend_phase_history(_phase_data('S1901M', 'local', 'local message'))
    new_phase = _phase_data('F1901M', 'remote', 'remote message')
    response_data = [_phase_data('S1901M', 'response', 'response message'), new_phase]

    result, response = _handle(game, response_data)

    assert result is response.data
    known = game._phase_wrapper_type('S1901M')
    assert game.state_history[known] == {'marker': 'local'}
    assert game.message_history[known][1].message == 'local message'
    for history in (game.state_history, game.order_history,
                    game.result_history, game.message_history):
        assert game._phase_wrapper_type('F1901M') in history

    result, _ = _handle(game, response_data)

    assert result is response.data
    assert game.state_history[known] == {'marker': 'local'}
    assert game.message_history[known][1].message == 'local message'
    assert [str(phase) for phase in game.state_history] == ['S1901M', 'F1901M']


def test_get_phase_history_rejects_partially_known_phase():
    game = Game()
    phase = game._phase_wrapper_type('S1901M')
    game.state_history.put(phase, {'marker': 'local'})
    response_data = [_phase_data('S1901M', 'response', 'response message')]

    with pytest.raises(ValueError, match='S1901M'):
        _handle(game, response_data)

    assert game.state_history[phase] == {'marker': 'local'}
    for history in (game.order_history, game.result_history, game.message_history):
        assert phase not in history
