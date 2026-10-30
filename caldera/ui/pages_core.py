"""Dashboard and calculator pages."""
from datetime import datetime

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtWidgets import (QApplication, QBoxLayout, QGridLayout, QMenu, QPlainTextEdit, QTableWidget,
                               QTableWidgetItem, QWidget, QFrame)
from PySide6.QtGui import QColor

from .. import units
from ..registry import TOOLS
from ..toolmeta import (CATEGORIES, CHOICE_ALIASES, FORMULAS, NOTES, DEFAULT_NOTE, blurb_of, category_of, evaluate,
                        format_metric, icon_of, is_toggle, parse_number, split_label, status_kind, sweep_all)
from . import icons
from .kit import (ClickRow, IconTile, ago, fit_table_height, page_header, section_title, stat_card, tool_card)
from .theme import current as T
from .widgets import (Banner, Card, Combo, Field, HeroMetric, MetricTile, ScrollPage, SweepChart, Tick, button, eyebrow,
                      get_value, hbox, icon_button, icon_label, label, set_value, style_table, vbox)


# =========================================================================== overview
def overview_page(win):
    t = T()
    page = ScrollPage()
    col = page.col
    hour = datetime.now().hour
    greeting = 'Good morning' if hour < 12 else ('Good afternoon' if hour < 18 else 'Good evening')

    head = hbox(None, (0, 0, 0, 0), 12)
    left = vbox(None, (0, 0, 0, 0), 4)
    left.addWidget(eyebrow(datetime.now().strftime('%A, %B %d')))
    left.addWidget(label(greeting, 'display'))
    left.addWidget(label('Your offline engineering workbench. Every calculation stays on this machine.', 'muted'))
    head.addLayout(left, 1)
    head.addWidget(button('Jump to anything', 'primary', 'search', win.open_palette), 0, Qt.AlignmentFlag.AlignTop)
    col.addLayout(head)

    history = win.data.get('history', [])
    favourites = [n for n in win.data.get('favorites', []) if n in TOOLS]
    stats = hbox(None, (0, 0, 0, 0), 16)
    stats.addWidget(stat_card('calculator', 'Calculators', len(TOOLS), t['cats']['Hydraulic']), 1)
    stats.addWidget(stat_card('folder', 'Projects', len(win.data['projects']), t['cats']['Mechanical']), 1)
    stats.addWidget(stat_card('bookmark', 'Saved results', len(history), t['cats']['Electrical']), 1)
    stats.addWidget(stat_card('star', 'Pinned tools', len(favourites), t['cats']['Pneumatic']), 1)
    col.addLayout(stats)

    # ---- recent activity + quick actions
    row = hbox(None, (0, 0, 0, 0), 16)
    recent = Card(padding=18, spacing=6)
    link = button('View all (%d)' % len(history) if history else 'View all', 'ghost', None,
                  lambda: win.navigate('Calculation History'))
    recent.body.addWidget(section_title('Recent activity', 'latest 3' if len(history) > 3 else '', right=link))
    if not history:
        empty = vbox(None, (0, 18, 0, 18), 8)
        empty.addWidget(icon_label('history', t['faint'], 30), 0, Qt.AlignmentFlag.AlignHCenter)
        l1 = label('Nothing saved yet', 'h3')
        l1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        l2 = label('Open any calculator and choose “Save to project” to build your history.', 'faint', wrap=True)
        l2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        empty.addWidget(l1)
        empty.addWidget(l2)
        recent.body.addLayout(empty)
    for rec in reversed(history[-3:]):
        tool = rec.get('tool', '')
        color = t['cats'][category_of(tool)]
        r = ClickRow()
        r.body.addWidget(IconTile(icon_of(tool), color, 36))
        mid = vbox(None, (0, 0, 0, 0), 1)
        mid.addWidget(label(tool, 'h3'))
        headline = str(rec.get('result', '')).split('\n')[0]
        mid.addWidget(label('%s  ·  %s' % (rec.get('project', 'General'), headline), 'faint'))
        r.body.addLayout(mid, 1)
        r.body.addWidget(label(ago(rec.get('date', '')), 'faint'))
        r.seal()
        r.clicked.connect(lambda checked=False, n=tool: win.navigate(n) if n in TOOLS else win.navigate('Calculation History'))
        recent.body.addWidget(r)
    recent.body.addStretch(1)
    row.addWidget(recent, 3)

    quick = Card(padding=18, spacing=4)
    quick.body.addWidget(section_title('Quick actions'))
    for text, icon_name, fn in [('Browse every calculator', 'search', win.open_palette),
                                ('Start a new project', 'plus', win.new_project),
                                ('Back up this workspace', 'download', win.export_data),
                                ('Change appearance', 'sliders', lambda: win.navigate('Settings'))]:
        r = ClickRow()
        r.body.addWidget(IconTile(icon_name, t['accent'], 34))
        r.body.addWidget(label(text, 'h3'), 1)
        r.body.addWidget(icon_label('chevron_right', t['faint'], 14))
        r.seal()
        r.clicked.connect(lambda checked=False, f=fn: f())
        quick.body.addWidget(r)
    quick.body.addStretch(1)
    row.addWidget(quick, 2)
    col.addLayout(row)

    def grid_of(names, color):
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for i, n in enumerate(names):
            grid.addWidget(tool_card(n, icon_of(n), color, blurb_of(n), lambda n=n: win.navigate(n),
                                     n in win.data.get('favorites', [])), i // 3, i % 3)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        return grid

    if favourites:
        col.addWidget(section_title('Pinned', '%d tool%s' % (len(favourites), '' if len(favourites) == 1 else 's'),
                                    t['warn']))
        col.addLayout(grid_of(favourites, t['warn']))
    for cat, names in CATEGORIES.items():
        col.addWidget(section_title(cat, '%d tools' % len(names), t['cats'][cat]))
        col.addLayout(grid_of(names, t['cats'][cat]))
    col.addStretch(1)
    return page


# =========================================================================== calculator
class CalculatorPage(ScrollPage):
    """Generic live calculator. Tool-specific pages subclass it and override build_inputs / build_right_top /
    after_recalc."""

    def __init__(self, win, name):
        super().__init__(max_width=1240)
        self.win, self.name = win, name
        self.specs, self.fn = TOOLS[name]
        self.inputs = []
        self.result = self.canon = None
        self._result_widget = None
        self._sweeps, self._chart_inputs = {}, []
        t = T()
        cat = category_of(name)
        draft = win.data['drafts'].get(name, [])
        if len(draft) != len(self.specs):          # layout changed since the draft was saved
            draft = []
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self.recalc)

        # ---- header
        self.fav_btn = icon_button('star', '', lambda: win.toggle_favorite(name), 38)
        self.on_fav_changed()
        col = self.col
        col.addWidget(page_header(name, blurb_of(name), cat,
                                  [self.fav_btn, button('Methodology', 'ghost', 'sigma', lambda: win.open_methodology(name))]))
        self.cols = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.cols.setSpacing(20)
        col.addLayout(self.cols)
        left = vbox(None, (0, 0, 0, 0), 16)
        right = vbox(None, (0, 0, 0, 0), 16)
        self.cols.addLayout(left, 5)
        self.cols.addLayout(right, 6)

        # ---- inputs
        card = Card(padding=20, spacing=16)
        card.body.addWidget(section_title('Inputs', right=label('↑ ↓ to step', 'faint')))
        self.build_inputs(card, draft)
        card.body.addWidget(self._divider())
        foot = hbox(None, (0, 0, 0, 0), 8)
        self.presets_btn = button('Presets', 'ghost', 'bookmark', self.show_presets)
        foot.addWidget(self.presets_btn)
        foot.addWidget(button('Reset', 'ghost', 'reset', self.reset_inputs))
        foot.addStretch(1)
        card.body.addLayout(foot)
        left.addWidget(card)

        # ---- how it is calculated
        method = Card(padding=20, spacing=12)
        method.body.addWidget(section_title('How it’s calculated'))
        box = QFrame()
        box.setObjectName('tile')
        bl = vbox(box, (16, 14, 16, 14), 6)
        for line in FORMULAS.get(name, []):
            bl.addWidget(label(line, 'mono', selectable=True))
        method.body.addWidget(box)
        method.body.addWidget(label(NOTES.get(name, DEFAULT_NOTE), 'faint', wrap=True))
        left.addWidget(method)
        left.addStretch(1)

        # ---- results
        self.build_right_top(right)
        head = hbox(None, (0, 0, 0, 0), 8)
        head.addWidget(section_title('Result'), 1)
        self.copy_btn = button('Copy', 'ghost', 'copy', self.copy_result)
        self.save_btn = button('Save to project', 'primary', 'bookmark', self.save_result)
        head.addWidget(self.copy_btn)
        head.addWidget(self.save_btn)
        right.addLayout(head)
        host = QWidget()
        self.result_lay = vbox(host, (0, 0, 0, 0), 0)
        right.addWidget(host)

        notes = Card(padding=18, spacing=8)
        notes.body.addWidget(section_title('Notes', 'saved with the result'))
        self.note_edit = QPlainTextEdit(win.data.get('note_drafts', {}).get(name, ''))
        self.note_edit.setPlaceholderText('Customer, job number, assumptions, why these inputs… '
                                          '“Save to project” stores this note with the result.')
        self.note_edit.setFixedHeight(84)
        self.note_edit.textChanged.connect(self._note_changed)
        notes.body.addWidget(self.note_edit)
        right.addWidget(notes)

        self.chart_card = Card(padding=20, spacing=12)
        self.chart_card.body.addWidget(section_title('Sensitivity', 'where the result curves as one input changes ±50 %'))
        ctl = hbox(None, (0, 0, 0, 0), 10)
        ctl.addWidget(label('Vary', 'muted'))
        self.in_combo = Combo()
        self.out_combo = Combo()
        ctl.addWidget(self.in_combo, 1)
        ctl.addWidget(label('Watch', 'muted'))
        ctl.addWidget(self.out_combo, 1)
        self.chart_card.body.addLayout(ctl)
        self.chart = SweepChart()
        self.chart_card.body.addWidget(self.chart)
        self.in_combo.currentIndexChanged.connect(lambda _i: self._on_in_changed())
        self.out_combo.currentIndexChanged.connect(lambda _i: self.update_chart())
        right.addWidget(self.chart_card)
        right.addStretch(1)
        self.recalc()

    # ------------------------------------------------------------------ input building (overridable)
    def make_input(self, i, lbl, default, draft):
        """Create the widget for spec #i. Returns (caption or None, widget)."""
        have = i < len(draft)
        if is_toggle(default):
            on = (draft[i] if have and draft[i] in default else default.default) == 'Yes'
            w = Tick(lbl, on)
            w.toggled.connect(lambda _b: self.schedule())
            caption = None
        elif isinstance(default, list):
            w = Combo(default, self.choice_labels(i, default))
            saved = CHOICE_ALIASES.get(draft[i], draft[i]) if have else None
            w.set_value(saved if saved in default else str(getattr(default, 'default', None) or default[0]))
            w.currentIndexChanged.connect(lambda _i: self.schedule())
            caption = lbl
        else:
            nm, unit = split_label(lbl)
            w = Field(draft[i] if have else default, unit, quantity=(nm, unit))
            w.changed.connect(self.schedule)
            caption = nm
        self.inputs.append(w)
        return caption, w

    def choice_labels(self, i, default):
        """Hook: visible labels for a choice input (None = show the stored values as-is)."""
        return None

    def input_cell(self, i, lbl, default, draft):
        wrap = QWidget()
        v = vbox(wrap, (0, 0, 0, 0), 6)
        caption, w = self.make_input(i, lbl, default, draft)
        if caption:
            v.addWidget(label(caption, 'muted'))
        v.addWidget(w)
        return wrap

    def build_inputs(self, card, draft):
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for i, (lbl, default) in enumerate(self.specs):
            grid.addWidget(self.input_cell(i, lbl, default, draft), i // 2, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)

    def build_right_top(self, right):
        """Hook: extra cards above the result (e.g. a 3D preview)."""

    def after_recalc(self):
        """Hook: called after every successful or failed recalculation."""

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _divider():
        d = QFrame()
        d.setObjectName('divider')
        d.setFixedHeight(1)
        return d

    def on_fav_changed(self):
        t = T()
        fav = self.win.is_favorite(self.name)
        self.fav_btn.setIcon(icons.icon('star', t['warn'] if fav else t['muted'], 18, fav))
        self.fav_btn.setToolTip('Unpin from sidebar' if fav else 'Pin to sidebar')

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        narrow = self.viewport().width() < 980
        direction = QBoxLayout.Direction.TopToBottom if narrow else QBoxLayout.Direction.LeftToRight
        if self.cols.direction() != direction:
            self.cols.setDirection(direction)

    def values(self):
        return [get_value(w) for w in self.inputs]

    def schedule(self):
        self._timer.start()

    # ------------------------------------------------------------------ calculation
    def recalc(self):
        values = self.values()
        self.win.data['drafts'][self.name] = values
        self.win.schedule_save()
        for w in self.inputs:
            if isinstance(w, Field):
                try:
                    parse_number(w.text())
                    w.set_invalid(False)
                except ValueError:
                    w.set_invalid(True)
        canon = evaluate(self.name, self.fn, self.specs, values, self.win.precision)
        self.canon = canon
        self.result = res = units.localize_result(canon)
        self.save_btn.setEnabled(not res.error)
        self.copy_btn.setEnabled(not res.error)
        new = self._build_result(res)
        self.result_lay.addWidget(new)
        if self._result_widget is not None:
            self.result_lay.removeWidget(self._result_widget)
            self._result_widget.setParent(None)
            self._result_widget.deleteLater()
        self._result_widget = new
        self._refresh_chart(canon, values)
        self.after_recalc()

    def _build_result(self, res):
        t = T()
        p = self.win.precision
        w = QWidget()
        lay = vbox(w, (0, 0, 0, 0), 12)
        if res.error:
            lay.addWidget(Banner('bad', res.error))
            return w
        for ok, text in res.status:
            lay.addWidget(Banner(status_kind(ok), text))
        if res.metrics:
            hero = res.metrics[res.hero]
            lay.addWidget(HeroMetric(hero.label, format_metric(hero, p), hero.unit, icon_of(self.name)))
            others = [m for i, m in enumerate(res.metrics) if i != res.hero]
            if others:
                grid = QGridLayout()
                grid.setHorizontalSpacing(12)
                grid.setVerticalSpacing(12)
                for k, m in enumerate(others):
                    tip = '%.10g' % m.value if m.kind == 'num' else ''
                    grid.addWidget(MetricTile(m.label, format_metric(m, p), m.unit, tip), k // 2, k % 2)
                grid.setColumnStretch(0, 1)
                grid.setColumnStretch(1, 1)
                lay.addLayout(grid)
        elif res.raw_text:
            card = Card(padding=18)
            card.body.addWidget(label(res.raw_text, 'mono', wrap=True, selectable=True))
            lay.addWidget(card)
        if res.table:
            headers, rows = res.table
            table = QTableWidget(len(rows), len(headers))
            table.setHorizontalHeaderLabels(headers)
            style_table(table, 40)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    if r == 0:
                        item.setBackground(QColor(t['accent_soft']))
                    table.setItem(r, c, item)
            fit_table_height(table)
            lay.addWidget(table)
        for note in res.notes:
            lay.addWidget(label(note, 'faint', wrap=True))
        return w

    # ------------------------------------------------------------------ sensitivity chart
    # Only shown where a result genuinely curves. Straight-line relationships (y = k·x) teach nothing, so any input /
    # output pair that is linear is left out, and the whole card disappears when nothing is left.
    def _refresh_chart(self, res, values):
        self._sweeps = {}
        if res and not res.error and res.sweepable and res.numeric():
            self._sweeps = sweep_all(self.name, self.fn, self.specs, values)
        usable = [i for i, s in self._sweeps.items() if s['nonlinear']]
        self._chart_inputs = usable
        self.chart_card.setVisible(bool(usable))
        if not usable:
            return
        previous = self.in_combo.currentText()
        names = [split_label(self.specs[i][0])[0] for i in usable]
        self.in_combo.blockSignals(True)
        self.in_combo.clear()
        self.in_combo.addItems(names)
        self.in_combo.setCurrentText(previous if previous in names else names[0])
        self.in_combo.blockSignals(False)
        self._fill_outputs()
        self.update_chart()

    def _selected_input(self):
        row = self.in_combo.currentIndex()
        return self._chart_inputs[row] if 0 <= row < len(self._chart_inputs) else None

    def _fill_outputs(self):
        idx = self._selected_input()
        if idx is None:
            return
        keys = self._sweeps[idx]['nonlinear']
        canon = self.canon
        hero = canon.metrics[canon.hero] if canon and canon.metrics else None
        hero_key = '%s (%s)' % (hero.label, hero.unit) if hero and hero.unit else (hero.label if hero else '')
        previous = self.out_combo.value() if self.out_combo.count() else ''
        self.out_combo.blockSignals(True)
        self.out_combo.clear()
        for k in keys:
            self.out_combo.addItem(self._display_key(k), k)
        self.out_combo.set_value(previous if previous in keys else (hero_key if hero_key in keys else keys[0]))
        self.out_combo.blockSignals(False)

    def _on_in_changed(self):
        self._fill_outputs()
        self.update_chart()

    @staticmethod
    def _display_key(key):
        nm, unit = split_label(key)
        return '%s (%s)' % (nm, units.display_unit(nm, unit)) if unit else nm

    def update_chart(self):
        idx = self._selected_input()
        if idx is None or self.canon is None or self.canon.error:
            return
        key = self.out_combo.value()
        sweep = self._sweeps.get(idx)
        if not sweep or key not in sweep['series']:
            return
        try:
            v0 = parse_number(self.values()[idx])
        except ValueError:
            return
        cur = None
        for m in self.canon.metrics:
            if m.kind == 'num' and ('%s (%s)' % (m.label, m.unit) if m.unit else m.label) == key:
                cur = m.value
        in_name, in_unit = split_label(self.specs[idx][0])
        out_name, out_unit = split_label(key)
        xs = [units.to_display(in_name, in_unit, x) for x in sweep['xs']]
        ys = [units.to_display(out_name, out_unit, y) for y in sweep['series'][key]]
        if cur is not None:
            cur = (units.to_display(in_name, in_unit, v0), units.to_display(out_name, out_unit, cur))
        xlabel = self._display_key(self.specs[idx][0])
        self.chart.set_data(xs, ys, cur, xlabel, self._display_key(key), self.win.precision)

    # ------------------------------------------------------------------ actions
    def commit(self):
        """Ctrl+Enter: recalculate immediately and honour the auto-save setting."""
        self._timer.stop()
        self.recalc()
        if self.win.data.get('auto_save', False):
            self.save_result()
        else:
            self.win.toast('Recalculated', 'info')

    def result_text(self):
        return self.result.as_text(self.win.precision) if self.result and not self.result.error else ''

    def _note_changed(self):
        self.win.data.setdefault('note_drafts', {})[self.name] = self.note_edit.toPlainText()
        self.win.schedule_save()

    def save_result(self):
        text = self.result_text()
        if text:
            self.win.add_history(self.name, self.values(), text, self.note_edit.toPlainText())

    def copy_result(self):
        text = self.result_text()
        if text:
            QApplication.clipboard().setText(text)
            self.win.toast('Result copied to clipboard')

    def reset_inputs(self):
        self.win.data['drafts'].pop(self.name, None)
        for w, (_lbl, default) in zip(self.inputs, self.specs):
            if isinstance(default, list):
                set_value(w, getattr(default, 'default', None) or default[0])
            else:
                set_value(w, default)
        self.recalc()
        self.win.toast('Inputs reset to defaults', 'info')

    # ------------------------------------------------------------------ presets
    def show_presets(self):
        presets = self.win.data['presets'].get(self.name, {})
        menu = QMenu(self)
        for n in presets:
            menu.addAction(n).triggered.connect(lambda checked=False, n=n: self.load_preset(n))
        if presets:
            menu.addSeparator()
        menu.addAction('Save current inputs as preset…').triggered.connect(self.save_preset)
        if presets:
            sub = menu.addMenu('Delete preset')
            for n in presets:
                sub.addAction(n).triggered.connect(lambda checked=False, n=n: self.delete_preset(n))
        menu.exec(self.presets_btn.mapToGlobal(QPoint(0, self.presets_btn.height() + 4)))

    def save_preset(self):
        name = self.win.ask_text('Save preset', 'Preset name:')
        if name:
            self.win.data['presets'].setdefault(self.name, {})[name] = self.values()
            self.win.save()
            self.win.toast('Preset “%s” saved' % name)

    def load_preset(self, name):
        values = self.win.data['presets'].get(self.name, {}).get(name)
        if not values or len(values) != len(self.inputs):
            self.win.toast('That preset was saved for an older layout of this tool', 'warn')
            return
        for w, v in zip(self.inputs, values):
            set_value(w, v)
        self.recalc()
        self.win.toast('Loaded preset “%s”' % name, 'info')

    def delete_preset(self, name):
        self.win.data['presets'].get(self.name, {}).pop(name, None)
        self.win.save()
        self.win.toast('Preset deleted', 'info')


def calculator_page(win, name):
    if name == 'Conduit Fill':
        from .page_conduit import ConduitPage
        return ConduitPage(win, name)
    if name == 'Hydraulic Cylinder Cycle Time':
        from .page_cylinder import CylinderCyclePage
        return CylinderCyclePage(win, name)
    if name == 'Reservoir / Drip Pan':
        from .page_tank import ReservoirPage     # imported here: page_tank subclasses CalculatorPage
        return ReservoirPage(win, name)
    return CalculatorPage(win, name)
