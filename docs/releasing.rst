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
#. Build documentation with Sphinx 9, keeping output outside the source::

       python -m pip install 'sphinx>=9,<10' sphinx_copybutton sphinx_rtd_theme
       python -m sphinx -W --keep-going -b html docs /tmp/diplomacy-release-docs

   Warnings fail release validation. Record and resolve failures rather than
   silently suppressing them or treating a non-strict build as a strict pass.

Build and inspect the distributions
-----------------------------------

Use a fresh output directory so stale distributions cannot be uploaded by mistake.
The default ``build`` command builds the wheel from the sdist, exercising both::

    python -m build --outdir /tmp/diplomacy-1.2.0-dist
    python tools/check_release_artifacts.py /tmp/diplomacy-1.2.0-dist
    RELEASE_DIST=/tmp/diplomacy-1.2.0-dist python -m pytest tests/test_release_artifacts.py
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

Trusted Publishing setup (external, not performed here)
-------------------------------------------------------

The approved authentication path is PyPI Trusted Publishing through GitHub
Actions OIDC, not an API token. No ``.pypirc``, password, repository secret, or
local publishing credential is needed. Do not inspect existing private
configuration or put credentials in commands, files, or logs.

An authorized PyPI project owner must configure a GitHub Trusted Publisher for
the existing ``diplomacy`` project with these exact fields:

* Owner: ``diplomacy``
* Repository name: ``diplomacy``
* Workflow filename: ``release.yml`` (the file is ``.github/workflows/release.yml``)
* Environment name: ``release``

An authorized GitHub administrator must separately create and protect the
``release`` environment. Configure required human reviewers, prevent self-review,
and restrict deployment to the intended version tags (``v*``), not arbitrary
branches. Review repository tag protections as well. These PyPI and GitHub
settings are prerequisites; adding this workflow does not configure them. Their
actual availability and protection rules must be verified before publishing.

Workflow and approval boundary
-------------------------------

Stop after local preparation and artifact review. Obtain explicit approval for
the release commit, version tag, repository push, and package upload before
those actions. Recheck that PyPI does not already contain version 1.2.0.
No upload, tagging, settings change, or push is part of this preparation.

``.github/workflows/release.yml`` has two entry points:

* ``workflow_dispatch`` validates the selected ref only. It does not require a
  version tag and **never publishes**, even when run against a tag.
* ``release.published`` validates and then publishes a stable, non-draft release
  only. The triggering release tag is explicitly checked out and must exactly
  equal ``v<PACKAGE_VERSION>`` (for this release, ``v1.2.0``). Prereleases and
  drafts are excluded from both validation and publishing. Publishing a stable
  GitHub release is therefore a publication trigger, not a validation preview.

Before running repository code, the workflow reads the version using only
stdlib AST parsing and literal evaluation. It builds from a ``git archive``
snapshot, not working-directory junk, on Ubuntu 24.04 with Python 3.12 and Node
22. Validation includes Python regressions, strict Sphinx 9 docs, frontend lint,
Jest and production build from the extracted sdist, full and production npm audits,
archive inspection of every shipped map/SVG and flattened frontend copy,
strict Twine checks, and isolated wheel/sdist installation with ``pip check``
and engine/render/export smoke tests. The sdist carries its own checker and
packaging regressions so they can be rerun after extraction.

The validation job uploads one immutable artifact containing exactly the wheel,
sdist, and ``SHA256SUMS`` manifest. The publish job downloads that exact artifact
by ID, checks the two safe filenames and checksums, and moves only the two
distributions into its publishing directory. It does not check out source or
rebuild. Only this job receives ``id-token: write`` and enters the protected
``release`` environment at https://pypi.org/p/diplomacy. The PyPI action uses
Trusted Publishing with attestations enabled and ``skip-existing: false``.
A collision fails rather than silently accepting an existing upload. Concurrent
runs do not cancel an in-progress publish.

For a separately authorized release, review the validation results, artifact
checksums, tag/metadata agreement, and environment approval before allowing the
publish job to proceed. A manual validation artifact is not promoted for upload:
the release event validates its own tagged snapshot and publishes those exact
validated bytes without a rebuild between jobs. If validation fails or artifacts
change, stop and review again. GitHub-hosted execution and OIDC publishing cannot
be verified by local checks alone.
