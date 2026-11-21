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

from diplomacy.engine.game import Game
from diplomacy.utils import strings
from diplomacy.utils.export import from_saved_game_format, to_saved_game_format

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
