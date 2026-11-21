# ==============================================================================
# Copyright (C) 2026 - Philip Paquette, Steven Bocco
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
""" Tests for diplomacy.utils.export. """
import ujson as json
import pytest

from diplomacy.engine.game import Game
from diplomacy.utils import strings
from diplomacy.utils.export import (from_saved_game_format, normalize_saved_game_influence,
                                   to_saved_game_format)

def test_export_import_completed_game():
    """ Tests that a completed game keeps status and outcome through a JSON roundtrip. """
    game = Game(game_id='completed_game')
    game.draw()
    assert game.status == strings.COMPLETED
    assert game.outcome

    saved_game = to_saved_game_format(game)
    assert saved_game['status'] == strings.COMPLETED

    restored = from_saved_game_format(json.loads(json.dumps(saved_game)))
    assert restored.phase == 'COMPLETED'
    assert restored.status == strings.COMPLETED
    assert restored.outcome == game.outcome

def test_export_import_non_completed_status():
    """ Tests that an active game status is restored through a JSON roundtrip. """
    game = Game(game_id='active_game')
    game.set_status(strings.ACTIVE)

    saved_game = to_saved_game_format(game)
    restored = from_saved_game_format(json.loads(json.dumps(saved_game)))
    assert restored.status == strings.ACTIVE
    assert restored.outcome == []

def test_import_legacy_completed_game_without_status_and_outcome():
    """ Tests that a completed saved game without status and outcome keeps the default values. """
    game = Game(game_id='legacy_completed_game')
    game.draw()
    saved_game = to_saved_game_format(game)
    saved_game.pop('status')
    saved_game.pop('outcome')

    restored = from_saved_game_format(json.loads(json.dumps(saved_game)))
    assert restored.phase == 'COMPLETED'
    assert restored.status == strings.FORMING
    assert restored.outcome == []

def _phase(name, influence, units):
    return {'name': name,
            'state': {'name': name, 'influence': influence, 'units': units},
            'orders': {}, 'results': {}, 'messages': {}}

def _saved_game(*phases):
    return {'id': 'legacy_game', 'map': 'standard', 'rules': [], 'status': 'active',
            'custom': {'keep': ['metadata']}, 'phases': list(phases)}

def test_normalize_saved_game_influence_canonicalizes_same_power_duplicates():
    """ Historical and current phases canonicalize same-power alias duplicates. """
    saved_game = _saved_game(
        _phase('S1901M', {'RUSSIA': ['STP', 'STP/NC', 'SPA/SC', 'SPA', 'STP/XX'], 'TURKEY': ['ANK']},
               {'RUSSIA': ['F STP/NC', 'F SPA/SC'], 'TURKEY': ['F ANK']}),
        _phase('F1901M', {'RUSSIA': ['SPA', 'SPA/SC']}, {'RUSSIA': ['F SPA/SC']}))
    original = json.loads(json.dumps(saved_game))

    normalized = normalize_saved_game_influence(saved_game)

    assert normalized is not saved_game
    assert saved_game == original
    assert normalized['custom'] == {'keep': ['metadata']}
    assert normalized['phases'][0]['state']['influence'] == {'RUSSIA': ['STP', 'SPA', 'STP/XX'], 'TURKEY': ['ANK']}
    assert normalized['phases'][1]['state']['influence'] == {'RUSSIA': ['SPA']}

def test_normalize_saved_game_influence_uses_cross_power_unique_occupant():
    """ A unique non-dislodged occupant resolves cross-power claims; unaffected claims stay. """
    saved_game = _saved_game(
        _phase('S1901M', {'FRANCE': ['SPA/SC'], 'ITALY': ['SPA'], 'GERMANY': ['POR']},
               {'FRANCE': ['F SPA/SC']}))

    normalized = normalize_saved_game_influence(saved_game)

    assert normalized['phases'][0]['state']['influence'] == {
        'FRANCE': ['SPA'], 'ITALY': [], 'GERMANY': ['POR']}

@pytest.mark.parametrize('influence,occupants', [
    ({'FRANCE': ['SPA/SC'], 'ITALY': ['SPA']}, {}),
    ({'FRANCE': ['SPA/SC'], 'ITALY': ['SPA']}, {'FRANCE': ['A SPA'], 'ITALY': ['A SPA']}),
    ({'FRANCE': ['SPA/SC']}, {'ITALY': ['A SPA']}),
])
def test_normalize_saved_game_influence_refuses_ambiguous_province(influence, occupants):
    """ No occupant, multiple occupants and a sole nonclaimant are ambiguous. """
    saved_game = _saved_game(_phase('S1901M', influence, occupants))
    original = json.loads(json.dumps(saved_game))

    with pytest.raises(ValueError, match='province SPA in phase S1901M'):
        normalize_saved_game_influence(saved_game)

    assert saved_game == original

def test_normalize_saved_game_influence_ignores_dislodged_occupant():
    """ A dislodged unit is not an occupant, so the sole claimant wins. """
    saved_game = _saved_game(
        _phase('S1901M', {'ITALY': ['SPA/SC']}, {'FRANCE': ['*A SPA']}))

    normalized = normalize_saved_game_influence(saved_game)

    assert normalized['phases'][0]['state']['influence'] == {'ITALY': ['SPA']}
