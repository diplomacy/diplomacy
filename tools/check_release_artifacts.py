"""Inspect release archives without extracting or executing their contents (stdlib only)."""
import argparse
import ast
from email.parser import BytesParser
from pathlib import Path
import re
import stat
import tarfile
import zipfile


PACKAGE_ASSETS = {
    'diplomacy/__init__.py', 'diplomacy/version.py',
    'diplomacy/README_COMMANDS.txt', 'diplomacy/README_MAPS.txt', 'diplomacy/README_RULES.txt',
    'diplomacy/maps/standard.map', 'diplomacy/maps/convoy_paths_cache.pkl',
    'diplomacy/maps/svg/standard.svg', 'diplomacy/maps/svg/svg.dtd',
    'diplomacy/daide/tests/game_data_1.csv',
    'diplomacy/daide/tests/game_data_1_history.csv',
    'diplomacy/daide/tests/game_data_1_reject_map.csv',
    'diplomacy/daide/tests/game_data_7.csv',
    'diplomacy/daide/tests/game_data_7_draw.csv',
    'diplomacy/daide/tests/game_data_7_press.csv',
    'diplomacy/tests/network/1.json', 'diplomacy/tests/network/2.json',
    'diplomacy/tests/network/3.json',
}
SOURCE_ASSETS = {
    'README.md', 'LICENSE', 'CHANGELOG.md', 'MANIFEST.in', 'pyproject.toml', 'setup.py',
    'requirements.txt', 'requirements_dev.txt',
    'tools/check_release_artifacts.py', 'tests/test_packaging.py', 'tests/test_release_artifacts.py',
    'docs/conf.py', 'docs/releasing.rst',
    'diplomacy/web/package.json', 'diplomacy/web/package-lock.json',
    'diplomacy/web/.eslintrc', 'diplomacy/web/vite.config.mjs',
    'diplomacy/web/babel.config.cjs', 'diplomacy/web/jest.config.cjs',
    'diplomacy/web/index.html', 'diplomacy/web/test/assetMock.cjs',
    'diplomacy/web/public/manifest.json', 'diplomacy/web/public/favicon.ico',
    'diplomacy/web/src/index.js', 'diplomacy/web/src/diplomacy/maps/standard.map',
    'diplomacy/web/src/diplomacy/maps/svg/standard.svg',
}
FORBIDDEN = {
    '.git', '.venv', 'venv', '.tox', 'node_modules', '__pycache__',
    '.cache', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'build', '_build', 'dist', 'data',
}
DEPENDENCIES = {'bcrypt', 'coloredlogs', 'python-dateutil', 'pytz', 'tornado>=5.0', 'tqdm', 'ujson'}


