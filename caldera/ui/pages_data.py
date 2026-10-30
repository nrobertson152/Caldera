"""History, projects and comparison pages."""
import copy
from datetime import datetime

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QLineEdit, QMenu, QPlainTextEdit, QTableWidget,
                               QTableWidgetItem, QWidget)

from ..registry import TOOLS
from .. import units
from ..toolmeta import category_of, icon_of, parse_number, split_label
from . import icons
from .kit import IconTile, clear_layout, fit_table_height, page_header, section_title
from .theme import current as T
from .widgets import (Banner, Card, Combo, Pill, ScrollPage, button, eyebrow, hbox, icon_button, icon_label, label,
                      style_table, vbox, Tick)


def fmt_date(iso, long=False):
    try:
        d = datetime.fromisoformat(str(iso))
    except ValueError:
        return str(iso)
    return d.strftime('%b %d, %Y  %H:%M' if long else '%b %d, %H:%M')


def empty_state(icon_name, title, text, action=None):
    t = T()
    c = Card(padding=40, spacing=8)
    c.body.addWidget(icon_label(icon_name, t['faint'], 36), 0, Qt.AlignmentFlag.AlignHCenter)
    a = label(title, 'h2')
    a.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    b = label(text, 'muted', wrap=True)
    b.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    c.body.addWidget(a)
    c.body.addWidget(b)
    if action is not None:
        c.body.addSpacing(8)
        c.body.addWidget(action, 0, Qt.AlignmentFlag.AlignHCenter)
    return c


