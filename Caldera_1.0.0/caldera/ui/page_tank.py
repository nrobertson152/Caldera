"""Reservoir / Drip Pan: grouped inputs, drip-rail tick box and a live 3D preview."""
from PySide6.QtWidgets import QGridLayout

from .. import model3d, tank
from .pages_core import CalculatorPage
from .theme import current as T
from .viewer3d import Viewer3D
from .kit import section_title
from .widgets import Card, Combo, Segmented, Tick, eyebrow, hbox, label

# (title, color key, first spec index, one-past-last spec index)
SECTIONS = [('Reservoir', 'Hydraulic', 0, 7), ('Drip pan', 'Mechanical', 7, 11), ('Drip rail', 'Electrical', 11, 14)]


class ReservoirPage(CalculatorPage):
    def build_inputs(self, card, draft):
        t = T()
        for title, color_key, lo, hi in SECTIONS:
            head = eyebrow(title)
            head.setStyleSheet('color: %s;' % t['cats'][color_key])
            card.body.addWidget(head)
            grid = QGridLayout()
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(14)
            slot = 0
            for i in range(lo, hi):
                lbl, default = self.specs[i]
                cell = self.input_cell(i, lbl, default, draft)
                if isinstance(self.inputs[-1], Tick):          # tick boxes take a whole row
                    row = (slot + 1) // 2
                    grid.addWidget(cell, row, 0, 1, 2)
                    slot = (row + 1) * 2
                else:
                    grid.addWidget(cell, slot // 2, slot % 2)
                    slot += 1
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            card.body.addLayout(grid)
            if title == 'Drip rail':
                card.body.addWidget(label('The rail is made from the drip pan’s material.', 'faint'))
        self.rail_tick = self.inputs[11]
        self.rail_tick.toggled.connect(lambda _b: self._sync_rail())
        self._sync_rail()

    def _sync_rail(self):
        on = self.rail_tick.isChecked()
        for w in self.inputs[12:14]:
            w.setEnabled(on)
            w.setToolTip('' if on else 'Tick “Drip rail” to edit')

    # ------------------------------------------------------------------ 3D preview
    def build_right_top(self, right):
        saved = self.win.data.get('tank_view', {})
        self.view = saved.get('view') if saved.get('view') in model3d.VIEWS else model3d.VIEWS[0]
        self.ref = saved.get('ref') if saved.get('ref') in model3d.REFERENCES else 'Soda can (12 oz)'
        card = Card(padding=18, spacing=12)
        card.body.addWidget(section_title('3D preview'))
        ctl = hbox(None, (0, 0, 0, 0), 12)
        self.seg = Segmented(model3d.VIEWS, self.view)
        self.seg.changed.connect(self._view_changed)
        ctl.addWidget(self.seg)
        ctl.addStretch(1)
        ctl.addWidget(label('Size reference', 'muted'))
        self.ref_combo = Combo(list(model3d.REFERENCES))
        self.ref_combo.setCurrentText(self.ref)
        self.ref_combo.setMinimumWidth(180)
        self.ref_combo.currentTextChanged.connect(self._ref_changed)
        ctl.addWidget(self.ref_combo)
        card.body.addLayout(ctl)
        self.viewer = Viewer3D()
        card.body.addWidget(self.viewer)
        card.body.addWidget(label('Models are simplified (walls drawn thicker than true gauge so they stay visible). '
                                  'Everything else, including the reference object, is to scale.', 'faint', wrap=True))
        right.addWidget(card)

    def _remember(self):
        self.win.data['tank_view'] = {'view': self.view, 'ref': self.ref}
        self.win.schedule_save()

    def _view_changed(self, name):
        self.view = name
        self._remember()
        self.refresh_model()

    def _ref_changed(self, name):
        self.ref = name
        self._remember()
        self.refresh_model()

    def refresh_model(self):
        try:
            v = tank.params(self.values())
        except ValueError as e:
            self.viewer.set_message(str(e))
            return
        parts, caption = model3d.build_scene(self.view, v, self.ref)
        if parts:
            self.viewer.set_scene(parts, caption)
        else:
            self.viewer.set_message(caption)

    def after_recalc(self):
        self.refresh_model()
