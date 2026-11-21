"""Regression coverage for the source distribution asset allowlist."""
from pathlib import Path

from setuptools.command.egg_info import FileList


def test_manifest_selects_only_source_assets(tmp_path, monkeypatch):
    """Apply the real manifest in an isolated synthetic source tree."""
    manifest = (Path(__file__).resolve().parents[1] / 'MANIFEST.in').read_text()
    required = {
        'ACKNOWLEDGEMENTS',
        'CODE_OF_CONDUCT.md',
        'LICENSE',
        'README.md',
        'requirements.txt',
        'requirements_dev.txt',
        'run_install_nvm.sh',
        'run_tests.sh',
        'tests/test_packaging.py',
        'diplomacy/README_COMMANDS.txt',
        'diplomacy/README_MAPS.txt',
        'diplomacy/README_RULES.txt',
        'diplomacy/maps/standard.map',
        'diplomacy/maps/variants/example.map',
        'diplomacy/maps/convoy_paths_cache.pkl',
        'diplomacy/maps/svg/standard.svg',
        'diplomacy/maps/svg/svg.dtd',
        'diplomacy/daide/tests/game_data_1.csv',
        'diplomacy/daide/tests/game_data_1_history.csv',
        'diplomacy/daide/tests/game_data_1_reject_map.csv',
        'diplomacy/daide/tests/game_data_7.csv',
        'diplomacy/daide/tests/game_data_7_draw.csv',
        'diplomacy/daide/tests/game_data_7_press.csv',
        'diplomacy/tests/network/1.json',
        'diplomacy/tests/network/2.json',
        'diplomacy/tests/network/3.json',
        'diplomacy/web/src/index.js',
        'diplomacy/web/src/gui/page.jsx',
        'diplomacy/web/src/gui/page.test.jsx',
        'diplomacy/web/src/gui/style.css',
        'diplomacy/web/src/gui/icon.svg',
        # An sdist can flatten the maps symlink into ordinary files.
        'diplomacy/web/src/diplomacy/maps/standard.map',
        'diplomacy/web/src/diplomacy/maps/svg/standard.svg',
        'diplomacy/web/package.json',
        'diplomacy/web/package-lock.json',
        'diplomacy/web/.eslintrc',
        'diplomacy/web/vite.config.mjs',
        'diplomacy/web/babel.config.cjs',
        'diplomacy/web/jest.config.cjs',
        'diplomacy/web/index.html',
        'diplomacy/web/test/assetMock.cjs',
        'diplomacy/web/public/manifest.json',
        'diplomacy/web/public/favicon.ico',
        'docs/conf.py',
        'docs/Makefile',
        'docs/api/example.rst',
        'docs/_static/theme.css',
        'docs/images/map.png',
    }
    unwanted = {
        'diplomacy/__pycache__/engine.cpython-310.pyc',
        'diplomacy/.pytest_cache/v/cache/nodeids',
        'diplomacy/.cache/session.json',
        'diplomacy/data/server.json',
        'diplomacy/data/games/private.json',
        'diplomacy/.env',
        'diplomacy/.env.local',
        'diplomacy/credentials.json',
        'diplomacy/maps/private.pkl',
        'diplomacy/maps/private.json',
        'diplomacy/maps/svg/private.dtd',
        'diplomacy/daide/private.csv',
        'diplomacy/tests/private.json',
        'diplomacy/web/node_modules/dependency/index.js',
        'diplomacy/web/node_modules/dependency/package.json',
        'diplomacy/web/build/assets/index.js',
        'diplomacy/web/build/manifest.json',
        'diplomacy/web/private.json',
        'diplomacy/web/private.config.cjs',
        'diplomacy/web/test/private.cjs',
        'diplomacy/web/public/private.json',
        'diplomacy/web/public/private.svg',
        'diplomacy/web/src/private.json',
        'diplomacy/web/src/private.pkl',
        'diplomacy/web/src/.env.local',
        'diplomacy/web/src/credentials.js',
        'diplomacy/web/src/diplomacy/maps/private.pkl',
        'diplomacy/daide/tests/private.csv',
        'diplomacy/tests/network/private.json',
        'diplomacy/web/src/node_modules/dependency/index.js',
        'diplomacy/web/src/nested/node_modules/dependency/deep/index.js',
        'diplomacy/web/src/__pycache__/deep/index.js',
        'diplomacy/web/src/.cache/deep/index.js',
        'diplomacy/web/src/.pytest_cache/deep/index.jsx',
        'diplomacy/web/src/build/deep/index.css',
        'diplomacy/web/src/data/deep/index.svg',
        'diplomacy/web/src/credentials/deep/index.js',
        'diplomacy/maps/nested/data/private.map',
        'diplomacy/maps/svg/nested/.cache/private.svg',
        'docs/_static/nested/build/private.css',
        'docs/images/nested/credentials/private.png',
        'docs/images/nested/credentials-prod/deep/private.png',
        'docs/_build/html/index.html',
        'docs/_build/generated.rst',
        'docs/_build/_static/theme.css',
    }
    # Real FileList globbing must never inspect the repository or live credentials.
    for name in required | unwanted:
        sentinel = tmp_path / name
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.touch()
    monkeypatch.chdir(tmp_path)
    file_list = FileList()
    for line in manifest.splitlines():
        command = line.split('#', 1)[0].strip()
        if command:
            file_list.process_template_line(command)
    selected = {Path(name).as_posix() for name in file_list.files}
    assert not selected & unwanted
    assert required <= selected
