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
""" Tests for diplomacy.utils.convoy_paths. """
import pickle
from queue import Queue

import pytest

from diplomacy.utils import convoy_paths

PORT_CACHE_SUFFIX = ':port-convoys-v1'

class _FakeMap:
    """ Minimal map object exposing the interface used by _get_convoy_paths. """
    def __init__(self, loc_types, abuts):
        self.name = 'fake'
        self.locs = list(loc_types)
        self._loc_types = loc_types
        self._abuts = abuts

    def area_type(self, loc):
        """ Returns the terrain type of a location. """
        return self._loc_types[loc.upper()]

    def abut_list(self, loc, incl_no_coast=False):      # pylint: disable=unused-argument
        """ Returns the locations adjacent to a location. """
        return self._abuts.get(loc.upper(), [])

def _convoy_paths_by_destination(max_convoy_length):
    """ Runs the convoy path generator on a small graph where POR is a port. """
    loc_types = {
        'LON': 'COAST', 'NTH': 'WATER', 'POR': 'PORT',
        'BAL': 'WATER', 'DEN': 'COAST', 'ECH': 'WATER', 'BEL': 'COAST',
    }
    abuts = {
        'LON': ['NTH'],
        'NTH': ['LON', 'POR', 'ECH'],
        'POR': ['NTH', 'BAL'],
        'BAL': ['POR', 'DEN'],
        'DEN': ['BAL'],
        'ECH': ['NTH', 'BEL'],
        'BEL': ['ECH'],
    }
    results = convoy_paths._get_convoy_paths(_FakeMap(loc_types, abuts), 'LON', max_convoy_length, Queue())
    paths = {}
    for _, fleets, destinations in results:
        for destination in destinations:
            paths.setdefault(destination, set()).add(frozenset(fleets))
    return paths

@pytest.mark.parametrize('max_convoy_length, den_path', [
    (13, frozenset({'NTH', 'POR', 'BAL'})),
    (2, None),
])
def test_get_convoy_paths_uses_ports_as_destination_and_transit(max_convoy_length, den_path):
    """ Tests that a port can be a convoy destination and a transit location. """
    paths = _convoy_paths_by_destination(max_convoy_length)
    assert frozenset({'NTH'}) in paths['POR']
    if den_path is None:
        assert 'DEN' not in paths
    else:
        assert den_path in paths['DEN']

def _write_cache(path, entries):
    """ Writes a convoy paths cache file. """
    data = {'__version__': convoy_paths.__VERSION__}
    data.update(entries)
    with open(path, 'wb') as cache_file:
        pickle.dump(data, cache_file)

def _read_cache(path):
    """ Reads a convoy paths cache file. """
    with open(path, 'rb') as cache_file:
        return pickle.load(cache_file)

@pytest.fixture
def cache_env(tmp_path, monkeypatch):
    """ Creates temporary maps and stale internal/external convoy caches. """
    maps_dir = tmp_path / 'maps'
    maps_dir.mkdir()
    port_map = maps_dir / 'port_map.map'
    port_map.write_text('port P1 ABUTS P2\nCOAST C1 ABUTS P1\n', encoding='utf-8')
    inherited_map = maps_dir / 'inherited.map'
    inherited_map.write_text('USE missing_map\nMAP port_map\n', encoding='utf-8')
    standard_map = maps_dir / 'standard.map'
    standard_map.write_text('# PORT ignored\nCOAST C1 ABUTS C2\n', encoding='utf-8')

    port_hash = convoy_paths.get_file_md5(str(port_map))
    inherited_hash = convoy_paths.get_file_md5(str(inherited_map))
    standard_hash = convoy_paths.get_file_md5(str(standard_map))

    internal_cache = tmp_path / 'internal_cache.pkl'
    external_cache = tmp_path / 'external_cache.pkl'
    _write_cache(internal_cache, {
        port_hash: 'stale-internal-port',
        inherited_hash: 'stale-internal-inherited',
        standard_hash: 'standard-buckets',
    })
    _write_cache(external_cache, {
        port_hash: 'stale-external-port',
        inherited_hash: 'stale-external-inherited',
        standard_hash: 'standard-buckets',
        'unrelated-external': 'external-sentinel',
    })

    monkeypatch.setattr(convoy_paths.settings, 'PACKAGE_DIR', str(tmp_path))
    monkeypatch.setattr(convoy_paths, 'INTERNAL_CACHE_PATH', str(internal_cache))
    monkeypatch.setattr(convoy_paths, 'EXTERNAL_CACHE_PATH', str(external_cache))
    return {
        'port_map': str(port_map),
        'inherited_map': str(inherited_map),
        'standard_map': str(standard_map),
        'port_hash': port_hash,
        'inherited_hash': inherited_hash,
        'standard_hash': standard_hash,
        'external_cache': external_cache,
    }

def test_get_convoy_paths_cache_rejects_stale_port_entries(cache_env):
    """ Tests that raw MD5 entries for PORT maps are ignored when loading the cache. """
    cache = convoy_paths.get_convoy_paths_cache()
    assert 'port_map' not in cache
    assert 'inherited' not in cache
    assert cache['standard'] == 'standard-buckets'
    stale_values = {'stale-internal-port', 'stale-external-port',
                    'stale-internal-inherited', 'stale-external-inherited'}
    assert stale_values.isdisjoint(cache.values())

@pytest.mark.parametrize('map_key, hash_key, cache_name', [
    ('port_map', 'port_hash', 'port_map'),
    ('inherited_map', 'inherited_hash', 'inherited'),
])
def test_add_to_cache_regenerates_port_entry_once(cache_env, monkeypatch, map_key, hash_key, cache_name):
    """ Tests that PORT entries are regenerated once under a suffixed key and reused. """
    build_calls = []

    def fake_build(map_object, max_convoy_length):      # pylint: disable=unused-argument
        build_calls.append(max_convoy_length)
        return {'buckets': len(build_calls)}

    monkeypatch.setattr(convoy_paths, 'Map', lambda *args, **kwargs: None)
    monkeypatch.setattr(convoy_paths, '_build_convoy_paths_cache', fake_build)

    assert convoy_paths.add_to_cache(cache_env[map_key]) == {'buckets': 1}
    assert build_calls == [convoy_paths.MAX_CONVOY_LENGTH]
    assert convoy_paths.add_to_cache(cache_env[map_key]) == {'buckets': 1}
    assert build_calls == [convoy_paths.MAX_CONVOY_LENGTH]
    assert convoy_paths.get_convoy_paths_cache()[cache_name] == {'buckets': 1}

    assert convoy_paths.add_to_cache(cache_env['standard_map']) == 'standard-buckets'
    assert build_calls == [convoy_paths.MAX_CONVOY_LENGTH]

    external_cache = _read_cache(cache_env['external_cache'])
    assert external_cache[cache_env[hash_key] + PORT_CACHE_SUFFIX] == {'buckets': 1}
    assert external_cache[cache_env['standard_hash']] == 'standard-buckets'
    assert external_cache['unrelated-external'] == 'external-sentinel'
