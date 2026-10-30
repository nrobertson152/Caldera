# Changelog

All notable changes to Caldera are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-10-30

### Added
- **Metric / US customary units.** A setting (Settings → Calculations, or the command palette) switches every
  calculator's inputs, results, charts and 3D captions between US customary and metric. Calculations, drafts,
  presets and saved inputs stay in US customary internally, so nothing already saved changes.
- **Notes on calculations.** Every calculator has a Notes box; "Save to project" stores the note with the result.
  Notes can be edited in History, are searchable, appear in Compare and are included in CSV, Excel and PDF exports.
- **Reservoir / Drip Pan safety checks**: zero or small air gap, a pan that cannot contain the tank's oil, less than
  110 % containment, no drip rail, tank not fitting the rail, tight clearance, shallow oil, open top, thin walls on
  tall tanks, thin aluminum, aluminum touching steel (galvanic corrosion) and very heavy assemblies.
- **Hydraulic Cylinder Cycle Time animation**: a play / pause button animates the cylinder extending and retracting
  at the calculated times, with ¼× to 5× speed, loop and a timeline.
- **Line Velocity recommendations**: choose suction, return or pressure line to see the recommended velocity range
  (Parker nomograph), a pass / warning verdict, the smallest inside diameter and hose dash size, and a table for every
  line type.
- **Compare Calculations** now takes up to three results, with changes shown relative to A.
- **Seal Compatibility**: 12 fluid families (mineral, HFA/HFB, HFC, HFDR, HFDU, HETG, HEES, HEPG, HEPR, water,
  diesel, brake fluid) and 12 materials, plus an all-fluids matrix, a material guide (temperature range, hardness,
  strengths, weaknesses) and selection tips.
- **Reference Tables**: sections for conversions (many more), fraction / decimal / mm, hydraulic (line velocity,
  hose dash sizes and JIC / SAE ORB threads, ISO VG grades, ISO 4406 cleanliness targets), electrical (NEC motor
  full-load amps, copper ampacity), pipe dimensions, bolt torque and handy formulas.

### Changed
- **Reservoir / Drip Pan materials and thickness.** Seven materials: carbon steel (A36), HSLA steel (A572 Gr 50),
  galvanized steel (G90), stainless 304 and 316, aluminum 5052-H32 and 6061-T6. Thickness can be a gauge (28 to 7 ga)
  or plate (1/8", 3/16", 1/4", 5/16", 3/8", 1/2"). Gauges use each material's own standard, and every option shows its
  real thickness for the chosen material.
- **Conduit Fill** rebuilt: list any mix of conductor sizes and insulations (THHN/THWN-2, XHHW, THW, bare copper or a
  custom area), pick a conduit type (EMT, RMC, IMC, PVC 40/80, FMC, LFMC), and get the NEC fill limit (53 / 31 / 40 %,
  60 % nipples), the recommended trade size, and the smallest size for every conduit type.
- **Charts**: axis numbers use compact labels (1.2k, 45k, 3.5M) so large values are no longer cut off, the left margin
  fits the widest label, and the y-axis has a title.
- About page: the GPL button uses a licence icon instead of the Caldera logo (and shows the official GNU artwork if
  `caldera/assets/gnu.svg` is added).

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