def read_version(source):
    """Read a single literal assignment, never importing version.py."""
    tree = ast.parse(source)
    assignments = [node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'PACKAGE_VERSION'
                           for target in node.targets)]
    if len(assignments) != 1:
        raise ValueError('expected one PACKAGE_VERSION assignment')
    version = ast.literal_eval(assignments[0])
    if not isinstance(version, str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('expected a stable three-component version')
    return version


def check_path(name):
    """Reject unsafe names and private/generated assets, at every nesting depth."""
    parts = name.rstrip('/').split('/')
    if (not name or any(part in {'', '.', '..'} for part in parts) or '\\' in name or ':' in name
            or any(ord(char) < 32 or ord(char) == 127 for char in name)):
        raise ValueError('unsafe archive path: ' + name)
    for part in parts:
        lower = part.lower()
        if (lower in FORBIDDEN or lower == '.env' or lower.startswith(('.env.', 'credentials'))
                or lower.endswith(('.pyc', '.pyo'))):
            raise ValueError('forbidden asset: ' + name)


def archive_files(path, version):
    """Return regular-file contents, rejecting links and duplicate names first."""
    files = {}
    seen = set()

    def add(name, is_directory, read):
        check_path(name)
        normalized = name.rstrip('/')
        if normalized in seen:
            raise ValueError('duplicate archive path: ' + name)
        seen.add(normalized)
        if not is_directory:
            files[normalized] = read()

    if path.suffix == '.whl':
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                mode = stat.S_IFMT(entry.external_attr >> 16)
                if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ValueError('non-regular wheel member: ' + entry.filename)
                add(entry.filename, entry.is_dir(), lambda: archive.read(entry))
    else:
        root = 'diplomacy-' + version
        with tarfile.open(path, 'r:gz') as archive:
            for entry in archive:
                check_path(entry.name)
                if not (entry.isdir() or entry.isfile()):
                    raise ValueError('non-regular sdist member: ' + entry.name)
                if entry.name == root and entry.isdir():
                    continue
                if not entry.name.startswith(root + '/'):
                    raise ValueError('unexpected sdist root: ' + entry.name)
                add(entry.name[len(root) + 1:], entry.isdir(),
                    lambda: archive.extractfile(entry).read())
    return files


def check_metadata(data, version):
    """Check the release identity and the existing runtime metadata contract."""
    metadata = BytesParser().parsebytes(data)
    expected = {'Name': 'diplomacy', 'Version': version, 'Requires-Python': '>=3.5',
                'Description-Content-Type': 'text/markdown'}
    for key, value in expected.items():
        if metadata.get_all(key) != [value]:
            raise ValueError('unexpected metadata ' + key)
    requirements = metadata.get_all('Requires-Dist', [])
    if {re.sub(r'\s+', '', item).lower() for item in requirements} != DEPENDENCIES:
        raise ValueError('unexpected runtime dependencies')


def map_assets():
    """Read the complete map inventory from the clean source tree, without imports."""
    root = Path(__file__).resolve().parents[1]
    paths = list((root / 'diplomacy/maps').glob('*.map'))
    paths += list((root / 'diplomacy/maps/svg').glob('*.svg'))
    paths.append(root / 'diplomacy/maps/svg/svg.dtd')
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in paths}


def check_dist(dist, version):
    """Validate exactly one universal wheel and one sdist, with no stale extras."""
    names = [f'diplomacy-{version}-py3-none-any.whl', f'diplomacy-{version}.tar.gz']
    if {entry.name for entry in dist.iterdir()} != set(names):
        raise ValueError('dist must contain only: ' + ', '.join(names))
    for name in names:
        path = dist / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('distribution must be a regular file: ' + name)
        wheel = name.endswith('.whl')
        files = archive_files(path, version)
        expected_maps = map_assets()
        if not wheel:
            expected_maps.update({name.replace('diplomacy/maps/', 'diplomacy/web/src/diplomacy/maps/', 1): data
                                  for name, data in list(expected_maps.items())})
        required = PACKAGE_ASSETS | expected_maps.keys() | (set() if wheel else SOURCE_ASSETS)
        metadata_path = f'diplomacy-{version}.dist-info/METADATA' if wheel else 'PKG-INFO'
        required = required | {metadata_path}
        if wheel:
            required.add(f'diplomacy-{version}.dist-info/WHEEL')
        missing = required - files.keys()
        if missing:
            raise ValueError('missing required assets: ' + ', '.join(sorted(missing)))
        for asset, expected in expected_maps.items():
            if files[asset] != expected:
                raise ValueError('map asset differs from source: ' + asset)
        if read_version(files['diplomacy/version.py']) != version:
            raise ValueError('archive version does not match release')
        check_metadata(files[metadata_path], version)
        if wheel:
            metadata = BytesParser().parsebytes(files[f'diplomacy-{version}.dist-info/WHEEL'])
            if metadata.get_all('Tag') != ['py3-none-any'] or metadata['Root-Is-Purelib'] != 'true':
                raise ValueError('expected a pure Python universal wheel')
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dist', type=Path)
    parser.add_argument('--version-file', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'diplomacy/version.py')
    args = parser.parse_args()
    version = read_version(args.version_file.read_bytes())
    try:
        names = check_dist(args.dist, version)
    except (ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        parser.exit(1, str(exc) + '\n')
    print('Validated: ' + ', '.join(names))


if __name__ == '__main__':
    main()
