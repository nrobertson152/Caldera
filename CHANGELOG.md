# Changelog

All notable changes to Caldera are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
