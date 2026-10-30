# Caldera 1.0.0

Free and open-source engineering calculation and project workspace for Linux, built with Python 3 and Qt 6 / PySide6.

Copyright © 2026 Nate Robertson. Licensed under GNU GPL version 3.0. See LICENSE.

## Run on Linux Mint

```bash
sudo apt install python3-venv libxcb-cursor0 fonts-dejavu-core
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Features

- Redesigned interface: collapsible sidebar grouped by discipline, pinned tools, back / forward navigation, and a **Ctrl+K command palette** that jumps to any calculator, page or action
- 21 calculators with **live results** (no Calculate button), unit-aware metric cards, a highlighted headline value, pass/fail banners, a hover-able **sensitivity chart** for every calculator, and fields that accept `30/2`, `2*pi*1.5` or `1,234.5`
- Five themes: Obsidian, Midnight, Graphite, Light and Terracotta (serif), with a one-click light / dark toggle
- Color-coded seal compatibility matrix (green = generally compatible; yellow = conditional; red = generally unsuitable) that follows the active theme
- Dashboard with greeting, stats, pinned tools, recent activity and quick actions
- Projects: create, rename, archive, restore, notes and a PDF summary
- Calculation history with search, project filter, pinning, duplicating, moving, deleting, side-by-side comparison, and CSV / XLSX export
- Presets, per-calculator drafts, electrical load and wire-list editors (with load totals), test report builder with live preview (PDF or text)
- **Tabs**: switching tools updates the current tab; a new tab opens only with the + button (or Ctrl+T). Each tab keeps its own back / forward history and tabs are restored on launch
- **Reservoir / Drip Pan** tool: tank and pan size, steel gauge, carbon or stainless, optional drip rail, oil capacity, air gap, weights, and a lightweight rotatable 3D model with a real-size reference object
- **.caldera project files**: export a single project and import it elsewhere (merge or copy). Projects page has search and tick-box filters
- Workspace backup / restore (**.caldera_backup**; older .json backups can still be restored). The workspace is written atomically, and an unreadable file is set aside instead of overwritten

### Keyboard shortcuts

| Keys | Action |
|---|---|
| Ctrl+K | Search everything |
| Ctrl+Enter | Recalculate (also saves if auto-save is on) |
| Ctrl+S | Save current result to the active project |
| Ctrl+T / Ctrl+W | New tab / close tab |
| Ctrl+Tab | Next tab (Shift = previous) |
| Ctrl+B | Collapse / expand the sidebar |
| Alt+← / Alt+→ | Back / forward |
| ↑ / ↓ in a field | Step the value (Shift = ×10) |

## Verification and limitations

Calculation, data-regression, workspace-persistence and export tests run without Qt: `python3 tests.py` and `python3 tests_migration.py`.
`tests_gui.py` opens the real window headlessly, visits every page and writes a screenshot of each one:

```bash
QT_QPA_PLATFORM=offscreen python3 tests_gui.py          # add a theme name to test another theme
```

The interface was developed in an environment where PySide6 could not be installed, so `tests_gui.py` has **not** been run against real Qt yet. Please run it, and report any page that looks wrong. Some specialized workflows, unit controls, and calculations remain incomplete or simplified compared with the prior application. No AppImage is included. Independently verify engineering results against appropriate standards and manufacturer documentation.

## Disclaimer

THIS SOFTWARE IS PROVIDED WITHOUT WARRANTY OF ANY KIND. It is not a substitute for qualified engineering review, applicable codes, or manufacturer specifications. Users are responsible for checking calculations and determining suitability for their applications. We hope it will be useful to as many people as possible.

## Releasing (AppImage)
Push a tag such as `v1.0.0` and the GitHub Actions workflow in `.github/workflows/release.yml` builds
`Caldera-1.0.0-x86_64.AppImage` and attaches it to the release. To build locally on Linux: `./packaging/build_appimage.sh`.
