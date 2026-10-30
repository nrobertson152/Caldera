"""Settings, about, reference, seal compatibility, methodology, table editors and the report builder."""
import math
from datetime import date

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QBoxLayout, QFrame, QGridLayout, QLineEdit, QPlainTextEdit,
                               QTableWidget, QTableWidgetItem, QWidget)

from .. import __version__, exports, units
from ..registry import TOOLS
from ..reference_data import SECTIONS as REF_SECTIONS
from ..seal_data import FLUIDS as SEAL_FLUIDS, GUIDE as SEAL_GUIDE, MATERIALS as SEAL_MATERIALS, SEAL_MATRIX, \
    SYMBOL as SEAL_SYMBOL, TIPS as SEAL_TIPS
from ..toolmeta import CATEGORIES, DEFAULT_NOTE, FORMULAS, NOTES, blurb_of, icon_of, parse_number
from . import icons
from .kit import IconTile, clear_layout, fit_table_height, page_header, section_title, setting_row
from .theme import THEMES, current as T
from .widgets import (Banner, BrandMark, Card, Combo, Field, Pill, ScrollPage, Segmented, Switch, ThemeSwatch, button,
                      hbox, label, style_table, vbox)

DISCLAIMER = ('THIS SOFTWARE IS PROVIDED WITHOUT ANY WARRANTY, INCLUDING THE IMPLIED WARRANTIES OF MERCHANTABILITY OR '
              'FITNESS FOR A PARTICULAR PURPOSE. CALCULATIONS AND REFERENCE DATA MAY CONTAIN ERRORS. VERIFY RESULTS '
              'INDEPENDENTLY BEFORE DESIGN, CONSTRUCTION, INSTALLATION OR OPERATION. CALDERA DOES NOT REPLACE '
              'ENGINEERING JUDGMENT, PROFESSIONAL REVIEW, APPLICABLE CODES, SAFETY STANDARDS, OR MANUFACTURER '
              'DOCUMENTATION. THE AUTHORS AND CONTRIBUTORS ARE NOT LIABLE FOR DAMAGES TO THE EXTENT PERMITTED BY LAW.')


def _kbd_row(keys, text):
    w = QWidget()
    r = hbox(w, (0, 5, 0, 5), 8)
    r.addWidget(label(text, 'muted'), 1)
    for k in keys:
        r.addWidget(label(k, 'kbd'))
    return w


