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
""" Tests for the server startup script and the server directory handling. """
import os
import runpy
import sys

import pytest

import diplomacy
from diplomacy import Server
from diplomacy.utils import constants, exceptions


@pytest.fixture
def server_cache(monkeypatch):
    """ Isolate Server's instance cache and restore it after the test. """
    cache = {}
    monkeypatch.setattr(Server, '__cache__', cache)
    return cache


def run_server_script(monkeypatch, argv):
    """ Run diplomacy.server.run as __main__ with a fake Server and return recorded calls. """
    calls = []

    class FakeServer:
        """ Fake server recording constructor and start calls. """
        def __init__(self, **kwargs):
            calls.append(('init', kwargs))

        def start(self, **kwargs):
            calls.append(('start', kwargs))

    monkeypatch.setattr(diplomacy, 'Server', FakeServer)
    monkeypatch.setattr(sys, 'argv', ['diplomacy.server.run'] + argv)
    runpy.run_module('diplomacy.server.run', run_name='__main__')
    return calls


@pytest.mark.parametrize(
    'option, port_args, expected_port',
    [
        (None, [], constants.DEFAULT_PORT),
        ('-s', ['-p', '9123'], 9123),
        ('--server_dir', [], constants.DEFAULT_PORT),
    ],
)
def test_run_forwards_server_dir_and_port(monkeypatch, tmp_path, option, port_args, expected_port):
    """ Run with default values and with each server directory alias. """
    server_dir = str(tmp_path / 'server')
    argv = [] if option is None else [option, server_dir]
    expected_server_dir = None if option is None else server_dir
    assert run_server_script(monkeypatch, argv + port_args) == [
        ('init', {'server_dir': expected_server_dir}),
        ('start', {'port': expected_port}),
    ]


def test_server_creates_data_under_missing_server_dir(tmp_path, server_cache):
    """ Create a missing server directory and reuse the cached server. """
    server_dir = tmp_path / 'missing' / 'nested' / 'server'
    server = Server(server_dir=str(server_dir))
    assert server_dir.is_dir()
    assert server.data_path == str(server_dir / 'data')
    assert server.games_path == str(server_dir / 'data' / 'games')
    assert os.path.isdir(server.data_path)
    assert os.path.isdir(server.games_path)
    assert (server_dir / 'data' / 'server.json').is_file()
    assert Server(server_dir=str(server_dir)) is server
    assert len(server_cache) == 1


def test_server_reloads_config_after_cache_reset(tmp_path, server_cache):
    """ Reload persisted configuration after clearing the server cache. """
    server_dir = tmp_path / 'server'
    server_dir.mkdir()
    server = Server(server_dir=str(server_dir), max_games=3)
    server.backup_now(force=True)
    server_cache.clear()
    reloaded = Server(server_dir=str(server_dir))
    assert reloaded is not server
    assert reloaded.max_games == 3


def test_server_rejects_existing_file_as_server_dir(tmp_path, server_cache):
    """ Reject an existing server directory path that is not a directory. """
    server_dir = tmp_path / 'server'
    server_dir.write_text('not a directory')
    with pytest.raises(exceptions.ServerDirException):
        Server(server_dir=str(server_dir))
