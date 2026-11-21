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
"""Test default orders.

    Engine defaults are not submitted orders. They must not appear in get_orders()
    or order_history, while their effects remain visible in phase results and in
    unit positions.
"""
from diplomacy.engine.game import Game
from diplomacy.utils.order_results import DISBAND, OK


def test_unordered_movement_unit_holds_without_an_order_string():
    """An unordered movement unit holds without being recorded as submitted."""
    game = Game()
    game.set_orders('FRANCE', ['A PAR - BUR'])
    submitted = game.get_orders('FRANCE')

    phase = game.process()

    assert submitted == ['A PAR - BUR']
    assert phase.orders['FRANCE'] == submitted
    assert game.order_history[phase.name]['FRANCE'] == submitted
    assert 'A BUR' in game.get_units('FRANCE')
    # A MAR held by default, but that hold was not a submitted order.
    assert 'A MAR' in game.get_units('FRANCE')
    # An empty result entry is not proof of a hold.
    assert 'A MAR' in phase.results
    assert phase.results['A MAR'] == []
    assert phase.results['A PAR'] == []


def test_adjustment_auto_disband_is_not_a_submitted_order():
    """Automatic adjustment removals report OK and are not submitted orders."""
    game = Game()
    game.clear_centers('FRANCE')
    game.set_current_phase('W1901A')
    units_before = set(game.get_units('FRANCE'))
    assert game.get_orders('FRANCE') == []

    phase = game.process()

    assert phase.orders['FRANCE'] == []
    assert game.order_history[phase.name]['FRANCE'] == []
    assert not game.get_units('FRANCE')
    for unit in units_before:
        assert OK in phase.results[unit]
        assert DISBAND not in phase.results[unit]


def test_retreat_default_disband_is_not_a_submitted_order():
    """A dislodged unit without a retreat order is disbanded, not submitted."""
    game = Game()
    game.clear_units()
    game.clear_centers()
    game.set_units('RUSSIA', ['F SPA/SC'])
    game.set_units('FRANCE', ['F GAS'])
    game.set_units('ENGLAND', ['F BRE', 'A PAR'])
    game.set_orders('RUSSIA', 'F SPA/SC - POR')
    game.set_orders('FRANCE', 'F GAS H')
    game.set_orders('ENGLAND', ['F BRE - GAS', 'A PAR S F BRE - GAS'])
    game.process()
    assert game.phase_type == 'R'
    retreaters = list(game.get_power('FRANCE').retreats)
    assert len(retreaters) == 1
    retreating_unit = retreaters[0]
    assert game.get_orders('FRANCE') == []

    phase = game.process()

    assert phase.orders['FRANCE'] == []
    assert game.order_history[phase.name]['FRANCE'] == []
    assert DISBAND in phase.results[retreating_unit]
    assert retreating_unit not in game.get_units('FRANCE')