# =========================================================================== settings
def settings_page(win):
    t = T()
    page = ScrollPage(max_width=940)
    col = page.col
    col.addWidget(page_header('Settings', 'Appearance, number formatting and your local workspace.'))

    look = Card(padding=22, spacing=14)
    look.body.addWidget(section_title('Appearance', '%d themes' % len(THEMES)))
    holder = QWidget()
    grid = QGridLayout(holder)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(18)
    grid.setVerticalSpacing(14)
    for i, (name, theme) in enumerate(THEMES.items()):
        sw = ThemeSwatch(theme, name == win.data.get('theme'))
        sw.clicked.connect(win.set_theme)
        grid.addWidget(sw, i // 3, i % 3)
    for c in range(3):
        grid.setColumnStretch(c, 1)
    look.body.addWidget(holder)
    col.addWidget(look)

    prefs = Card(padding=22, spacing=6)
    prefs.body.addWidget(section_title('Calculations'))
    unit_seg = Segmented(list(units.SYSTEMS), units.SYSTEM)
    unit_seg.changed.connect(win.set_units)
    prefs.body.addWidget(setting_row('Units', 'Show and enter every calculator in US customary (in, PSI, GPM, lb) or '
                                              'metric (mm, bar, L/min, kg). Saved results keep the units they were '
                                              'saved in.', unit_seg))
    precision = Combo([str(i) for i in range(1, 11)])
    precision.setCurrentText(str(win.precision))
    precision.setMinimumWidth(90)
    precision.currentTextChanged.connect(lambda v: win.update_option('precision', int(v)))
    prefs.body.addWidget(setting_row('Decimal places', 'How many decimals results show. Stored values keep full precision.',
                                     precision))
    auto = Switch(win.data.get('auto_save', False))
    auto.toggled.connect(lambda v: win.update_option('auto_save', bool(v)))
    prefs.body.addWidget(setting_row('Auto-save on Ctrl+Enter',
                                     'Pressing Ctrl+Enter in a calculator also saves the result to the active project.',
                                     auto))
    col.addWidget(prefs)

    ws = Card(padding=22, spacing=10)
    ws.body.addWidget(section_title('Workspace'))
    ws.body.addWidget(label('Everything is stored on this computer. Nothing is ever uploaded.', 'muted', wrap=True))
    box = QFrame()
    box.setObjectName('tile')
    bl = vbox(box, (14, 11, 14, 11), 0)
    bl.addWidget(label(str(win.store_path), 'mono', wrap=True, selectable=True))
    ws.body.addWidget(box)
    row = hbox(None, (0, 4, 0, 0), 10)
    row.addWidget(button('Export backup (.caldera_backup)…', 'primary', 'download', win.export_data))
    row.addWidget(button('Restore backup…', '', 'upload', win.restore_data))
    row.addWidget(button('Open data folder', 'ghost', 'folder',
                         lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(win.store_path.parent)))))
    row.addStretch(1)
    ws.body.addLayout(row)
    col.addWidget(ws)

    keys = Card(padding=22, spacing=2)
    keys.body.addWidget(section_title('Keyboard shortcuts'))
    for ks, text in ((['Ctrl', 'K'], 'Search everything'), (['Ctrl', '↵'], 'Recalculate (and auto-save if enabled)'),
                     (['Ctrl', 'S'], 'Save the current result to the active project'),
                     (['Ctrl', 'B'], 'Collapse or expand the sidebar'), (['Alt', '←'], 'Back'), (['Alt', '→'], 'Forward'),
                     (['↑', '↓'], 'Step the value in a focused field (hold Shift for ×10)')):
        keys.body.addWidget(_kbd_row(ks, text))
    col.addWidget(keys)
    col.addStretch(1)
    return page


# =========================================================================== about
def about_page(win):
    page = ScrollPage(max_width=860)
    col = page.col
    hero = Card(padding=30, spacing=10, name='hero')
    top = hbox(None, (0, 0, 0, 0), 18)
    top.addWidget(BrandMark(72), 0, Qt.AlignmentFlag.AlignTop)
    titles = vbox(None, (0, 0, 0, 0), 4)
    titles.addWidget(label('Caldera', 'display'))
    titles.addWidget(label('Offline engineering calculation and project workspace.', 'muted'))
    pills = hbox(None, (0, 6, 0, 0), 8)
    pills.addWidget(Pill("Version " + __version__))
    pills.addWidget(Pill('Qt 6 · PySide6', 'Muted'))
    pills.addWidget(Pill('GPL-3.0', 'Muted'))
    pills.addStretch(1)
    titles.addLayout(pills)
    top.addLayout(titles, 1)
    hero.body.addLayout(top)
    col.addWidget(hero)

    lic = Card(padding=22, spacing=8)
    lic.body.addWidget(section_title('License'))
    lic.body.addWidget(label('Copyright © 2026 Nate Robertson', 'h3'))
    lic.body.addWidget(label('Caldera is free and open-source software, licensed under the GNU General Public License '
                             'version 3. You may use, study, modify and redistribute it under the terms of that license. '
                             'We hope Caldera will be useful to as many people as possible. See LICENSE for the full terms.',
                             'muted', wrap=True))
    lrow = hbox(None, (0, 4, 0, 0), 10)
    gpl = button('GNU GPL version 3 (full text)', '', None,
                 lambda: QDesktopServices.openUrl(QUrl('https://www.gnu.org/licenses/gpl-3.0.html')))
    gnu = Path(__file__).resolve().parent.parent / 'assets' / 'gnu.svg'      # official GNU head, if bundled
    gpl.setIcon(QIcon(str(gnu)) if gnu.exists() else icons.icon('scale', T()['text'], 18))
    gpl.setIconSize(QSize(18, 18))
    lrow.addWidget(gpl)
    lrow.addStretch(1)
    lic.body.addLayout(lrow)
    col.addWidget(lic)
    col.addWidget(Banner('warn', DISCLAIMER))
    col.addStretch(1)
    return page


