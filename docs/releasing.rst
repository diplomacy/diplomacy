Release checklist
=================

This is a maintainer checklist, not authorization to publish. Preparing version
1.2.0 must not create a release tag, push, or upload packages. Those actions require
separate explicit approval after the artifacts and validation report are reviewed.

Compatibility and prerequisites
-------------------------------

The runtime metadata still declares Python >=3.5 and retains the historical
classifiers. That is legacy policy, not evidence that Python 3.5 through 3.9 was
retested. The current validation target is Python 3.10 through 3.13. Record each
interpreter, platform, dependency set, command, result, and known limitation in
the release report before making a tested-compatibility claim.

Build-tool requirements are separate from the runtime metadata. Development,
documentation, and current publishing tools can require newer Python. Use Python
3.12 for release preparation; this does not establish an older runtime support floor.
The frontend requires Node.js >=22.13 and the checked-in npm lockfile.

Prepare and validate the source
-------------------------------

#. Confirm the intended branch and clean starting state. Preserve unrelated work.
#. Update ``diplomacy/version.py``, ``CHANGELOG.md``, and the README together.
   Check the version in built metadata, not just the source file.
#. In an isolated environment, install development dependencies and run checks::

       python -m venv /tmp/diplomacy-release-checks
       . /tmp/diplomacy-release-checks/bin/activate
       python -m pip install --upgrade pip
       python -m pip install -r requirements_dev.txt build twine
       python -m pytest diplomacy tests
       ./run_tests.sh

   ``run_tests.sh`` also runs pylint, documentation, frontend lint, Jest, and the
   production build when frontend dependencies are installed. It reports failure
   rather than hiding known lint debt. Install frontend dependencies first::

       cd diplomacy/web
       npm ci
       npm run lint
       npm test -- --runInBand
       npm run build
       cd ../..

   Repeat the Python suite on every claimed interpreter. Record pre-existing
   failures separately; a skipped frontend check is not a frontend pass.
#. Build documentation with current Sphinx, keeping output outside the source::

       sphinx-build -b html docs /tmp/diplomacy-release-docs

   Review warnings and errors. Existing API autodoc warnings must be recorded,
   not silently suppressed or mistaken for new release-page errors.

Build and inspect the distributions
-----------------------------------

Use a fresh output directory so stale distributions cannot be uploaded by mistake.
The default ``build`` command builds the wheel from the sdist, exercising both::

    python -m build --outdir /tmp/diplomacy-1.2.0-dist
    python -m twine check --strict /tmp/diplomacy-1.2.0-dist/*
    tar -tzf /tmp/diplomacy-1.2.0-dist/diplomacy-1.2.0.tar.gz
    python -m zipfile -l /tmp/diplomacy-1.2.0-dist/diplomacy-1.2.0-py3-none-any.whl

Inspect both archives before installation:

* Confirm name, version, ``Requires-Python``, dependencies, and rendered README.
* Confirm maps, SVGs, ``svg.dtd``, ``convoy_paths_cache.pkl``, and the required
  DAIDE/network fixtures are present in the installed package.
* Confirm the sdist contains the changelog, ``pyproject.toml``, release guide,
  top-level ``tests/test_packaging.py``, frontend sources/configuration, lockfile,
  and public assets. Frontend map imports must survive symlink flattening.
* Reject unexpected files, including private credentials, ``.env`` files,
  runtime data, dependency trees, caches, generated documentation, and frontend
  build output. Inspect filenames only; do not open credentials or home-directory
  authentication configuration.

Install the wheel into a fresh environment and test from outside the checkout so
source imports cannot mask missing package data::

    python -m venv /tmp/diplomacy-wheel-check
    /tmp/diplomacy-wheel-check/bin/python -m pip install /tmp/diplomacy-1.2.0-dist/diplomacy-1.2.0-py3-none-any.whl
    cd /tmp
    /tmp/diplomacy-wheel-check/bin/python -c "from diplomacy import Game; from diplomacy.version import PACKAGE_VERSION; assert PACKAGE_VERSION == '1.2.0'; assert '<svg' in Game().render()"

Also install the sdist into a separate fresh environment, verify imports and map
rendering there, and run the packaged Python regression suite outside the checkout.
The packaging regression intentionally lives outside the installed package: run it
from the extracted sdist with pytest and setuptools installed::

    mkdir /tmp/diplomacy-sdist-check
    tar -xzf /tmp/diplomacy-1.2.0-dist/diplomacy-1.2.0.tar.gz -C /tmp/diplomacy-sdist-check
    cd /tmp/diplomacy-sdist-check/diplomacy-1.2.0
    python -m pytest tests/test_packaging.py
    cd diplomacy/web
    npm ci
    npm test -- --runInBand
    npm run build

Use the release-check environment for the extracted-source commands. Verify the
production site's map assets and relative URLs as well as command exit codes.
Record checksums of the exact reviewed artifacts and retain their validation logs.

Approval and publishing credentials
-----------------------------------

Stop after preparation and artifact review. Obtain explicit approval for the
release commit, version tag, repository push, and package upload before taking
any of those actions. Recheck that PyPI does not already contain version 1.2.0.
Do not rebuild between approval and publishing without rechecking the artifacts.

For a future authorized upload, use a narrowly scoped PyPI API token supplied
through a secure local configuration or secret manager. This example contains
placeholders only; never commit a real token or inspect existing private config::

    [pypi]
    username = __token__
    password = <PYPI_API_TOKEN_PLACEHOLDER>

Do not place tokens in command-line arguments, repository files, or release logs.
Use ``python -m twine`` for any separately authorized upload, not obsolete
``setup.py upload``. No upload or tagging command is part of this preparation.
