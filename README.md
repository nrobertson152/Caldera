<div align="center">

<img src="caldera/assets/caldera.svg" alt="Caldera logo" width="96">

# Caldera

**An offline engineering calculation workbench for hydraulic, pneumatic, mechanical and electrical work.**

[![Release](https://img.shields.io/github/v/release/nrobertson152/caldera?label=release)](https://github.com/nrobertson152/caldera/releases/latest)
[![Tests](https://github.com/nrobertson152/caldera/actions/workflows/tests.yml/badge.svg)](https://github.com/nrobertson152/caldera/actions/workflows/tests.yml)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey)

[Download](#installation) · [Features](#features) · [Calculators](#calculators) · [Development](#development) · [Changelog](CHANGELOG.md)

</div>

---

Caldera puts the everyday sizing and checking calculations of industrial and fluid-power work into one fast
desktop app. Results update as you type, every input accepts simple math, and your work is organised into
projects you can export, back up and share. It runs entirely on your machine: no account, no cloud, no telemetry.

## Features

- **21 live calculators.** No Calculate button: unit-aware result cards, a highlighted headline value, pass/fail
  banners and a sensitivity chart showing how each output responds to each input.
- **Inputs that accept math.** Type `30/2`, `2*pi*1.5` or `1,234.5`. Use ↑ / ↓ to step a value (Shift for ×10).
- **Tabs and a command palette.** Work in several tabs, each with its own back / forward history, restored on
  launch. Press **Ctrl+K** to jump to any calculator, page or action.
- **Reservoir / Drip Pan designer.** Tank and pan size, steel gauge, carbon or stainless, optional drip rail, oil
  capacity, air gap and weights, with a rotatable 3D preview beside a real-size reference object.
- **Projects and history.** Save results to projects; search, filter, pin, duplicate, move and compare
  calculations side by side.
- **Reports and exports.** PDF project summaries, a test report builder with live preview, and CSV / XLSX export.
- **Portable files.** Share a single project as a `.caldera` file (import as merge or copy), or back up the whole
  workspace as `.caldera_backup`. Saves are atomic, and a damaged workspace is set aside, never overwritten.
- **Five themes.** Obsidian, Midnight, Graphite, Light and Terracotta, with a one-click light / dark toggle.

## Calculators

| Discipline | Tools |
|---|---|
| **Hydraulic** | Pump & Motor · Hydraulic Motor · Power & Efficiency · Hydraulic Cylinder · Cylinder Cycle Time · Accumulator · Heat Load & Cooler Sizing · Line Velocity · Pressure Drop · Orifice Flow Estimate · Reservoir / Drip Pan · Seal Compatibility |
| **Pneumatic** | Pneumatic Cylinder · Air Consumption · Compressed Air Horsepower |
| **Mechanical** | Cylinder Buckling · Torque, RPM & Power |
| **Electrical** | Motor & Electrical Power · Wire Gauge & Voltage Drop · Conduit Fill · Electrical Load Summary · Wire List / CSV Generator |
| **Utilities** | Unit Converter · Labor Savings · Reference Tables · Test Report Generator · Compare Calculations · Methodology |

The **Methodology** page in the app lists the formula behind each calculator.

## Installation

### AppImage (recommended)

Download `Caldera-<version>-x86_64.AppImage` from the
[latest release](https://github.com/nrobertson152/caldera/releases/latest), then:

```bash
chmod +x Caldera-*-x86_64.AppImage
./Caldera-*-x86_64.AppImage
```

### From source

Requires Python 3.10 or newer. On Debian, Ubuntu or Linux Mint:

```bash
sudo apt install python3-venv libxcb-cursor0
git clone https://github.com/nrobertson152/caldera.git
cd caldera
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m caldera
```

Or install it as a command with `pip install .` and then run `caldera`.

## Keyboard shortcuts

| Keys | Action |
|---|---|
| <kbd>Ctrl</kbd>+<kbd>K</kbd> | Search calculators, pages and actions |
| <kbd>Ctrl</kbd>+<kbd>Enter</kbd> | Recalculate (also saves if auto-save is on) |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> | Save the current result to the active project |
| <kbd>Ctrl</kbd>+<kbd>T</kbd> / <kbd>Ctrl</kbd>+<kbd>W</kbd> | New tab / close tab |
| <kbd>Ctrl</kbd>+<kbd>Tab</kbd> | Next tab (add <kbd>Shift</kbd> for previous) |
| <kbd>Ctrl</kbd>+<kbd>B</kbd> | Collapse / expand the sidebar |
| <kbd>Alt</kbd>+<kbd>←</kbd> / <kbd>Alt</kbd>+<kbd>→</kbd> | Back / forward |
| <kbd>↑</kbd> / <kbd>↓</kbd> in a field | Step the value (<kbd>Shift</kbd> for ×10) |

## Your data

Caldera stores its workspace in `~/.local/share/caldera` (or `$XDG_DATA_HOME/caldera`). Set `CALDERA_DATA` to use a
different folder. Use **Export backup** in Settings to save everything to a single `.caldera_backup` file; backups from
older JSON versions can still be restored.

## Development

```
caldera/            application package
├── *.py            calculators, workspace and exports (Qt-free)
├── ui/             PySide6 interface
└── assets/         icon, stylesheet, fonts
tests/              calculation, migration and GUI smoke tests
packaging/          AppImage build script and desktop entry
docs/               architecture notes
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit together.

### Running the tests

```bash
python3 tests/test_core.py          # calculators, parsing, workspace, exports (no Qt needed)
python3 tests/test_migration.py     # regression values from the earlier app (no Qt needed)
QT_QPA_PLATFORM=offscreen python3 tests/test_gui.py [Theme]   # opens every page, saves screenshots/
```

The GUI test uses a throw-away data folder, so your own workspace is never touched.

### Building the AppImage

```bash
bash packaging/build_appimage.sh    # output: dist/Caldera-<version>-x86_64.AppImage
```

Pushing a tag such as `v1.0.1` runs the [release workflow](.github/workflows/release.yml), which tests, builds the
AppImage and attaches it to the GitHub release. The version comes from `caldera/__init__.py`.

## Contributing

Bug reports and suggestions are welcome in [Issues](https://github.com/nrobertson152/caldera/issues). If a
calculation looks wrong, please include the inputs you used and the result you expected.

## Disclaimer

Caldera is provided **without warranty of any kind**. It is not a substitute for qualified engineering review,
applicable codes or manufacturer specifications. Some workflows and calculations are simplified. Always verify
results independently before relying on them.

## License

Copyright © 2026 Nate Robertson.

Caldera is free software, released under the [GNU General Public License v3.0](LICENSE).
The bundled [Inter](https://rsms.me/inter/) typeface keeps its own license (SIL Open Font License 1.1; see
`caldera/assets/fonts/Inter-LICENSE.txt`).