# =========================================================================== reference
def reference_page(win):
    t = T()
    page = ScrollPage(max_width=1100)
    col = page.col
    col.addWidget(page_header('Reference Tables', blurb_of('Reference Tables') +
                              ' Verify against published standards for design work.', 'Utilities'))
    sections = list(REF_SECTIONS)
    start = getattr(win, 'reference_section', sections[0])
    seg = Segmented(sections, start if start in sections else sections[0])
    bar = hbox(None, (0, 0, 0, 0), 12)
    bar.addWidget(seg)
    bar.addStretch(1)
    col.addLayout(bar)
    find = QLineEdit()
    find.setPlaceholderText('Filter this section…')
    find.setClearButtonEnabled(True)
    find.setFixedHeight(40)
    col.addWidget(find)
    host = vbox(None, (0, 0, 0, 0), 14)
    col.addLayout(host)
    col.addStretch(1)
    built = []          # (table, rows, title widget, note widget)

    def show(section):
        win.reference_section = section
        clear_layout(host)
        built.clear()
        colors = list(t['cats'].values())
        for k, (title, headers, rows, note) in enumerate(REF_SECTIONS[section]):
            head = section_title(title, color=colors[k % len(colors)])
            host.addWidget(head)
            table = QTableWidget(0, len(headers))
            table.setHorizontalHeaderLabels(headers)
            style_table(table, 40)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
            host.addWidget(table)
            note_w = label(note, 'faint', wrap=True) if note else None
            if note_w:
                host.addWidget(note_w)
            built.append((table, [[str(c) for c in r] for r in rows], head, note_w))
        filt(find.text())

    def filt(text):
        needle = text.strip().casefold()
        for table, rows, head, note_w in built:
            keep = [r for r in rows if not needle or needle in ' '.join(r).casefold()]
            table.setRowCount(len(keep))
            for i, r in enumerate(keep):
                for c, v in enumerate(r):
                    item = QTableWidgetItem(v)
                    if c == 0:
                        item.setForeground(QColor(t['muted'] if len(r) == 3 and section_is_conv() else t['text']))
                    table.setItem(i, c, item)
            fit_table_height(table)
            for w in (table, head, note_w):
                if w is not None:
                    w.setVisible(bool(keep))

    def section_is_conv():
        return seg.current == 'Conversions'

    find.textChanged.connect(filt)
    seg.changed.connect(show)
    show(seg.current)
    return page


# =========================================================================== seals
def _temp_range(lo, hi):
    f = lambda c: c * 9 / 5 + 32
    if units.metric():
        return '%d to %d °C' % (lo, hi)
    return '%d to %d °F  (%d to %d °C)' % (round(f(lo)), round(f(hi)), lo, hi)


