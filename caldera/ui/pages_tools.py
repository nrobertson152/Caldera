"""Settings, about, reference, seal compatibility, methodology, table editors and the report builder."""
import math
from datetime import date

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QBoxLayout, QFrame, QGridLayout, QLineEdit, QPlainTextEdit,
                               QTableWidget, QTableWidgetItem, QWidget)

from .. import exports
from ..registry import TOOLS
from ..seal_data import SEAL_MATRIX
from ..toolmeta import CATEGORIES, DEFAULT_NOTE, FORMULAS, NOTES, blurb_of, icon_of, parse_number
from .kit import IconTile, fit_table_height, page_header, section_title, setting_row
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
    pills.addWidget(Pill('Version 1.0.0'))
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
    gpl.setIcon(QIcon(str(Path(__file__).resolve().parent.parent / 'assets' / 'caldera.svg')))
    gpl.setIconSize(QSize(16, 16))
    lrow.addWidget(gpl)
    lrow.addStretch(1)
    lic.body.addLayout(lrow)
    col.addWidget(lic)
    col.addWidget(Banner('warn', DISCLAIMER))
    col.addStretch(1)
    return page


# =========================================================================== reference
CONVERSIONS = [
    ('Length', '1 in', '25.4 mm'), ('Length', '1 ft', '0.3048 m'), ('Area', '1 in²', '645.16 mm²'),
    ('Volume', '1 US gal', '3.785411784 L'), ('Volume', '1 US gal', '231 in³'), ('Volume', '1 ft³', '7.480519 US gal'),
    ('Flow', '1 GPM', '3.785411784 L/min'), ('Pressure', '1 PSI', '6.894757293 kPa'), ('Pressure', '1 bar', '14.5038 PSI'),
    ('Force', '1 lbf', '4.448221615 N'), ('Torque', '1 lb·ft', '1.355817948 N·m'), ('Power', '1 HP', '0.745699872 kW'),
    ('Power', '1 HP', '550 ft·lbf/s'), ('Mass', '1 lb', '0.45359237 kg'), ('Temperature', '°C', '(°F − 32) × 5/9'),
]
FORMULA_REF = [
    ('Hydraulic power', 'HP ≈ PSI × GPM / 1714'), ('Cylinder area', 'A = π d² / 4'),
    ('Pump flow', 'GPM = (cc/rev × RPM) / 3785.41'), ('Torque and power', 'HP = lb·ft × RPM / 5252.11'),
    ('Cylinder force', 'F = P × A'), ('Reynolds number', 'Re = V D / ν'),
    ('Three-phase current', 'I = kW × 1000 / (√3 × V × PF × η)'), ('Voltage drop (DC / single phase)', 'V = 2 × I × L × R'),
]


def reference_page(win):
    page = ScrollPage(max_width=1000)
    col = page.col
    col.addWidget(page_header('Reference Tables', blurb_of('Reference Tables') +
                              ' Verify against published standards for design work.', 'Utilities'))
    find = QLineEdit()
    find.setPlaceholderText('Filter conversions…')
    find.setClearButtonEnabled(True)
    find.setFixedHeight(40)
    col.addWidget(find)

    table = QTableWidget(0, 3)
    table.setHorizontalHeaderLabels(['QUANTITY', 'FROM', 'EQUALS'])
    style_table(table, 42)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

    def fill(text=''):
        needle = text.strip().casefold()
        rows = [r for r in CONVERSIONS if not needle or needle in ' '.join(r).casefold()]
        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for c, v in enumerate(r):
                item = QTableWidgetItem(v)
                if c == 0:
                    item.setForeground(QColor(T()['muted']))
                table.setItem(i, c, item)
        fit_table_height(table)

    find.textChanged.connect(fill)
    fill()
    col.addWidget(section_title('Conversions', color=T()['cats']['Utilities']))
    col.addWidget(table)
    col.addWidget(section_title('Handy formulas', color=T()['cats']['Hydraulic']))
    card = Card(padding=14, spacing=0)
    for name, formula in FORMULA_REF:
        r = hbox(None, (8, 9, 8, 9), 14)
        r.addWidget(label(name, 'muted'), 1)
        r.addWidget(label(formula, 'mono', selectable=True))
        card.body.addLayout(r)
    col.addWidget(card)
    col.addStretch(1)
    return page


# =========================================================================== seals
def seals_page(win):
    t = T()
    page = ScrollPage(max_width=1100)
    col = page.col
    col.addWidget(page_header('Hydraulic Seal Compatibility', blurb_of('Seal Compatibility'), 'Hydraulic'))

    fluids = list(SEAL_MATRIX)
    start = getattr(win, 'seal_fluid', fluids[0])
    seg = Segmented(fluids, start if start in fluids else fluids[0])
    bar = hbox(None, (0, 0, 0, 0), 14)
    bar.addWidget(label('Fluid family', 'muted'))
    bar.addWidget(seg)
    bar.addStretch(1)
    for text, kind in (('Compatible', 'Good'), ('Conditional', 'Warn'), ('Unsuitable', 'Bad'), ('No data', 'Muted')):
        bar.addWidget(Pill(text, kind))
    col.addLayout(bar)

    table = QTableWidget(0, 3)
    table.setHorizontalHeaderLabels(['SEAL MATERIAL', 'COMPATIBILITY', 'NOTES AND LIMITS'])
    style_table(table, 60)
    table.horizontalHeader().setSectionResizeMode(0, table.horizontalHeader().ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, table.horizontalHeader().ResizeMode.ResizeToContents)
    table.setWordWrap(True)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
    palette = {'good': (t['good_soft'], t['good']), 'conditional': (t['warn_soft'], t['warn']),
               'bad': (t['bad_soft'], t['bad']), 'unknown': (t['raised'], t['muted'])}

    def fill(fluid):
        win.seal_fluid = fluid
        rows = SEAL_MATRIX[fluid]
        table.setRowCount(len(rows))
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
                table.setItem(i, c, item)
        fit_table_height(table)

    seg.changed.connect(fill)
    fill(seg.current)
    col.addWidget(table)
    col.addWidget(Banner('warn', 'Compatibility depends on the exact polymer compound, fluid additives, temperature, '
                                 'pressure, speed and seal construction. These ratings are not approvals.'))
    col.addStretch(1)
    return page


# =========================================================================== methodology
def methodology_page(win):
    t = T()
    page = ScrollPage(max_width=1000)
    col = page.col
    col.addWidget(page_header('Methodology', blurb_of('Methodology') + ' Every number in Caldera is an estimate: '
                              'check inputs, units and applicable standards.', 'Utilities'))
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
