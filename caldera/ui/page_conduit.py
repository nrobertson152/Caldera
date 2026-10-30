"""Conduit Fill: an editable list of conductors (mixed sizes and insulations) instead of one size × count."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QWidget

from .. import conduit
from ..toolmeta import is_text, parse_number
from .pages_core import CalculatorPage
from .theme import current as T
from .widgets import Combo, Field, Tick, button, hbox, icon_button, label, vbox


class ConductorRow(QWidget):
    changed = Signal()
    remove = Signal(object)

    def __init__(self, qty=1, insulation='THHN / THWN-2', size='12', area=0.05):
        super().__init__()
        lay = hbox(self, (0, 0, 0, 0), 8)
        self.qty = Field(str(qty), 'qty')
        self.qty.setFixedWidth(92)
        self.qty.changed.connect(self.changed.emit)
        lay.addWidget(self.qty)
        lay.addWidget(label('×', 'muted'))
        self.size = Combo()
        self.size.setMinimumWidth(118)
        lay.addWidget(self.size, 2)
        self.area = Field('%g' % area, 'in²', quantity=('Area', 'in²'))
        self.area.changed.connect(self.changed.emit)
        lay.addWidget(self.area, 2)
        self.ins = Combo(conduit.INSULATION_TYPES)
        self.ins.set_value(insulation if insulation in conduit.INSULATION_TYPES else conduit.INSULATION_TYPES[0])
        lay.addWidget(self.ins, 3)
        lay.addWidget(icon_button('trash', 'Remove this conductor', lambda: self.remove.emit(self), 36))
        self._fill_sizes(size)
        self.ins.currentIndexChanged.connect(lambda _i: (self._fill_sizes(self.size.value()), self.changed.emit()))
        self.size.currentIndexChanged.connect(lambda _i: self.changed.emit())

    def _fill_sizes(self, keep):
        other = self.ins.value() == 'Other (enter area)'
        self.size.setVisible(not other)
        self.area.setVisible(other)
        if other:
            return
        sizes = [s for s in conduit.SIZES if s in conduit.INSULATIONS[self.ins.value()]]
        self.size.blockSignals(True)
        self.size.clear()
        for s in sizes:
            self.size.addItem(conduit.size_text(s), s)
        self.size.set_value(keep if keep in sizes else ('12' if '12' in sizes else sizes[0]))
        self.size.blockSignals(False)

    def entry(self):
        """(qty, insulation, size_or_None, area) or None when the quantity does not parse."""
        try:
            qty = int(round(parse_number(self.qty.text())))
        except ValueError:
            return None
        ins = self.ins.value()
        if ins == 'Other (enter area)':
            try:
                area = parse_number(self.area.value())
            except ValueError:
                return None
            return qty, ins, None, area
        size = self.size.value()
        return qty, ins, size, conduit.INSULATIONS[ins].get(size, 0)


class ConductorList(QWidget):
    """Editor for the conductor list. value() / set_value() speak conduit.format_rows text."""
    changed = Signal()

    def __init__(self, text=conduit.DEFAULT_ROWS):
        super().__init__()
        self.rows = []
        lay = vbox(self, (0, 0, 0, 0), 8)
        head = hbox(None, (2, 0, 2, 0), 8)
        for text_, stretch, width in (('Qty', 0, 92), ('', 0, 10), ('Size', 2, 0), ('Insulation', 3, 0), ('', 0, 36)):
            w = label(text_, 'faint')
            if width:
                w.setFixedWidth(width)
            head.addWidget(w, stretch)
        lay.addLayout(head)
        self.body = vbox(None, (0, 0, 0, 0), 8)
        lay.addLayout(self.body)
        foot = hbox(None, (0, 2, 0, 0), 8)
        foot.addWidget(button('Add conductor', 'ghost', 'plus', self._add_clicked))
        foot.addStretch(1)
        self.summary = label('', 'faint')
        foot.addWidget(self.summary)
        lay.addLayout(foot)
        self.set_value(text)

    def _add_clicked(self):
        last = self.rows[-1].entry() if self.rows else None
        if last:
            self._add(1, last[1], last[2] or '12', last[3])
        else:
            self._add()
        self._emit()

    def _add(self, qty=1, insulation='THHN / THWN-2', size='12', area=0.05):
        row = ConductorRow(qty, insulation, size, area)
        row.changed.connect(self._emit)
        row.remove.connect(self._remove)
        self.rows.append(row)
        self.body.addWidget(row)

    def _remove(self, row):
        if len(self.rows) <= 1:
            return
        self.rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        self._emit()

    def _emit(self):
        entries = [r.entry() for r in self.rows]
        n = sum(e[0] for e in entries if e)
        self.summary.setText('%d conductor%s' % (n, '' if n == 1 else 's'))
        self.changed.emit()

    def value(self):
        entries = [r.entry() for r in self.rows]
        if any(e is None for e in entries):
            return 'invalid'
        return conduit.format_rows(entries)

    def set_value(self, text):
        try:
            rows = conduit.parse_rows(text)
        except ValueError:
            rows = conduit.parse_rows(conduit.DEFAULT_ROWS)
        for r in self.rows:
            r.setParent(None)
            r.deleteLater()
        self.rows = []
        for qty, ins, size, area in rows or conduit.parse_rows(conduit.DEFAULT_ROWS):
            self._add(qty, ins, size or '12', area)
        self._emit()


class ConduitPage(CalculatorPage):
    def make_input(self, i, lbl, default, draft):
        if not is_text(default):
            return super().make_input(i, lbl, default, draft)
        text = draft[i] if i < len(draft) else str(default)
        try:
            conduit.parse_rows(text)
        except ValueError:
            text = str(default)
        w = ConductorList(text)
        w.changed.connect(self.schedule)
        self.inputs.append(w)
        return None, w

    def choice_labels(self, i, default):
        if self.specs[i][0] == 'Trade size':
            return [v if v == conduit.RECOMMEND else '%s"' % v for v in default]
        return None

    def build_inputs(self, card, draft):
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        lists = []
        for i, (lbl, default) in enumerate(self.specs):
            cell = self.input_cell(i, lbl, default, draft)
            if is_text(default):
                lists.append((lbl, cell))
            elif isinstance(self.inputs[-1], Tick):
                grid.addWidget(cell, 1, 0, 1, 2)
            else:
                grid.addWidget(cell, 0, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        for lbl, cell in lists:
            card.body.addWidget(label(lbl, 'muted'))
            card.body.addWidget(cell)
        card.body.addWidget(label('Mix any sizes and insulation types in one raceway. Count the equipment grounding '
                                  'conductor too; choose “Other” to enter the area of a cable or a type not listed.',
                                  'faint', wrap=True))