def seals_page(win):
    t = T()
    page = ScrollPage(max_width=1200)
    col = page.col
    col.addWidget(page_header('Hydraulic Seal Compatibility', blurb_of('Seal Compatibility'), 'Hydraulic'))
    palette = {'good': (t['good_soft'], t['good']), 'conditional': (t['warn_soft'], t['warn']),
               'bad': (t['bad_soft'], t['bad']), 'unknown': (t['raised'], t['muted'])}
    views = ['By fluid', 'All fluids', 'Material guide', 'Selection tips']
    start_view = getattr(win, 'seal_view', views[0])
    seg = Segmented(views, start_view if start_view in views else views[0])
    bar = hbox(None, (0, 0, 0, 0), 14)
    bar.addWidget(seg)
    bar.addStretch(1)
    for text, kind in (('Compatible', 'Good'), ('Conditional', 'Warn'), ('Unsuitable', 'Bad'), ('No data', 'Muted')):
        bar.addWidget(Pill(text, kind))
    col.addLayout(bar)
    host = vbox(None, (0, 0, 0, 0), 14)
    col.addLayout(host)
    col.addWidget(Banner('warn', 'Compatibility depends on the exact polymer compound, fluid additives, temperature, '
                                 'pressure, speed and seal construction. These ratings are general screening '
                                 'guidance, not approvals: confirm with the seal and fluid manufacturers.'))
    col.addStretch(1)

    def table(headers, nrows, height=52):
        tbl = QTableWidget(nrows, len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        style_table(tbl, height)
        tbl.setWordWrap(True)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        return tbl

    def by_fluid():
        fluids = list(SEAL_MATRIX)
        start = getattr(win, 'seal_fluid', fluids[0])
        pick = hbox(None, (0, 0, 0, 0), 12)
        pick.addWidget(label('Fluid', 'muted'))
        combo = Combo(fluids)
        combo.setCurrentText(start if start in fluids else fluids[0])
        combo.setMinimumWidth(300)
        pick.addWidget(combo)
        desc = label('', 'faint', wrap=True)
        pick.addWidget(desc, 1)
        host.addLayout(pick)
        tbl = table(['SEAL MATERIAL', 'COMPATIBILITY', 'NOTES AND LIMITS'], 0, 56)
        tbl.horizontalHeader().setSectionResizeMode(0, tbl.horizontalHeader().ResizeMode.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, tbl.horizontalHeader().ResizeMode.ResizeToContents)
        host.addWidget(tbl)

        def fill(fluid):
            win.seal_fluid = fluid
            cls, text, _rows = SEAL_FLUIDS[fluid]
            desc.setText('%s  ·  %s' % (cls, text) if cls != '—' else text)
            rows = SEAL_MATRIX[fluid]
            tbl.setRowCount(len(rows))
            for i, (material, rating, note, tag) in enumerate(rows):
                bg, fg = palette.get(tag, palette['unknown'])
                m = QTableWidgetItem(material)
                m.setForeground(QColor(t['text']))
                r = QTableWidgetItem('●  ' + rating)
                r.setBackground(QColor(bg))
                r.setForeground(QColor(fg))
                n = QTableWidgetItem(note)
                n.setForeground(QColor(t['muted']))
                for c, item in enumerate((m, r, n)):
                    tbl.setItem(i, c, item)
            fit_table_height(tbl)

        combo.currentTextChanged.connect(fill)
        fill(combo.currentText())

    def all_fluids():
        fluids = list(SEAL_FLUIDS)
        heads = ['MATERIAL'] + [SEAL_FLUIDS[f][0] if SEAL_FLUIDS[f][0] != '—' else f.split(' ')[0].rstrip(',/')
                                for f in fluids]
        tbl = table(heads, len(SEAL_MATERIALS), 40)
        tbl.horizontalHeader().setSectionResizeMode(0, tbl.horizontalHeader().ResizeMode.ResizeToContents)
        for c, f in enumerate(fluids, start=1):
            tbl.horizontalHeaderItem(c).setToolTip(f)
        for r, m in enumerate(SEAL_MATERIALS):
            item = QTableWidgetItem(m)
            item.setForeground(QColor(t['text']))
            tbl.setItem(r, 0, item)
            for c, f in enumerate(fluids, start=1):
                tag, note = SEAL_FLUIDS[f][2][m]
                bg, fg = palette.get(tag, palette['unknown'])
                cell = QTableWidgetItem(SEAL_SYMBOL[tag])
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setBackground(QColor(bg))
                cell.setForeground(QColor(fg))
                cell.setToolTip('%s in %s: %s' % (m, f, note))
                tbl.setItem(r, c, cell)
        fit_table_height(tbl)
        host.addWidget(label('Hover a cell for the note. ✓ compatible   ~ conditional   ✗ unsuitable   ? no data.  '
                             'Columns: ' + ',  '.join('%s = %s' % (h, f) for h, f in zip(heads[1:], fluids)), 'faint',
                             wrap=True))
        host.addWidget(tbl)

    def guide():
        tbl = table(['MATERIAL', 'TYPICAL TEMPERATURE', 'HARDNESS', 'STRENGTHS', 'WATCH OUT FOR'], len(SEAL_GUIDE), 64)
        tbl.horizontalHeader().setSectionResizeMode(0, tbl.horizontalHeader().ResizeMode.ResizeToContents)
        for r, (m, ((lo, hi), hard, good, bad)) in enumerate(SEAL_GUIDE.items()):
            for c, text in enumerate((m, _temp_range(lo, hi), hard, good, bad)):
                item = QTableWidgetItem(text)
                item.setForeground(QColor(t['text'] if c == 0 else (t['bad'] if c == 4 else t['muted'])))
                tbl.setItem(r, c, item)
        tbl.resizeRowsToContents()
        fit_table_height(tbl)
        host.addWidget(tbl)

    def tips():
        for title, text in SEAL_TIPS:
            card = Card(padding=18, spacing=6)
            card.body.addWidget(label(title, 'h3'))
            card.body.addWidget(label(text, 'muted', wrap=True))
            host.addWidget(card)

    builders = dict(zip(views, (by_fluid, all_fluids, guide, tips)))

    def show(view):
        win.seal_view = view
        clear_layout(host)
        builders[view]()

    seg.changed.connect(show)
    show(seg.current)
    return page


# =========================================================================== methodology
def methodology_page(win):
    t = T()
    page = ScrollPage(max_width=1000)
    col = page.col
    col.addWidget(page_header('Methodology', blurb_of('Methodology') + ' Every number in Caldera is an estimate: '
                              'check inputs, units and applicable standards.', 'Utilities'))
    if units.metric():
        col.addWidget(Banner('warn', 'Formulas are written in US customary units, which is how Caldera calculates. '
                                     'With metric units selected, your inputs are converted before the calculation and '
                                     'the results are converted back for display.'))
    find = QLineEdit()
    find.setPlaceholderText('Filter by calculator or formula…')
    find.setClearButtonEnabled(True)
    find.setFixedHeight(40)
    col.addWidget(find)

    cards = []   # (haystack, widgets-to-toggle)
    for cat, names in CATEGORIES.items():
        mine = [n for n in names if n in TOOLS]
        if not mine:
            continue
        head = section_title(cat, '%d calculators' % len(mine), t['cats'][cat])
        col.addWidget(head)
        group = []
        for n in mine:
            card = Card(padding=20, spacing=10)
            top = hbox(None, (0, 0, 0, 0), 12)
            top.addWidget(IconTile(icon_of(n), t['cats'][cat], 38), 0, Qt.AlignmentFlag.AlignTop)
            tt = vbox(None, (0, 0, 0, 0), 2)
            tt.addWidget(label(n, 'h2'))
            tt.addWidget(label(blurb_of(n), 'faint', wrap=True))
            top.addLayout(tt, 1)
            card.body.addLayout(top)
            box = QFrame()
            box.setObjectName('tile')
            bl = vbox(box, (16, 12, 16, 12), 5)
            for line in FORMULAS.get(n, ['See calculator notes.']):
                bl.addWidget(label(line, 'mono', selectable=True))
            card.body.addWidget(box)
            card.body.addWidget(label(NOTES.get(n, DEFAULT_NOTE), 'faint', wrap=True))
            col.addWidget(card)
            hay = ' '.join([n, cat, blurb_of(n)] + FORMULAS.get(n, [])).casefold()
            cards.append((hay, card))
            group.append(card)
        cards.append((None, (head, group)))
    col.addStretch(1)

    def filt(text):
        needle = text.strip().casefold()
        for hay, obj in cards:
            if hay is not None:
                obj.setVisible(not needle or needle in hay)
        for hay, obj in cards:
            if hay is None:
                head, group = obj
                head.setVisible(any(not c.isHidden() for c in group))

    find.textChanged.connect(filt)
    focus = getattr(win, 'methodology_focus', '')
    if focus:
        find.setText(focus)
        win.methodology_focus = ''
    return page


# =========================================================================== editable tables
def _load_rows(win, title, ncols):
    out = []
    for row in win.data.get('tables', {}).get(title, []):
        if isinstance(row, list):
            out.append([str(v) for v in row[:ncols]] + [''] * (ncols - len(row)))
    return out


def _summarize_loads(rows):
    total_a = kva = 0.0
    n = 0
    for r in rows:
        try:
            volts, amps = parse_number(r[1]), parse_number(r[3])
        except (ValueError, IndexError):
            continue
        phase = math.sqrt(3) if '3' in str(r[2]) else 1.0
        total_a += amps
        kva += volts * amps * phase / 1000
        n += 1
    if not n:
        return 'Add voltage, phase and current to see totals.'
    return '%d load%s   ·   Σ current %s A   ·   Σ apparent power %s kVA' % (
        n, '' if n == 1 else 's', '{:,.2f}'.format(total_a), '{:,.2f}'.format(kva))


def table_editor_page(win, title, columns):
    page = ScrollPage(max_width=1280)
    col = page.col
    desc = {'Electrical Load Summary': 'Tabulate loads by voltage, phase and current. Totals update as you type.',
            'Wire List / CSV Generator': 'Build a wire schedule and export it as CSV for the shop floor.'}.get(title, '')
    table = QTableWidget(0, len(columns))
    summary = label('', 'muted')

    def rows_now():
        return [[table.item(r, c).text() if table.item(r, c) else '' for c in range(len(columns))]
                for r in range(table.rowCount())]

    def persist(*_):
        win.data.setdefault('tables', {})[title] = rows_now()
        win.schedule_save()
        refresh_summary()

    def refresh_summary():
        rows = rows_now()
        filled = sum(1 for r in rows if any(v.strip() for v in r))
        if title == 'Electrical Load Summary':
            summary.setText(_summarize_loads(rows))
        else:
            summary.setText('%d row%s' % (filled, '' if filled == 1 else 's'))

    def add_row():
        table.blockSignals(True)
        table.insertRow(table.rowCount())
        table.blockSignals(False)
        table.setCurrentCell(table.rowCount() - 1, 0)
        table.editItem(table.item(table.rowCount() - 1, 0) or _blank(table.rowCount() - 1))
        persist()

    def _blank(r):
        item = QTableWidgetItem('')
        table.setItem(r, 0, item)
        return item

    def delete_rows():
        picked = sorted({i.row() for i in table.selectedIndexes()}, reverse=True)
        if not picked:
            win.toast('Select one or more rows first', 'info')
            return
        table.blockSignals(True)
        for r in picked:
            table.removeRow(r)
        if not table.rowCount():
            table.insertRow(0)
        table.blockSignals(False)
        persist()
        win.toast('Deleted %d row%s' % (len(picked), '' if len(picked) == 1 else 's'), 'info')

    def export_csv():
        path = win.pick_save('Export CSV', title.lower().replace(' / ', '_').replace(' ', '_') + '.csv', 'CSV (*.csv)')
        if path:
            exports.write_table_csv(path, columns, rows_now())
            win.toast('Exported %s' % path.rsplit('/', 1)[-1])

    col.addWidget(page_header(title, desc, 'Electrical', [
        button('Delete rows', 'ghost', 'trash', delete_rows), button('Export CSV', '', 'download', export_csv),
        button('Add row', 'primary', 'plus', add_row)]))

    table.setHorizontalHeaderLabels([c.upper() for c in columns])
    style_table(table, 46)
    table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed |
                          QAbstractItemView.EditTrigger.AnyKeyPressed)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
    table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    table.setMinimumHeight(430)
    table.blockSignals(True)
    saved = _load_rows(win, title, len(columns))
    table.setRowCount(len(saved) or 1)
    for r, vals in enumerate(saved):
        for c, v in enumerate(vals):
            table.setItem(r, c, QTableWidgetItem(v))
    table.blockSignals(False)
    table.itemChanged.connect(persist)
    col.addWidget(table, 1)
    foot = hbox(None, (2, 0, 2, 0), 12)
    foot.addWidget(summary, 1)
    foot.addWidget(label('Double-click or just start typing to edit a cell', 'faint'))
    col.addLayout(foot)
    refresh_summary()
    return page