# =========================================================================== history
class HistoryPage(ScrollPage):
    def __init__(self, win):
        super().__init__(max_width=1280)
        self.win = win
        self.indices = []
        self.selected = None
        col = self.col
        col.addWidget(page_header('Calculation History', 'Every saved result, across all projects.', None, [
            button('Export CSV', '', 'download', win.export_history),
            button('Export XLSX', '', 'table', win.export_history_xlsx)]))
        if not win.data['history']:
            col.addWidget(empty_state('history', 'No saved calculations yet',
                                      'Open any calculator and choose “Save to project”. Results land here, grouped by project.',
                                      button('Browse calculators', 'primary', 'search', win.open_palette)))
            col.addStretch(1)
            return
        bar = hbox(None, (0, 0, 0, 0), 12)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Filter by tool, project, value or note…')
        self.search.setClearButtonEnabled(True)
        self.search.setFixedHeight(40)
        self.search.textChanged.connect(lambda _t: self.populate())
        projects = list(win.data['projects'])
        for r in win.data['history']:
            if r.get('project') and r.get('project') not in projects:
                projects.append(r['project'])
        self.proj = Combo(['All projects'] + projects)
        wanted = getattr(win, 'history_project', 'All projects')
        self.proj.setCurrentText(wanted if wanted in ['All projects'] + projects else 'All projects')
        self.proj.currentTextChanged.connect(self._proj_changed)
        self.proj.setMinimumWidth(190)
        self.count = label('', 'faint')
        bar.addWidget(self.search, 1)
        bar.addWidget(self.proj)
        bar.addWidget(self.count)
        col.addLayout(bar)

        split = hbox(None, (0, 0, 0, 0), 16)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['WHEN', 'TOOL', 'PROJECT', 'RESULT'])
        style_table(self.table, 46)
        self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, self.table.horizontalHeader().ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, self.table.horizontalHeader().ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setMinimumHeight(520)
        self.table.itemSelectionChanged.connect(self._on_select)
        split.addWidget(self.table, 3)
        self.detail = Card(padding=20, spacing=12)
        self.detail.setMinimumWidth(340)
        self.detail.setMaximumWidth(430)
        self.detail_lay = vbox(None, (0, 0, 0, 0), 12)
        self.detail.body.addLayout(self.detail_lay)
        split.addWidget(self.detail, 2, Qt.AlignmentFlag.AlignTop)
        col.addLayout(split)
        col.addStretch(1)
        self.populate()

    def _proj_changed(self, text):
        self.win.history_project = text
        self.populate()

    # ------------------------------------------------------------------ table
    def populate(self, select=None):
        rows = self.win.data['history']
        needle = self.search.text().strip().casefold()
        project = self.proj.currentText()
        order = sorted(range(len(rows)), key=lambda i: (0 if rows[i].get('pinned') else 1, -i))
        self.indices = []
        for i in order:
            r = rows[i]
            if project != 'All projects' and r.get('project') != project:
                continue
            hay = ' '.join([str(r.get('tool', '')), str(r.get('project', '')), str(r.get('result', '')),
                            str(r.get('note', ''))]).casefold()
            if needle and needle not in hay:
                continue
            self.indices.append(i)
        t = T()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.indices))
        for row, i in enumerate(self.indices):
            r = rows[i]
            tool = str(r.get('tool', ''))
            when = QTableWidgetItem(fmt_date(r.get('date', '')))
            name = QTableWidgetItem(tool)
            name.setData(Qt.ItemDataRole.UserRole, i)
            if r.get('pinned'):
                name.setIcon(icons.icon('star', t['warn'], 14, True))
            headline = str(r.get('result', '')).split('\n')[0]
            if r.get('note'):
                headline = '✎ ' + headline
            for c, item in enumerate((when, name, QTableWidgetItem(str(r.get('project', 'General'))),
                                      QTableWidgetItem(headline))):
                if c in (0, 2):
                    item.setForeground(QColor(t['muted']))
                self.table.setItem(row, c, item)
        self.table.blockSignals(False)
        self.count.setText('%d of %d' % (len(self.indices), len(rows)))
        target = None
        if select is not None and select in self.indices:
            target = self.indices.index(select)
        elif self.selected in self.indices:
            target = self.indices.index(self.selected)
        elif self.indices:
            target = 0
        if target is not None:
            self.table.selectRow(target)
        self._on_select()

    def _on_select(self):
        items = self.table.selectedItems()
        if not items:
            self.selected = None
            self.render_detail(None)
            return
        row = items[0].row()
        if 0 <= row < len(self.indices):
            self.selected = self.indices[row]
            self.render_detail(self.selected)

    # ------------------------------------------------------------------ detail pane
    def render_detail(self, idx):
        clear_layout(self.detail_lay)
        t = T()
        if idx is None:
            self.detail_lay.addWidget(label('Select a result to see its inputs and actions.', 'muted', wrap=True))
            return
        rec = self.win.data['history'][idx]
        tool = str(rec.get('tool', ''))
        cat = category_of(tool)
        head = hbox(None, (0, 0, 0, 0), 12)
        head.addWidget(IconTile(icon_of(tool), t['cats'].get(cat, t['accent']), 42), 0, Qt.AlignmentFlag.AlignTop)
        titles = vbox(None, (0, 0, 0, 0), 2)
        e = eyebrow(cat)
        e.setStyleSheet('color: %s;' % t['cats'].get(cat, t['faint']))
        titles.addWidget(e)
        titles.addWidget(label(tool, 'h2', wrap=True))
        head.addLayout(titles, 1)
        self.detail_lay.addLayout(head)
        pills = hbox(None, (0, 0, 0, 0), 6)
        pills.addWidget(Pill(str(rec.get('project', 'General'))))
        pills.addWidget(Pill(fmt_date(rec.get('date', ''), True), 'Muted'))
        if rec.get('pinned'):
            pills.addWidget(Pill('Pinned', 'Warn'))
        pills.addStretch(1)
        self.detail_lay.addLayout(pills)

        specs = TOOLS.get(tool, ([], None))[0]
        inputs = rec.get('inputs') or []
        if specs and inputs and len(specs) == len(inputs):
            self.detail_lay.addWidget(eyebrow('Inputs'))
            grid = QGridLayout()
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(5)
            for k, ((lbl, _d), value) in enumerate(zip(specs, inputs)):
                nm, unit = split_label(lbl)
                shown = str(value)
                if not isinstance(_d, list) and units.convertible(nm, unit):
                    try:
                        shown = units.num_text(units.to_display(nm, unit, parse_number(value)))
                    except ValueError:
                        pass
                    unit = units.display_unit(nm, unit)
                grid.addWidget(label(nm, 'muted'), k, 0)
                cell = label(('%s %s' % (shown, '' if isinstance(_d, list) else unit)).strip(), wrap=True)
                cell.setAlignment(Qt.AlignmentFlag.AlignRight)
                grid.addWidget(cell, k, 1)
            grid.setColumnStretch(0, 1)
            self.detail_lay.addLayout(grid)
        self.detail_lay.addWidget(eyebrow('Note'))
        note = QPlainTextEdit(str(rec.get('note', '')))
        note.setPlaceholderText('Add a note to this result…')
        note.setFixedHeight(76)
        note.textChanged.connect(lambda: self._note_changed(idx, note.toPlainText()))
        self.detail_lay.addWidget(note)
        self.detail_lay.addWidget(eyebrow('Result'))
        box = QFrame()
        box.setObjectName('tile')
        bl = vbox(box, (14, 12, 14, 12), 0)
        bl.addWidget(label(str(rec.get('result', '')), 'mono', wrap=True, selectable=True))
        self.detail_lay.addWidget(box)

        if tool in TOOLS:
            self.detail_lay.addWidget(button('Open in calculator', 'primary', 'calculator',
                                             lambda: self.win.open_with_inputs(tool, inputs)))
        row = hbox(None, (0, 0, 0, 0), 8)
        row.addWidget(button('Copy', '', 'copy', lambda: self._copy(rec)), 1)
        row.addWidget(button('Unpin' if rec.get('pinned') else 'Pin', '', 'pin', lambda: self._toggle_pin(idx)), 1)
        self.detail_lay.addLayout(row)
        row2 = hbox(None, (0, 0, 0, 0), 8)
        self.move_btn = button('Move…', '', 'folder', lambda: self._move_menu(idx))
        row2.addWidget(self.move_btn, 1)
        row2.addWidget(button('Duplicate', '', 'copy', lambda: self._duplicate(idx)), 1)
        self.detail_lay.addLayout(row2)
        self.detail_lay.addWidget(button('Delete', 'danger', 'trash', lambda: self._delete(idx)))

    # ------------------------------------------------------------------ actions
    def _note_changed(self, idx, text):
        rec = self.win.data['history'][idx]
        if text.strip():
            rec['note'] = text
        else:
            rec.pop('note', None)
        self.win.schedule_save()
        for row, i in enumerate(self.indices):          # keep the ✎ marker in the list in step
            if i == idx and self.table.item(row, 3):
                head = str(rec.get('result', '')).split('\n')[0]
                self.table.item(row, 3).setText(('✎ ' + head) if rec.get('note') else head)

    def _copy(self, rec):
        text = str(rec.get('result', ''))
        if rec.get('note'):
            text += '\n\nNote: ' + str(rec['note'])
        QApplication.clipboard().setText(text)
        self.win.toast('Result copied to clipboard')

    def _toggle_pin(self, idx):
        rec = self.win.data['history'][idx]
        rec['pinned'] = not rec.get('pinned', False)
        self.win.save()
        self.populate(select=idx)

    def _duplicate(self, idx):
        rows = self.win.data['history']
        clone = copy.deepcopy(rows[idx])
        clone['date'] = datetime.now().isoformat(timespec='seconds')
        rows.append(clone)
        self.win.save()
        self.populate(select=len(rows) - 1)
        self.win.toast('Duplicated')

    def _move_menu(self, idx):
        menu = QMenu(self)
        current = self.win.data['history'][idx].get('project')
        for name in self.win.data['projects']:
            act = menu.addAction(name)
            act.setEnabled(name != current)
            act.triggered.connect(lambda checked=False, n=name: self._move(idx, n))
        menu.exec(self.move_btn.mapToGlobal(QPoint(0, self.move_btn.height() + 4)))

    def _move(self, idx, project):
        self.win.data['history'][idx]['project'] = project
        self.win.save()
        self.populate(select=idx)
        self.win.toast('Moved to %s' % project)

    def _delete(self, idx):
        if not self.win.confirm('Delete result', 'Delete this saved calculation? This cannot be undone.'):
            return
        rows = self.win.data['history']
        rows.pop(idx)
        self.selected = None
        self.win.save()
        if not rows:
            self.win.open_page('Calculation History')
            return
        self.populate()
        self.win.toast('Deleted', 'info')


