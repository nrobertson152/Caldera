"""Hydraulic Cylinder Cycle Time: the calculator plus an animated cylinder that extends and retracts at the
computed speeds, with play / pause, playback speed and a timeline."""
from PySide6.QtCore import QElapsedTimer, QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from .. import units
from ..toolmeta import parse_number
from .kit import section_title
from .pages_core import CalculatorPage
from .theme import current as T, mix
from .widgets import Card, Segmented, Tick, button, hbox, label

SPEEDS = {'¼×': 0.25, '½×': 0.5, '1×': 1.0, '2×': 2.0, '5×': 5.0}


class CylinderAnimation(QWidget):
    """Painted double-acting cylinder. `t` is seconds into the cycle (0 .. extend + retract)."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(250)
        self.bore, self.rod, self.stroke = 4.0, 2.0, 24.0
        self.t_ext, self.t_ret = 1.0, 1.0
        self.t = 0.0
        self.valid = False
        self.message = ''

    def set_cylinder(self, bore, rod, stroke, t_ext, t_ret):
        self.bore, self.rod, self.stroke, self.t_ext, self.t_ret = bore, rod, stroke, t_ext, t_ret
        self.valid, self.message = True, ''
        self.t = min(self.t, self.cycle())
        self.update()

    def set_message(self, text):
        self.valid, self.message = False, text
        self.update()

    def cycle(self):
        return self.t_ext + self.t_ret

    def position(self):
        """Fraction extended (0 = retracted, 1 = fully out) and the phase name."""
        t = self.t
        if t < self.t_ext:
            return t / self.t_ext if self.t_ext else 1.0, 'Extending'
        r = t - self.t_ext
        return max(0.0, 1 - (r / self.t_ret if self.t_ret else 1.0)), 'Retracting'

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        full = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(t['border']), 1))
        p.setBrush(QColor(mix(t['bg'], t['surface'], 0.5)))
        p.drawRoundedRect(full, 12, 12)
        f = QFont(self.font())
        f.setPixelSize(12)
        p.setFont(f)
        if not self.valid:
            p.setPen(QColor(t['muted']))
            p.drawText(full.adjusted(20, 0, -20, 0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       self.message or 'Enter valid inputs to animate the cylinder.')
            return
        frac, phase = self.position()
        extending = phase == 'Extending'

        # ---- geometry (inches -> px). Length is to scale; bore height is clamped so it stays readable.
        b, r, s = self.bore, self.rod, self.stroke
        cap, piston, gland, eye = 0.45 * b, 0.35 * b, 0.4 * b, 0.55 * b
        barrel_len = cap + s + piston + gland
        total = barrel_len + s + eye
        left, right = 26.0, self.width() - 26.0
        k = (right - left) / total
        mid = 30 + (self.height() - 30 - 70) / 2
        bh = min(max(b * k, 34.0), (self.height() - 120) * 0.9, 110.0)
        rh = max(bh * r / b, 6.0)
        x_cap = left
        x_bore0 = x_cap + cap * k
        x_bore1 = x_bore0 + (s + piston) * k
        x_end = x_bore1 + gland * k
        piston_x = x_bore0 + frac * s * k
        rod_end = x_end + frac * s * k                    # rod length is constant: (stroke + gland) beyond the piston
        top, bottom = mid - bh / 2, mid + bh / 2

        oil_p = QColor(t['accent'])
        oil_l = QColor(mix(t['accent'], t['bg'], 0.65))
        cap_col, ann_col = (oil_p, oil_l) if extending else (oil_l, oil_p)
        steel = QColor(mix(t['muted'], t['surface'], 0.25))
        edge = QPen(QColor(t['border2']), 1.2)

        # oil chambers
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cap_col)
        p.drawRect(QRectF(x_bore0, top + 4, max(piston_x - x_bore0, 0), bh - 8))
        p.setBrush(ann_col)
        p.drawRect(QRectF(piston_x + piston * k, top + 4, max(x_bore1 - piston_x - piston * k, 0), bh - 8))
        # barrel walls, cap and gland
        p.setPen(edge)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(x_cap, top, x_end - x_cap, bh), 6, 6)
        p.setBrush(steel)
        p.drawRoundedRect(QRectF(x_cap, top - 3, cap * k, bh + 6), 4, 4)
        p.drawRoundedRect(QRectF(x_bore1, top - 3, gland * k, bh + 6), 4, 4)
        # rod (shiny) and piston
        grad = QLinearGradient(QPointF(0, mid - rh / 2), QPointF(0, mid + rh / 2))
        grad.setColorAt(0, QColor(mix(t['text'], t['surface'], 0.35)))
        grad.setColorAt(0.5, QColor(mix(t['text'], t['surface'], 0.1)))
        grad.setColorAt(1, QColor(mix(t['text'], t['surface'], 0.5)))
        p.setBrush(grad)
        p.drawRect(QRectF(piston_x + piston * k, mid - rh / 2, rod_end - piston_x - piston * k, rh))
        p.setBrush(steel)
        p.drawRoundedRect(QRectF(piston_x, top + 3, piston * k, bh - 6), 3, 3)
        # rod eye
        p.drawEllipse(QPointF(rod_end + eye * k * 0.4, mid), max(rh * 0.75, 7), max(rh * 0.75, 7))
        p.setBrush(QColor(mix(t['bg'], t['surface'], 0.5)))
        p.drawEllipse(QPointF(rod_end + eye * k * 0.4, mid), max(rh * 0.3, 3), max(rh * 0.3, 3))

        # ports + flow arrows
        port_cap = QPointF(x_bore0 + 10, top - 3)
        port_rod = QPointF(x_bore1 - 10, top - 3)
        for pt, pressured in ((port_cap, extending), (port_rod, not extending)):
            col = QColor(t['accent'] if pressured else t['faint'])
            p.setPen(QPen(col, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(pt, QPointF(pt.x(), pt.y() - 18))
            path = QPainterPath()
            if pressured:                                   # arrow pointing into the port
                path.moveTo(pt.x() - 5, pt.y() - 9)
                path.lineTo(pt.x(), pt.y() - 3)
                path.lineTo(pt.x() + 5, pt.y() - 9)
            else:                                           # arrow leaving the port
                path.moveTo(pt.x() - 5, pt.y() - 12)
                path.lineTo(pt.x(), pt.y() - 18)
                path.lineTo(pt.x() + 5, pt.y() - 12)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            p.setPen(QColor(t['faint']))
            p.drawText(QRectF(pt.x() - 40, pt.y() - 36, 80, 14), Qt.AlignmentFlag.AlignCenter,
                       'pressure' if pressured else 'to tank')

        # ---- readouts
        p.setPen(QColor(t['text']))
        f2 = QFont(f)
        f2.setPixelSize(14)
        f2.setWeight(QFont.Weight.DemiBold)
        p.setFont(f2)
        p.drawText(QRectF(18, 10, self.width() - 36, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   '%s  ·  %.2f s' % (phase, self.t))
        p.setFont(f)
        p.setPen(QColor(t['muted']))
        out_now = frac * s
        p.drawText(QRectF(18, 10, self.width() - 36, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   'Rod out %s of %s' % (_len(out_now), _len(s)))

        # ---- timeline
        ty = self.height() - 44
        tl, tr = 18.0, self.width() - 18.0
        cyc = self.cycle() or 1.0
        xe = tl + (tr - tl) * self.t_ext / cyc
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(mix(t['accent'], t['bg'], 0.35)))
        p.drawRoundedRect(QRectF(tl, ty, xe - tl, 8), 4, 4)
        p.setBrush(QColor(mix(t['accent2'], t['bg'], 0.55)))
        p.drawRoundedRect(QRectF(xe, ty, tr - xe, 8), 4, 4)
        head = tl + (tr - tl) * min(self.t / cyc, 1.0)
        p.setBrush(QColor(t['text']))
        p.drawEllipse(QPointF(head, ty + 4), 6, 6)
        p.setPen(QColor(t['faint']))
        fm = QFontMetrics(f)
        a = 'Extend %.2f s' % self.t_ext
        bt = 'Retract %.2f s' % self.t_ret
        p.drawText(QRectF(tl, ty + 12, max(xe - tl, fm.horizontalAdvance(a) + 4), 16),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, a)
        p.drawText(QRectF(xe, ty + 12, tr - xe, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, bt)


def _len(inches):
    if units.metric():
        return '%.0f mm' % (inches * 25.4)
    return '%.2f in' % inches


class CylinderCyclePage(CalculatorPage):
    def build_right_top(self, right):
        card = Card(padding=18, spacing=12)
        self.play_btn = button('Play', 'primary', 'play', self.toggle_play)
        card.body.addWidget(section_title('Animation', 'real-time extend and retract', right=self.play_btn))
        self.anim = CylinderAnimation()
        card.body.addWidget(self.anim)
        ctl = hbox(None, (0, 0, 0, 0), 12)
        ctl.addWidget(label('Speed', 'muted'))
        saved = self.win.data.get('cylinder_anim', {})
        self.speed_name = saved.get('speed') if saved.get('speed') in SPEEDS else '1×'
        self.speed = Segmented(list(SPEEDS), self.speed_name)
        self.speed.changed.connect(self._speed_changed)
        ctl.addWidget(self.speed)
        ctl.addStretch(1)
        self.loop = Tick('Loop', saved.get('loop', True))
        self.loop.toggled.connect(lambda _b: self._remember())
        ctl.addWidget(self.loop)
        ctl.addWidget(button('Restart', 'ghost', 'reset', self.restart))
        card.body.addLayout(ctl)
        card.body.addWidget(label('Length is to scale; the bore is drawn taller when needed so it stays visible. The '
                                  'bright chamber is pressurised; the pale one drains to tank.', 'faint', wrap=True))
        right.addWidget(card)
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)
        self._anim_timer.timeout.connect(self._tick)
        self._clock = QElapsedTimer()
        self._playing = False

    def _remember(self):
        self.win.data['cylinder_anim'] = {'speed': self.speed_name, 'loop': self.loop.isChecked()}
        self.win.schedule_save()

    def _speed_changed(self, name):
        self.speed_name = name
        self.speed.current = name
        self.speed.update()
        self._remember()

    def toggle_play(self):
        if self._playing:
            self._pause()
        else:
            if not self.anim.valid:
                return
            if self.anim.t >= self.anim.cycle() - 1e-6:
                self.anim.t = 0.0
            self._playing = True
            self._clock.start()
            self._anim_timer.start()
            self._set_button()

    def _pause(self):
        self._playing = False
        self._anim_timer.stop()
        self._set_button()

    def restart(self):
        self.anim.t = 0.0
        self.anim.update()
        if not self._playing:
            self.toggle_play()

    def _set_button(self):
        from . import icons
        t = T()
        self.play_btn.setText('Pause' if self._playing else 'Play')
        self.play_btn.setIcon(icons.icon('pause' if self._playing else 'play', t['on_accent'], 18))

    def _tick(self):
        dt = self._clock.restart() / 1000.0 * SPEEDS.get(self.speed_name, 1.0)
        cyc = self.anim.cycle()
        if cyc <= 0:
            self._pause()
            return
        self.anim.t += dt
        if self.anim.t >= cyc:
            if self.loop.isChecked():
                self.anim.t %= cyc
            else:
                self.anim.t = cyc
                self._pause()
        self.anim.update()

    def after_recalc(self):
        res = self.canon
        if res is None or res.error:
            self.anim.set_message(res.error if res else '')
            self._pause()
            return
        times = {m.label: m.value for m in res.metrics if m.kind == 'num'}
        try:
            bore, rod, stroke = (parse_number(v) for v in self.values()[:3])
        except ValueError:
            self.anim.set_message('Enter valid inputs to animate the cylinder.')
            return
        te, tr = times.get('Extend time', 0.0), times.get('Retract time', 0.0)
        if te <= 0 or tr <= 0 or te + tr > 3600:
            self.anim.set_message('Cycle is too slow or too fast to animate (%.3g s).' % (te + tr))
            self._pause()
            return
        self.anim.set_cylinder(bore, rod, stroke, te, tr)
