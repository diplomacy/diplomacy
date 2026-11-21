# Changelog

## 1.2.0

### Engine, persistence, and server

- Reset unit-owner caches when deep-copying a game while preserving submitted orders (#160).
- Normalize unit locations, case, and whitespace before replacing ownership in `set_units` (#159).
- Preserve saved-game status and outcome across export/import round trips (#158).
- Attribute split-coast retreat influence to the parent province (#152).
- Compute longer convoy chains through ports and refresh bundled convoy caches (#150).
- Add a tested `--server_dir` option with explicit root-directory semantics and creation
  of missing directories, replacing the proposal in #134 (#161).
- Preserve and refresh the DAIDE client guide from #101 against the current
  server/client APIs, including reconnect and power-selection limitations.
- Provide opt-in migration of legacy split-coast influence in saved games (#113).
- Accept overlapping phase-history responses without replacing existing local history (#151).

### Rendering and web interface

- Load single JSON and appended JSONL saved games with explicit game selection and
  propagated validation/read errors (#142).
- Document implicit default actions and how they differ from submitted order history (#118).
- Filter SVG order overlays by issuing power without hiding public board state (#140).
- Expose SVG power-color metadata through the game and renderer APIs (#110).
- Add optional high-contrast army/fleet labels to Python-rendered SVGs (#117).
- Refresh frontend dependencies, replace Create React App with Vite and standalone
  Jest, and preserve map assets and keyboard lifecycle behavior (#170). The frontend
  now requires Node.js 22.13+ and modern browsers: Chrome/Edge 111+, Firefox 114+,
  and Safari 16.4+.

### Packaging and maintenance

- Replace the broad source-distribution include rule with bounded source, map, fixture,
  frontend, and documentation assets. Exclude nested dependency, build, cache, data,
  environment, and credential artifacts; preserve the trusted convoy cache.
- Add a source-distribution regression test, a modern isolated-build backend,
  current Sphinx/Read the Docs configuration, and a maintainer release checklist.
- Retain the legacy Python >=3.5 runtime metadata without claiming renewed validation
  of old interpreters. Release preparation uses Python 3.12; runtime validation
  targets Python 3.10 through 3.13 without implying all targets have passed.

### Validation notes

Release validation is recorded separately from the feature list. Existing frontend
lint debt is not silently waived by the check runner, and this changelog does not imply
that every historical check is clean. Do not publish or tag until the release checklist
has been reviewed and explicitly approved.
