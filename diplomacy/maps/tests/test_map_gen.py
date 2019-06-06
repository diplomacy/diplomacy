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
""" Test Map Generation
    - Contains test for map generation
"""
import glob
import os
import sys

from diplomacy.engine.map import Map

MODULE_PATH = sys.modules['diplomacy'].__path__[0]

def test_map_creation():
    """ Tests for map creation """
    maps = glob.glob(os.path.join(MODULE_PATH, 'maps', '*.map'))
    assert maps, 'Expected maps to be found.'
    for current_map in maps:
        map_name = current_map[current_map.rfind('/') + 1:].replace('.map', '')
        this_map = Map(map_name)
        assert this_map.error == [], 'Map %s should have no errors' % map_name
        del this_map
