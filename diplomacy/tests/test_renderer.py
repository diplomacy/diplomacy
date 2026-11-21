# ==============================================================================
# Copyright (C) 2026 - Philip Paquette
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
"""Tests for the rendered order overlays."""
from pathlib import Path
from xml.dom import minidom

import pytest

from diplomacy import settings
from diplomacy.engine.game import Game
from diplomacy.engine.renderer import Renderer


def _in_layer(node, layer_id):
    """Returns True when node is inside the named SVG layer."""
    parent = node.parentNode
    while parent is not None:
        if parent.nodeName == 'g' and parent.getAttribute('id') == layer_id:
            return True
        parent = parent.parentNode
    return False


def _classes(node):
    """Returns the CSS classes attached to a node."""
    return node.getAttribute('class').split()


def _move_lines(svg):
    """Returns the movement order markers in the order layer."""
    dom = minidom.parseString(svg)
    return [node for node in dom.getElementsByTagName('line')
            if 'varwidthorder' in _classes(node) and _in_layer(node, 'OrderLayer')]


def _support_lines(svg):
    """Returns the support order markers in the order layer."""
    dom = minidom.parseString(svg)
    return [node for node in dom.getElementsByTagName('line')
            if 'supportorder' in _classes(node) and _in_layer(node, 'OrderLayer')]


def _highest_order_symbols(svg, symbol):
    """Returns build or disband symbols in the highest order layer."""
    dom = minidom.parseString(svg)
    return [node for node in dom.getElementsByTagName('use')
            if node.getAttribute('xlink:href') == '#{}'.format(symbol)
            and _in_layer(node, 'HighestOrderLayer')]


def _unit_ids(svg):
    """Returns the ids of units drawn in the unit layer."""
    dom = minidom.parseString(svg)
    return {node.getAttribute('id') for node in dom.getElementsByTagName('use')
            if _in_layer(node, 'UnitLayer')}


def _movement_game():
    """Builds a game where two powers each issue one move order."""
    game = Game()
    game.set_units('FRANCE', ['A PAR'])
    game.set_units('GERMANY', ['A MUN'])
    game.set_orders('FRANCE', ['A PAR - BUR'])
    game.set_orders('GERMANY', ['A MUN - BUR'])
    return game


def test_render_incl_orders_filters_movement_orders_by_issuing_power():
    """True draws all moves, a power name draws its own, and False draws none."""
    game = _movement_game()

    all_svg = game.render()
    french_svg = game.render(incl_orders='FRANCE')
    none_svg = game.render(incl_orders=False)

    assert len(_move_lines(all_svg)) == 2
    assert len(_move_lines(french_svg)) == 1
    assert len(_move_lines(none_svg)) == 0
    # Units remain visible for every power regardless of the order filter.
    assert {'unit_PAR', 'unit_MUN'} <= _unit_ids(french_svg)


def test_render_incl_orders_uses_support_issuer_across_powers():
    """A support order is selected by the power issuing it, not the supported power."""
    game = Game()
    game.set_units('FRANCE', ['A BUR'])
    game.set_units('GERMANY', ['A MUN'])
    game.set_orders('FRANCE', ['A BUR S A MUN'])

    assert len(_support_lines(game.render(incl_orders='FRANCE'))) == 1
    assert len(_support_lines(game.render(incl_orders='GERMANY'))) == 0
    assert len(_support_lines(game.render())) == 1


def test_render_incl_orders_filters_adjustment_builds_and_disbands():
    """Build and disband overlays follow the same issuing-power filter."""
    game = Game()
    game.set_current_phase('W1901A')
    game.get_power('FRANCE').adjust = ['A PAR B']
    game.get_power('GERMANY').adjust = ['A MUN D']

    all_svg = game.render()
    french_svg = game.render(incl_orders='france')
    german_svg = game.render(incl_orders='GERMANY')
    none_svg = game.render(incl_orders=False)

    assert len(_highest_order_symbols(all_svg, 'BuildUnit')) == 1
    assert len(_highest_order_symbols(all_svg, 'RemoveUnit')) == 1
    assert len(_highest_order_symbols(french_svg, 'BuildUnit')) == 1
    assert len(_highest_order_symbols(french_svg, 'RemoveUnit')) == 0
    assert len(_highest_order_symbols(german_svg, 'BuildUnit')) == 0
    assert len(_highest_order_symbols(german_svg, 'RemoveUnit')) == 1
    assert len(_highest_order_symbols(none_svg, 'BuildUnit')) == 0
    assert len(_highest_order_symbols(none_svg, 'RemoveUnit')) == 0


def test_render_incl_orders_keeps_bool_compatibility_and_reuses_renderer():
    """The renderer can alternate filters without leaking markers between renders."""
    game = _movement_game()
    renderer = Renderer(game)

    all_svg = renderer.render()
    filtered_svg = renderer.render(incl_orders='FRANCE')
    none_svg = renderer.render(incl_orders=False)
    all_again_svg = renderer.render()

    assert all_svg == all_again_svg
    assert len(_move_lines(all_svg)) == 2
    assert len(_move_lines(filtered_svg)) == 1
    assert len(_move_lines(none_svg)) == 0
    assert renderer.render(incl_orders='france') == filtered_svg
    with pytest.raises(ValueError):
        renderer.render(incl_orders='UNKNOWN')


@pytest.mark.parametrize('map_name,power,color', [
    ('standard', 'FRANCE', 'royalblue'),
    ('modern', 'EGYPT', '#808000'),
    ('ancmed', 'ROME', '#c48f85'),
    ('pure', 'FRANCE', '#8E85B7'),
    ('standard_age_of_empires', 'FRANCE', 'royalblue'),
])
def test_get_power_color_uses_map_metadata(map_name, power, color):
    """Both accessors preserve each SVG palette and root-map fallback."""
    game = Game(map_name=map_name)
    assert game.get_power_color(power.lower()) == color
    assert game.renderer.get_power_color(power) == color


def test_get_power_color_reuses_custom_renderer(tmp_path):
    """A custom palette is retained, including missing metadata without inference."""
    game = Game()
    custom_svg = tmp_path / 'custom.svg'
    source_svg = Path(settings.PACKAGE_DIR) / 'maps' / 'svg' / 'standard.svg'
    custom_svg.write_text(source_svg.read_text().replace('color="royalblue"', 'color="#123456"'))
    game.renderer = Renderer(game, svg_path=str(custom_svg))
    renderer = game.renderer
    assert game.get_power_color('france') == '#123456'
    assert game.renderer is renderer
    del renderer.metadata['color']['FRANCE']
    assert game.get_power_color('FRANCE') is None
    with pytest.raises(ValueError):
        game.get_power_color('UNKNOWN')


def test_get_power_color_without_svg():
    """Unavailable SVG data yields None only for a valid power."""
    game = Game(map_name='colonial')
    assert game.get_power_color('britain') is None
    with pytest.raises(ValueError):
        game.get_power_color('UNKNOWN')


def test_render_validates_power_without_svg():
    """Missing rendering data does not bypass power-name validation."""
    game = Game(map_name='colonial')
    assert game.render(incl_orders='BRITAIN') is None
    with pytest.raises(ValueError):
        game.render(incl_orders='UNKNOWN')
