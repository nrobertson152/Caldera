# Changelog

All notable changes to Caldera are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.1] - 2026-10-30

### Fixed
- Rotating the 3D preview in Reservoir / Drip Pan no longer crashes the app.
- Hovering or otherwise interacting with the sensitivity charts no longer crashes the app.
  Both crashes came from a bug in PySide6 6.12.0: on Python 3.10/3.11, each paint call leaked a
  reference to `None` until Python aborted ("deallocating None"). Views that repaint continuously hit it within seconds.
  PySide6 is now pinned below 6.12, and the AppImage is built on Python 3.12, which is not affected.

### Added
- `tests/test_interaction.py`: drags, zooms and resets the 3D viewer and hovers every sensitivity chart under real Qt;
  runs in CI on Python 3.10-3.12.

### Changed
- Repository restructured: the application now lives at the repository root (`caldera/`, `tests/`, `packaging/`)
  instead of inside a `Caldera_1.0.0/` folder.
- Launch with `python3 -m caldera`, or install with `pip install .` and run `caldera`.
- Tests moved to `tests/` (`test_core.py`, `test_migration.py`, `test_gui.py`).

### Added
- `pyproject.toml` with package metadata and a `caldera` launcher.
- Continuous-integration workflow that runs the calculation tests and the offscreen GUI test on every push.
- Architecture notes in `docs/ARCHITECTURE.md`.

## [1.0.0] - 2026-10-30

First public release.

- 21 live calculators across hydraulic, pneumatic, mechanical and electrical disciplines.
- Tabbed workspace with per-tab back / forward history, a Ctrl+K command palette and a collapsible sidebar.
- Reservoir / Drip Pan sizing with a rotatable 3D preview.
- Projects, calculation history, side-by-side comparison, and PDF / CSV / XLSX export.
- `.caldera` project files and `.caldera_backup` workspace backups.
- Five themes: Obsidian, Midnight, Graphite, Light and Terracotta.
- Linux AppImage built by GitHub Actions.

[Unreleased]: https://github.com/nrobertson152/caldera/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/nrobertson152/caldera/releases/tag/v1.0.0