def history_page(win):
    return HistoryPage(win)


# =========================================================================== projects
def project_page(win):
    t = T()
    page = ScrollPage()
    col = page.col
    col.addWidget(page_header('Projects', 'Group saved calculations, keep notes, and export a PDF summary.', None, [
        button('Import project', '', 'upload', win.import_project),
        button('New project', 'primary', 'plus', win.new_project)]))

    flt = getattr(win, '_proj_filter', None)
    if flt is None:
        flt = win._proj_filter = {'q': '', 'active': False, 'notes': False, 'results': False, 'archived': True}

    bar = Card(padding=14, spacing=10)
    row = hbox(None, (0, 0, 0, 0), 12)
    search = QLineEdit()
    search.setPlaceholderText('Search projects by name or notes…')
    search.setClearButtonEnabled(True)
    search.setText(flt['q'])
    row.addWidget(search, 1)
    count = label('', 'faint')
    row.addWidget(count)
    bar.body.addLayout(row)
    ticks = hbox(None, (0, 0, 0, 0), 18)
    ticks.addWidget(label('Filters', 'faint'))
    boxes = {}
    for key, text in (('active', 'Active project only'), ('notes', 'Has notes'), ('results', 'Has saved results'),
                      ('archived', 'Show archived')):
        box = Tick(text, flt[key])
        boxes[key] = box
        ticks.addWidget(box)
    ticks.addStretch(1)
    reset = button('Clear filters', 'ghost', 'reset')
    ticks.addWidget(reset)
    bar.body.addLayout(ticks)
    col.addWidget(bar)

    results = vbox(None, (0, 0, 0, 0), 16)
    col.addLayout(results)
    col.addStretch(1)

    def render():
        clear_layout(results)
        active, history = win.data['active_project'], win.data['history']
        notes_map = win.data.get('project_notes', {})
        q = flt['q'].strip().lower()

        def keep(name):
            mine = [r for r in history if r.get('project') == name]
            note = str(notes_map.get(name, '')).strip()
            if q and q not in name.lower() and q not in note.lower():
                return False
            if flt['active'] and name != active:
                return False
            if flt['notes'] and not note:
                return False
            if flt['results'] and not mine:
                return False
            return True

        names = [n for n in win.data['projects'] if keep(n)]
        archived = [n for n in win.data.get('archived_projects', []) if keep(n)] if flt['archived'] else []
        total = len(win.data['projects']) + (len(win.data.get('archived_projects', [])) if flt['archived'] else 0)
        count.setText('%d of %d' % (len(names) + len(archived), total))

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        for i, name in enumerate(names):
            mine = [r for r in history if r.get('project') == name]
            is_active = name == active
            card = Card(padding=20, spacing=10)
            if is_active:
                card.setStyleSheet('QFrame#card { border: 1px solid %s; }' % t['accent_line'])
            top = hbox(None, (0, 0, 0, 0), 12)
            top.addWidget(IconTile('folder', t['accent'] if is_active else t['cats']['Utilities'], 42), 0,
                          Qt.AlignmentFlag.AlignTop)
            titles = vbox(None, (0, 0, 0, 0), 2)
            titles.addWidget(label(name, 'h2', wrap=True))
            last = fmt_date(mine[-1].get('date', '')) if mine else 'No activity yet'
            titles.addWidget(label('%d saved  ·  %s' % (len(mine), last), 'faint'))
            top.addLayout(titles, 1)
            if is_active:
                top.addWidget(Pill('Active'), 0, Qt.AlignmentFlag.AlignTop)
            card.body.addLayout(top)
            notes = str(notes_map.get(name, '')).strip()
            snippet = label(notes if notes else 'No notes. Use ⋯ → Edit notes to add context.',
                            'muted' if notes else 'faint', wrap=True)
            snippet.setMaximumHeight(60)
            card.body.addWidget(snippet)
            card.body.addStretch(1)
            actions = hbox(None, (0, 0, 0, 0), 8)
            if not is_active:
                actions.addWidget(button('Make active', '', 'check', lambda n=name: win.set_active_project(n)))
            actions.addWidget(button('History', 'ghost', 'history', lambda n=name: win.show_history_for(n)))
            actions.addStretch(1)
            more = icon_button('chevron_down', 'More actions', None, 34)
            more.clicked.connect(lambda checked=False, n=name, b=more: _project_menu(win, n, b))
            actions.addWidget(more)
            card.body.addLayout(actions)
            grid.addWidget(card, i // 2, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        if names:
            results.addLayout(grid)
        elif not archived:
            empty = Card(padding=28, spacing=6)
            empty.body.addWidget(label('No projects match', 'h2'))
            empty.body.addWidget(label('Try a different search or clear the filters.', 'muted'))
            results.addWidget(empty)

        if archived:
            results.addWidget(section_title('Archived', '%d project%s' % (len(archived), '' if len(archived) == 1 else 's')))
            box = Card(padding=12, spacing=4)
            for name in archived:
                r = hbox(None, (8, 4, 8, 4), 12)
                r.addWidget(icon_label('archive', t['faint'], 18))
                r.addWidget(label(name, 'h3'), 1)
                r.addWidget(button('Restore', 'ghost', 'reset', lambda n=name: win.restore_project(n)))
                box.body.addLayout(r)
            results.addWidget(box)

    def on_text(text):
        flt['q'] = text
        render()

    def on_tick(key):
        def fn(checked=False):
            flt[key] = boxes[key].isChecked()
            render()
        return fn

    def clear_all():
        flt.update({'q': '', 'active': False, 'notes': False, 'results': False, 'archived': True})
        search.setText('')
        for k, b in boxes.items():
            b.setChecked(flt[k])
        render()

    search.textChanged.connect(on_text)
    for k, b in boxes.items():
        b.toggled.connect(on_tick(k))
    reset.clicked.connect(lambda checked=False: clear_all())
    render()
    return page


def _project_menu(win, name, anchor):
    menu = QMenu(anchor)
    menu.addAction('Rename…').triggered.connect(lambda checked=False: win.rename_project(name))
    menu.addAction('Edit notes…').triggered.connect(lambda checked=False: win.edit_project_notes(name))
    menu.addAction('Export project (.caldera)…').triggered.connect(lambda checked=False: win.export_project(name))
    menu.addAction('Export PDF summary…').triggered.connect(lambda checked=False: win.export_project_pdf(name))
    menu.addSeparator()
    arch = menu.addAction('Archive project')
    arch.setEnabled(name != 'General')
    arch.triggered.connect(lambda checked=False: win.archive_project(name))
    menu.exec(anchor.mapToGlobal(QPoint(0, anchor.height() + 4)))


# =========================================================================== compare
def _parse_result(text):
    """'Label (unit): 1,234.5' lines -> {label: (display, float|None)} preserving order."""
    out = {}
    for line in str(text).split('\n'):
        if ': ' not in line:
            continue
        k, v = line.rsplit(': ', 1)
        try:
            num = float(v.replace(',', ''))
        except ValueError:
            num = None
        out[k.strip()] = (v.strip(), num)
    return out


def compare_page(win):
    t = T()
    page = ScrollPage()
    col = page.col
    rows = win.data['history']
    col.addWidget(page_header('Compare Calculations', 'Pick two or three saved results to see exactly what changed.',
                              'Utilities'))
    if not rows:
        col.addWidget(empty_state('compare', 'Nothing to compare yet',
                                  'Save two results from any calculator and they will show up here.',
                                  button('Browse calculators', 'primary', 'search', win.open_palette)))
        col.addStretch(1)
        return page
    labels = ['%d.  %s  ·  %s  ·  %s' % (i + 1, r.get('tool', ''), r.get('project', 'General'),
                                         fmt_date(r.get('date', ''))) for i, r in enumerate(rows)]
    NONE = '— none —'
    pick = hbox(None, (0, 0, 0, 0), 14)
    a = Combo(labels)
    b = Combo(labels)
    c = Combo([NONE] + labels)
    a.setCurrentIndex(max(len(rows) - 2, 0))
    b.setCurrentIndex(len(rows) - 1)
    c.setCurrentIndex(0)
    for tag, combo in (('A', a), ('B', b), ('C  (optional)', c)):
        wrap = vbox(None, (0, 0, 0, 0), 6)
        wrap.addWidget(eyebrow('Result ' + tag))
        wrap.addWidget(combo)
        pick.addLayout(wrap, 1)
    col.addLayout(pick)
    host = vbox(None, (0, 0, 0, 0), 16)
    col.addLayout(host)
    col.addStretch(1)

    def chosen():
        out = [('A', rows[a.currentIndex()]), ('B', rows[b.currentIndex()])]
        if c.currentIndex() > 0:
            out.append(('C', rows[c.currentIndex() - 1]))
        return out

    def render():
        clear_layout(host)
        picked = chosen()
        side = hbox(None, (0, 0, 0, 0), 16)
        for tag, rec in picked:
            card = Card(padding=18, spacing=8)
            head = hbox(None, (0, 0, 0, 0), 10)
            head.addWidget(Pill(tag))
            head.addWidget(label(str(rec.get('tool', '')), 'h3', wrap=True), 1)
            card.body.addLayout(head)
            card.body.addWidget(label(fmt_date(rec.get('date', ''), True) + '  ·  ' + str(rec.get('project', '')), 'faint'))
            if rec.get('note'):
                card.body.addWidget(label('Note: ' + str(rec['note']), 'muted', wrap=True))
            card.body.addWidget(label(str(rec.get('result', '')), 'mono', wrap=True, selectable=True))
            side.addWidget(card, 1)
        host.addLayout(side)

        parsed = [(tag, _parse_result(rec.get('result', ''))) for tag, rec in picked]
        base = parsed[0][1]
        shared = [k for k in base if all(k in p for _t, p in parsed[1:])]
        if not shared:
            host.addWidget(Banner('warn', 'These results share no common measurements, so there is nothing to diff.'))
            return
        others = parsed[1:]
        headers = ['MEASUREMENT'] + [tag for tag, _p in parsed]
        for tag, _p in others:
            headers += ['%s − A' % tag, '%s vs A' % tag]
        table = QTableWidget(len(shared), len(headers))
        table.setHorizontalHeaderLabels(headers)
        style_table(table, 42)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.horizontalHeader().setSectionResizeMode(0, table.horizontalHeader().ResizeMode.ResizeToContents)
        for r, key in enumerate(shared):
            da, na = base[key]
            cells = [(key, None), (da, None)] + [(p[key][0], None) for _t, p in others]
            for _tag, p in others:
                db, nb = p[key]
                delta_text, pct_text, color = '—', '—', None
                if na is not None and nb is not None:
                    delta = nb - na
                    delta_text = ('%+.6g' % delta) if delta else '0'
                    if na != 0:
                        pct_text = '%+.1f %%' % (delta / abs(na) * 100)
                    color = t['faint'] if delta == 0 else (t['good'] if delta > 0 else t['warn'])
                cells += [(delta_text, color), (pct_text, color)]
            for ci, (text, color) in enumerate(cells):
                item = QTableWidgetItem(str(text))
                if color:
                    item.setForeground(QColor(color))
                table.setItem(r, ci, item)
        fit_table_height(table)
        host.addWidget(section_title('What changed', 'relative to A'))
        host.addWidget(table)
        tools = {rec.get('tool') for _tag, rec in picked}
        if len(tools) == 1 and picked[0][1].get('tool') in TOOLS:
            specs = TOOLS[picked[0][1]['tool']][0]
            ins = [rec.get('inputs', []) for _tag, rec in picked]
            changed = []
            for k, s_ in enumerate(specs):
                vals = [str(i[k]) if k < len(i) else '' for i in ins]
                if len(set(vals)) > 1:
                    changed.append((split_label(s_[0]), vals))
            if changed:
                host.addWidget(section_title('Inputs that differ', 'saved values, US customary'))
                box = Card(padding=16, spacing=6)
                for (nm, unit), vals in changed:
                    row = hbox(None, (0, 0, 0, 0), 10)
                    row.addWidget(label('%s%s' % (nm, (' (%s)' % unit) if unit else ''), 'muted'), 1)
                    row.addWidget(label('  →  '.join(vals), 'h3'))
                    box.body.addLayout(row)
                host.addWidget(box)

    for combo in (a, b, c):
        combo.currentIndexChanged.connect(lambda _i: render())
    render()
    return page
