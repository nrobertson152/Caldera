# Architecture

Caldera is a Python 3 / PySide6 (Qt 6) desktop application. The calculation and data layers are **Qt-free**, so
they can be tested without a display and reused outside the GUI.

```
caldera/
├── __main__.py            python -m caldera
├── app.py                 Window, tabs, navigation, persistence, project/history actions
├── registry.py            TOOLS: name -> (field specs, function)
├── calculations.py        core calculators
├── legacy_calculations.py calculators carried over from the earlier app
├── extended.py            additional calculators
├── seal_data.py           seal compatibility matrix
├── tank.py                Reservoir / Drip Pan sizing (gauge tables, carbon vs stainless, drip rail)
├── model3d.py             scene builder + orthographic projection for the 3D tank view
├── toolmeta.py            navigation model, icons, formulas, parse_number, evaluate() -> Result
├── workspace.py           defaults, sanitize, atomic save/load, .caldera and .caldera_backup files
├── exports.py             PDF, CSV, XLSX and text reports
├── assets/                icon, stylesheet, Inter font
└── ui/
    ├── theme.py, widgets.py, kit.py   themes and custom-painted components
    ├── chrome.py          sidebar, tab bar, top bar, command palette, modal sheets
    ├── icons.py           vector icon set
    ├── pages_core.py      overview, CalculatorPage
    ├── page_tank.py       Reservoir / Drip Pan page
    ├── pages_data.py      history, projects, compare
    ├── pages_tools.py     settings, about, reference and utility pages
    └── viewer3d.py        software-painted 3D viewer (no OpenGL)
```

## Layers

**Calculators.** `registry.TOOLS` maps each calculator name to its input field specs and the function that
computes it. A spec's default is a number, a `Choice(list)` (drop-down) or a `Toggle(on)` (tick box).

**Metadata and evaluation.** `toolmeta` holds the sidebar categories, icons, descriptions and formulas.
`evaluate()` runs a calculator and returns a `Result` (metrics, pass/fail state, raw text). `parse_number`
accepts simple expressions like `30/2` or `2*pi*1.5` without using `eval`. `sweep_all` / `is_linear` decide which
input/output pairs get a sensitivity chart; perfectly linear tools get none.

**Workspace.** All user state (projects, history, presets, drafts, tabs, settings) lives in one JSON workspace.
It is sanitised on load, written atomically, and an unreadable file is set aside instead of overwritten.
Location: `$CALDERA_DATA`, else `$XDG_DATA_HOME/caldera`, else `~/.local/share/caldera`.

**UI.** `app.Window` owns a set of tabs; each `Tab` has its current page and its own back/forward stack, and the
tab set is saved in the workspace. `navigate()` only changes the current tab; new tabs come from `new_tab()`.

## Gotchas

- Pages are rebuilt on every navigation; state lives in `win.data`, not in widgets.
- `QPushButton` ignores the size hint of an inner layout, so `ClickRow` overrides `sizeHint`.
- Word-wrapped labels in frameless dialogs need an explicit height (`Sheet._fit`).

## Tests

| File | Needs Qt | Covers |
|---|---|---|
| `tests/test_core.py` | No | every calculator with defaults, number parsing, workspace persistence, exports, tank, 3D model, project/backup files |
| `tests/test_migration.py` | No | regression values carried over from the earlier app |
| `tests/test_gui.py` | Yes (offscreen) | opens the real window, visits every page and saves a screenshot of each to `screenshots/` |
