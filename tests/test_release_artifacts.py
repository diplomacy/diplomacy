"""Focused safety checks for the release archive inspector."""
import importlib.util
import io
import os
from pathlib import Path
import stat
import tarfile
import zipfile

import pytest


SPEC = importlib.util.spec_from_file_location(
    'check_release_artifacts', Path(__file__).resolve().parents[1] / 'tools/check_release_artifacts.py')
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
VERSION = CHECKER.read_version(
    (Path(__file__).resolve().parents[1] / 'diplomacy/version.py').read_bytes())


def make_archive(tmp_path, kind, name, symlink=False):
    """Produce a single member, without ever extracting its unsafe name."""
    path = tmp_path / ('test.whl' if kind == 'wheel' else 'test.tar.gz')
    if kind == 'wheel':
        with zipfile.ZipFile(path, 'w') as archive:
            entry = zipfile.ZipInfo(name)
            entry.external_attr = (stat.S_IFLNK if symlink else stat.S_IFREG) << 16
            archive.writestr(entry, b'target')
    else:
        with tarfile.open(path, 'w:gz') as archive:
            entry = tarfile.TarInfo(f'diplomacy-{VERSION}/' + name)
            if symlink:
                entry.type = tarfile.SYMTYPE
                entry.linkname = 'target'
                archive.addfile(entry)
            else:
                entry.size = 6
                archive.addfile(entry, io.BytesIO(b'target'))
    return path


@pytest.mark.parametrize('kind', ['wheel', 'sdist'])
@pytest.mark.parametrize('name', ['../escape.py', '/absolute.py', 'nested/../../escape.py',
                                 'nested\\escape.py'])
def test_rejects_unsafe_archive_paths(tmp_path, kind, name):
    with pytest.raises(ValueError, match='unsafe archive path'):
        CHECKER.archive_files(make_archive(tmp_path, kind, name), VERSION)


@pytest.mark.parametrize('kind', ['wheel', 'sdist'])
@pytest.mark.parametrize('name', ['diplomacy/.env.local', 'nested/credentials-prod/key',
                                 'nested/node_modules/package/index.js', 'nested/data/game.json',
                                 'nested/.cache/file', 'nested/build/index.js'])
def test_rejects_forbidden_assets(tmp_path, kind, name):
    with pytest.raises(ValueError, match='forbidden asset'):
        CHECKER.archive_files(make_archive(tmp_path, kind, name), VERSION)


@pytest.mark.parametrize('kind', ['wheel', 'sdist'])
def test_rejects_archive_symlinks(tmp_path, kind):
    with pytest.raises(ValueError, match='non-regular'):
        CHECKER.archive_files(make_archive(tmp_path, kind, 'link', symlink=True), VERSION)


def test_rejects_missing_required_asset(tmp_path):
    make_archive(tmp_path, 'wheel', 'placeholder').rename(
        tmp_path / f'diplomacy-{VERSION}-py3-none-any.whl')
    make_archive(tmp_path, 'sdist', 'placeholder').rename(
        tmp_path / f'diplomacy-{VERSION}.tar.gz')
    with pytest.raises(ValueError, match='missing required assets:.*diplomacy/maps/standard.map'):
        CHECKER.check_dist(tmp_path, VERSION)


@pytest.mark.parametrize('wheel, asset', [
    (True, 'diplomacy/maps/svg/ancmed.svg'),
    (False, 'diplomacy/web/src/diplomacy/maps/svg/ancmed.svg'),
])
def test_rejects_missing_nonstandard_map(monkeypatch, wheel, asset):
    dist = os.environ.get('RELEASE_DIST')
    if not dist:
        pytest.skip('set RELEASE_DIST to validate freshly built release artifacts')
    original = CHECKER.archive_files

    def without_map(path, version):
        files = original(path, version)
        if (path.suffix == '.whl') == wheel:
            del files[asset]
        return files

    monkeypatch.setattr(CHECKER, 'archive_files', without_map)
    with pytest.raises(ValueError, match='missing required assets:.*' + asset):
        CHECKER.check_dist(Path(dist), VERSION)


def test_accepts_real_release_artifacts():
    """The release workflow supplies its freshly built wheel and sdist here."""
    dist = os.environ.get('RELEASE_DIST')
    if not dist:
        pytest.skip('set RELEASE_DIST to validate freshly built release artifacts')
    assert len(CHECKER.check_dist(Path(dist), VERSION)) == 2