# =========================================================================== test report
def report_page(win):
    t = T()
    page = ScrollPage(max_width=1240)
    col = page.col
    draft = win.data.setdefault('report_draft', {})
    draft.setdefault('date', date.today().isoformat())
    col.addWidget(page_header('Test Report Generator', blurb_of('Test Report Generator'), 'Utilities'))
    cols = QBoxLayout(QBoxLayout.Direction.LeftToRight)
    cols.setSpacing(20)
    col.addLayout(cols)

    form = Card(padding=22, spacing=14)
    form.body.addWidget(section_title('Details'))
    widgets = {}
    short = [(k, c) for k, c in exports.REPORT_FIELDS if k in ('title', 'asset', 'tech', 'date')]
    long = [(k, c) for k, c in exports.REPORT_FIELDS if k in ('procedure', 'results')]
    grid = QGridLayout()
    grid.setHorizontalSpacing(14)
    grid.setVerticalSpacing(12)
    for i, (key, caption) in enumerate(short):
        wrap = QWidget()
        v = vbox(wrap, (0, 0, 0, 0), 6)
        v.addWidget(label(caption, 'muted'))
        f = Field(draft.get(key, ''), '', numeric=False)
        widgets[key] = f
        v.addWidget(f)
        grid.addWidget(wrap, i // 2, i % 2)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    form.body.addLayout(grid)
    for key, caption in long:
        form.body.addWidget(label(caption, 'muted'))
        e = QPlainTextEdit(draft.get(key, ''))
        e.setMinimumHeight(130)
        widgets[key] = e
        form.body.addWidget(e)
    cols.addWidget(form, 5)

    side = vbox(None, (0, 0, 0, 0), 14)
    prev = Card(padding=22, spacing=10)
    prev.body.addWidget(section_title('Preview'))
    box = QFrame()
    box.setObjectName('tile')
    bl = vbox(box, (16, 14, 16, 14), 0)
    preview = label('', 'mono', wrap=True, selectable=True)
    bl.addWidget(preview)
    prev.body.addWidget(box)
    row = hbox(None, (0, 6, 0, 0), 10)
    side.addWidget(prev)
    cols.addLayout(side, 4)

    def values():
        return {k: (w.toPlainText() if isinstance(w, QPlainTextEdit) else w.text()) for k, w in widgets.items()}

    def changed(*_):
        vals = values()
        win.data['report_draft'] = vals
        win.schedule_save()
        preview.setText(exports.report_text(vals))

    def export_txt():
        path = win.pick_save('Export report', 'caldera_test_report.txt', 'Text (*.txt)')
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(exports.report_text(values()))
            win.toast('Report exported')

    def export_pdf():
        path = win.pick_save('Export PDF report', 'caldera_test_report.pdf', 'PDF (*.pdf)')
        if path:
            win.write_pdf(path, values().get('title') or 'Test Report', exports.report_blocks(values()),
                          'Equipment: %s' % (values().get('asset') or '—'))

    row.addWidget(button('Export PDF', 'primary', 'file', export_pdf))
    row.addWidget(button('Export text', '', 'download', export_txt))
    row.addStretch(1)
    prev.body.addLayout(row)
    side.addStretch(1)
    for w in widgets.values():
        (w.textChanged if isinstance(w, QPlainTextEdit) else w.changed).connect(changed)
    changed()
    return page
