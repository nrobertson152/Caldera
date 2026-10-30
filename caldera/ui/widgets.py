"""Reusable, custom-painted building blocks for the Caldera interface."""
import math

from PySide6.QtCore import (QEvent, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer, QVariantAnimation,
                            Signal, QByteArray)
from PySide6.QtGui import (QBrush, QColor, QCursor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath,
                           QPen)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QHeaderView,
                               QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from ..toolmeta import fmt_num, parse_number
from . import icons
from .theme import current as T, mix


# --------------------------------------------------------------------------- small helpers
def qcolor(hex_color, alpha=255):
    c = QColor(hex_color)
    c.setAlpha(alpha)
    return c


def label(text='', name=None, wrap=False, selectable=False):
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    if wrap:
        w.setWordWrap(True)
    if selectable:
        w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return w


def eyebrow(text):
    """Small spaced-out uppercase caption."""
    w = QLabel(text.upper())
    w.setObjectName('eyebrow')
    f = QFont(w.font())
    f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.3)
    w.setFont(f)
    return w


def divider():
    f = QFrame()
    f.setObjectName('divider')
    f.setFixedHeight(1)
    return f


def vbox(parent=None, margins=(0, 0, 0, 0), spacing=0):
    lay = QVBoxLayout(parent) if parent is not None else QVBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return lay


def hbox(parent=None, margins=(0, 0, 0, 0), spacing=0):
    lay = QHBoxLayout(parent) if parent is not None else QHBoxLayout()
    lay.setContentsMargins(*margins)
    lay.setSpacing(spacing)
    return lay


def button(text, kind='', icon=None, cb=None, tip=None):
    """kind: '' (default) | 'primary' | 'ghost' | 'danger'."""
    b = QPushButton(text)
    if kind:
        b.setObjectName(kind)
    t = T()
    if icon:
        color = t['on_accent'] if kind == 'primary' else (t['bad'] if kind == 'danger' else t['text'])
        b.setIcon(icons.icon(icon, color, 16))
        b.setIconSize(QSize(16, 16))
    if cb:
        b.clicked.connect(lambda checked=False: cb())
    if tip:
        b.setToolTip(tip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    return b


def icon_button(name, tip='', cb=None, size=34, color=None, filled=False):
    b = QPushButton()
    b.setObjectName('iconBtn')
    b.setIcon(icons.icon(name, color or T()['muted'], 18, filled))
    b.setIconSize(QSize(18, 18))
    b.setFixedSize(size, size)
    b.setToolTip(tip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    if cb:
        b.clicked.connect(lambda checked=False: cb())
    return b


def icon_label(name, color, size=18, filled=False):
    w = QLabel()
    w.setPixmap(icons.pixmap(name, color, size, 2.0, filled))
    w.setFixedSize(size, size)
    return w


def style_table(table, row_height=44):
    table.setFrameShape(QFrame.Shape.NoFrame)
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
    table.horizontalHeader().setHighlightSections(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)


def fade_in(widget, ms=220):
    """Fade a widget in. The effect is removed afterwards so it never interferes with painting."""
    try:
        fx = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(fx)
        anim = QPropertyAnimation(fx, b'opacity', widget)
        anim.setDuration(ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))
        anim.start()
        widget._fade_anim = anim
    except RuntimeError:
        pass


# --------------------------------------------------------------------------- containers
class Card(QFrame):
    """Rounded surface. Add content through `.body` (a QVBoxLayout)."""

    def __init__(self, padding=20, spacing=12, name='card'):
        super().__init__()
        self.setObjectName(name)
        self.body = vbox(self, (padding, padding, padding, padding), spacing)


class ClickCard(QFrame):
    """A card that behaves like a button (hover outline, pointer cursor)."""
    clicked = Signal()

    def __init__(self, padding=18, spacing=8):
        super().__init__()
        self.setObjectName('cardLink')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.body = vbox(self, (padding, padding, padding, padding), spacing)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton and self.rect().contains(ev.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(ev)


class ScrollPage(QScrollArea):
    """Scrolling page body with a centred, max-width content column."""

    def __init__(self, max_width=1180):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer = QWidget()
        self.setWidget(outer)
        row = hbox(outer, (32, 0, 32, 0))
        row.addStretch(1)
        self.content = QWidget()
        self.content.setMaximumWidth(max_width)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(self.content, 100)
        row.addStretch(1)
        self.col = vbox(self.content, (0, 30, 0, 40), 20)


class Banner(QFrame):
    """Inline status message. kind: good | bad | warn."""

    def __init__(self, kind, text, icon_name=None):
        super().__init__()
        self.setObjectName('banner_' + kind)
        t = T()
        color = {'good': t['good'], 'bad': t['bad'], 'warn': t['warn']}[kind]
        icon_name = icon_name or {'good': 'check_circle', 'bad': 'x_circle', 'warn': 'alert'}[kind]
        lay = hbox(self, (14, 11, 14, 11), 10)
        lay.addWidget(icon_label(icon_name, color, 18), 0, Qt.AlignmentFlag.AlignTop)
        self.text = QLabel(text)
        self.text.setWordWrap(True)
        lay.addWidget(self.text, 1)


class Pill(QLabel):
    def __init__(self, text, kind=''):
        super().__init__(text)
        self.setObjectName('pill' + kind)  # '', 'Muted', 'Good', 'Warn', 'Bad'
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)


# --------------------------------------------------------------------------- inputs
class Combo(QComboBox):
    """Combo box that ignores the mouse wheel unless focused, so scrolling a page never changes a value."""

    def __init__(self, items=()):
        super().__init__()
        self.addItems(list(items))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def wheelEvent(self, ev):
        if self.hasFocus():
            super().wheelEvent(ev)
        else:
            ev.ignore()


class Field(QFrame):
    """Numeric/text input with an inline unit. ↑/↓ step the value (Shift = ×10)."""
    changed = Signal()

    def __init__(self, text='', unit='', numeric=True):
        super().__init__()
        self.setObjectName('field')
        self.numeric = numeric
        self.setFixedHeight(40)
        lay = hbox(self, (12, 0, 12, 0), 8)
        self.edit = QLineEdit(str(text))
        self.edit.setFrame(False)
        self.edit.textChanged.connect(lambda _t: self.changed.emit())
        self.edit.installEventFilter(self)
        lay.addWidget(self.edit, 1)
        if unit:
            u = QLabel(unit)
            u.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lay.addWidget(u)
        self.setProperty('focused', False)
        self.setProperty('invalid', False)

    def text(self):
        return self.edit.text()

    def setText(self, value):
        self.edit.setText(str(value))

    def _flag(self, prop, value):
        if self.property(prop) == value:
            return
        self.setProperty(prop, value)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def set_invalid(self, bad):
        self._flag('invalid', bool(bad))

    def eventFilter(self, obj, ev):
        if obj is self.edit:
            kind = ev.type()
            if kind == QEvent.Type.FocusIn:
                self._flag('focused', True)
            elif kind == QEvent.Type.FocusOut:
                self._flag('focused', False)
            elif kind == QEvent.Type.KeyPress and self.numeric and ev.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                self._step(1 if ev.key() == Qt.Key.Key_Up else -1,
                           bool(ev.modifiers() & Qt.KeyboardModifier.ShiftModifier))
                return True
        return super().eventFilter(obj, ev)

    def _step(self, direction, big):
        try:
            v = parse_number(self.edit.text())
        except ValueError:
            return
        step = 10 ** (math.floor(math.log10(abs(v))) - 1) if v else 1.0
        step = max(step, 1e-9) * (10 if big else 1)
        self.edit.setText('%.10g' % round(v + direction * step, 10))


class Switch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked=False):
        super().__init__()
        self.setFixedSize(42, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._on = bool(checked)
        self._pos = 1.0 if checked else 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(130)
        self._anim.valueChanged.connect(self._tick)

    def _tick(self, v):
        self._pos = float(v)
        self.update()

    def isChecked(self):
        return self._on

    def setChecked(self, on):
        self._on = bool(on)
        self._pos = 1.0 if on else 0.0
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._on = not self._on
            self._anim.stop()
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(1.0 if self._on else 0.0)
            self._anim.start()
            self.toggled.emit(self._on)

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QColor(mix(t['border2'], t['accent'], self._pos))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 2, 42, 20), 10, 10)
        p.setBrush(QColor('#ffffff'))
        p.drawEllipse(QPointF(11 + 20 * self._pos, 12), 8, 8)


class Segmented(QWidget):
    """Pill-shaped option switcher."""
    changed = Signal(str)

    def __init__(self, options, current):
        super().__init__()
        self.options = list(options)
        self.current = current
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        f = QFont(self.font())
        f.setPixelSize(13)
        fm = QFontMetrics(f)
        self._widths = [fm.horizontalAdvance(o) + 28 for o in self.options]
        self.setFixedWidth(sum(self._widths) + 8)

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(t['border']), 1))
        p.setBrush(QColor(t['raised']))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 10, 10)
        x = 4.0
        f = QFont(self.font())
        f.setPixelSize(13)
        f.setWeight(QFont.Weight.Medium)
        p.setFont(f)
        for opt, w in zip(self.options, self._widths):
            r = QRectF(x, 4, w, self.height() - 8)
            if opt == self.current:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(t['accent_soft']))
                p.drawRoundedRect(r, 7, 7)
                p.setPen(QColor(t['accent']))
            else:
                p.setPen(QColor(t['muted']))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, opt)
            x += w

    def mouseReleaseEvent(self, ev):
        x = 4.0
        px = ev.position().x()
        for opt, w in zip(self.options, self._widths):
            if x <= px < x + w:
                if opt != self.current:
                    self.current = opt
                    self.update()
                    self.changed.emit(opt)
                return
            x += w


class Tick(QCheckBox):
    """Tick box that reads and writes the calculator-style strings 'Yes' / 'No'."""

    def __init__(self, text='', checked=False):
        super().__init__(text)
        self.setChecked(bool(checked))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(30)


def get_value(w):
    """The string a calculator input currently holds, whatever widget type it is."""
    if isinstance(w, Tick):
        return 'Yes' if w.isChecked() else 'No'
    if isinstance(w, QComboBox):
        return w.currentText()
    return w.text()


def set_value(w, value):
    if isinstance(w, Tick):
        w.setChecked(str(value) == 'Yes')
    elif isinstance(w, QComboBox):
        w.setCurrentText(str(value))
    else:
        w.setText(str(value))


# --------------------------------------------------------------------------- results
class MetricTile(QFrame):
    def __init__(self, title, value, unit='', tip=''):
        super().__init__()
        self.setObjectName('tile')
        lay = vbox(self, (16, 14, 16, 14), 4)
        cap = QLabel(title)
        cap.setObjectName('faint')
        cap.setWordWrap(True)
        lay.addWidget(cap)
        row = hbox(None, (0, 0, 0, 0), 6)
        self.value = QLabel(value)
        self.value.setObjectName('metricValue')
        row.addWidget(self.value)
        if unit:
            u = QLabel(unit)
            u.setObjectName('unit')
            row.addWidget(u, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        lay.addLayout(row)
        if tip:
            self.setToolTip(tip)


class HeroMetric(QFrame):
    def __init__(self, title, value, unit='', accent_icon='gauge'):
        super().__init__()
        self.setObjectName('hero')
        t = T()
        lay = hbox(self, (22, 18, 22, 18), 16)
        col = vbox(None, (0, 0, 0, 0), 2)
        col.addWidget(eyebrow(title))
        row = hbox(None, (0, 0, 0, 0), 8)
        self.value = QLabel(value)
        self.value.setObjectName('heroValue')
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(self.value)
        if unit:
            u = QLabel(unit)
            u.setObjectName('unit')
            u.setStyleSheet('font-size: 16px;')
            row.addWidget(u, 0, Qt.AlignmentFlag.AlignBottom)
        row.addStretch(1)
        col.addLayout(row)
        lay.addLayout(col, 1)
        lay.addWidget(icon_label(accent_icon, t['accent'], 34), 0, Qt.AlignmentFlag.AlignVCenter)


class SweepChart(QWidget):
    """Sensitivity curve: how one output responds as one input is swept ±50 %."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(210)
        self.setMouseTracking(True)
        self.xs, self.ys = [], []
        self.cur = None
        self.xlabel = self.ylabel = ''
        self._hover = None
        self._precision = 3

    def set_data(self, xs, ys, cur, xlabel, ylabel, precision=3):
        self.xs, self.ys, self.cur = list(xs), list(ys), cur
        self.xlabel, self.ylabel = xlabel, ylabel
        self._precision = precision
        self._hover = None
        self.update()

    # layout helpers
    def _plot(self):
        return QRectF(58, 12, max(self.width() - 58 - 16, 10), max(self.height() - 12 - 34, 10))

    def _bounds(self):
        x0, x1 = min(self.xs), max(self.xs)
        y0, y1 = min(self.ys), max(self.ys)
        if x1 == x0:
            x1 = x0 + 1
        if y1 == y0:
            pad = abs(y0) * 0.1 or 1.0
            y0, y1 = y0 - pad, y1 + pad
        else:
            pad = (y1 - y0) * 0.08
            y0, y1 = y0 - pad, y1 + pad
        return x0, x1, y0, y1

    def _map(self, x, y, b, r):
        x0, x1, y0, y1 = b
        return QPointF(r.left() + (x - x0) / (x1 - x0) * r.width(), r.bottom() - (y - y0) / (y1 - y0) * r.height())

    def mouseMoveEvent(self, ev):
        if len(self.xs) > 1:
            r = self._plot()
            b = self._bounds()
            best, dist = None, 1e9
            for i, (x, y) in enumerate(zip(self.xs, self.ys)):
                d = abs(self._map(x, y, b, r).x() - ev.position().x())
                if d < dist:
                    best, dist = i, d
            self._hover = best
            self.update()

    def leaveEvent(self, ev):
        self._hover = None
        self.update()
        super().leaveEvent(ev)

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        f = QFont(self.font())
        f.setPixelSize(11)
        p.setFont(f)
        if len(self.xs) < 2:
            p.setPen(QColor(t['faint']))
            p.drawText(QRectF(self.rect()), Qt.AlignmentFlag.AlignCenter, 'Not enough valid points to plot.')
            return
        r = self._plot()
        b = self._bounds()
        x0, x1, y0, y1 = b
        # grid + y labels
        for i in range(5):
            frac = i / 4
            y = r.bottom() - frac * r.height()
            p.setPen(QPen(QColor(t['border']), 1, Qt.PenStyle.DotLine if 0 < i < 4 else Qt.PenStyle.SolidLine))
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            p.setPen(QColor(t['faint']))
            p.drawText(QRectF(0, y - 8, r.left() - 8, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       fmt_num(y0 + frac * (y1 - y0), min(self._precision, 2)))
        for i in range(5):
            frac = i / 4
            x = r.left() + frac * r.width()
            p.setPen(QColor(t['faint']))
            p.drawText(QRectF(x - 40, r.bottom() + 6, 80, 14), Qt.AlignmentFlag.AlignCenter,
                       fmt_num(x0 + frac * (x1 - x0), min(self._precision, 2)))
        p.setPen(QColor(t['muted']))
        p.drawText(QRectF(r.left(), self.height() - 15, r.width(), 14), Qt.AlignmentFlag.AlignCenter, self.xlabel)
        # curve + fill
        pts = [self._map(x, y, b, r) for x, y in zip(self.xs, self.ys)]
        line = QPainterPath(pts[0])
        for pt in pts[1:]:
            line.lineTo(pt)
        area = QPainterPath(line)
        area.lineTo(QPointF(pts[-1].x(), r.bottom()))
        area.lineTo(QPointF(pts[0].x(), r.bottom()))
        area.closeSubpath()
        grad = QLinearGradient(QPointF(0, r.top()), QPointF(0, r.bottom()))
        grad.setColorAt(0, qcolor(t['accent'], 70))
        grad.setColorAt(1, qcolor(t['accent'], 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(area)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(t['accent']), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawPath(line)
        # current operating point
        if self.cur is not None:
            cx, cy = self.cur
            if x0 <= cx <= x1:
                pt = self._map(cx, cy, b, r)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(qcolor(t['accent'], 60))
                p.drawEllipse(pt, 9, 9)
                p.setBrush(QColor(t['accent']))
                p.drawEllipse(pt, 4.5, 4.5)
                p.setBrush(QColor(t['surface']))
                p.drawEllipse(pt, 1.8, 1.8)
        # hover read-out
        if self._hover is not None:
            hx, hy = self.xs[self._hover], self.ys[self._hover]
            pt = self._map(hx, hy, b, r)
            p.setPen(QPen(QColor(t['border2']), 1, Qt.PenStyle.DashLine))
            p.drawLine(QPointF(pt.x(), r.top()), QPointF(pt.x(), r.bottom()))
            p.setPen(QPen(QColor(t['surface']), 2))
            p.setBrush(QColor(t['text']))
            p.drawEllipse(pt, 4, 4)
            text = '%s  →  %s' % (fmt_num(hx, self._precision), fmt_num(hy, self._precision))
            fm = QFontMetrics(f)
            w = fm.horizontalAdvance(text) + 20
            bx = min(max(pt.x() - w / 2, r.left()), r.right() - w)
            by = pt.y() - 36 if pt.y() - 36 > r.top() else pt.y() + 12
            p.setPen(QPen(QColor(t['border2']), 1))
            p.setBrush(QColor(t['raised']))
            p.drawRoundedRect(QRectF(bx, by, w, 24), 7, 7)
            p.setPen(QColor(t['text']))
            p.drawText(QRectF(bx, by, w, 24), Qt.AlignmentFlag.AlignCenter, text)


# --------------------------------------------------------------------------- navigation
class NavItem(QWidget):
    """Sidebar row, fully custom painted: icon, label, active indicator and a favourite star."""

    def __init__(self, owner, key, text, icon_name, favourable=False, accent=None):
        super().__init__()
        self.owner, self.key, self.text_, self.icon_name = owner, key, text, icon_name
        self.favourable, self.accent = favourable, accent
        self.selected = False
        self.fav = False
        self.collapsed = False
        self._hover = False
        self._star_hover = False
        self.setFixedHeight(36)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def set_state(self, selected=None, fav=None, collapsed=None):
        if selected is not None:
            self.selected = selected
        if fav is not None:
            self.fav = fav
        if collapsed is not None:
            self.collapsed = collapsed
            self.setToolTip(self.text_ if collapsed else '')
        self.update()

    def _star_rect(self):
        return QRectF(self.width() - 36, 4, 28, self.height() - 8)

    def _star_visible(self):
        return self.favourable and not self.collapsed and (self._hover or self.fav)

    def enterEvent(self, ev):
        self._hover = True
        self.update()
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        self._hover = self._star_hover = False
        self.update()
        super().leaveEvent(ev)

    def mouseMoveEvent(self, ev):
        over = self._star_visible() and self._star_rect().contains(ev.position())
        if over != self._star_hover:
            self._star_hover = over
            self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        if self._star_visible() and self._star_rect().contains(ev.position()):
            self.owner.toggle_favorite(self.key)
        else:
            self.owner.navigate(self.key)

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(8, 2, self.width() - 16, self.height() - 4)
        if self.selected:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t['accent_soft']))
            p.drawRoundedRect(r, 9, 9)
            p.setBrush(QColor(t['accent']))
            p.drawRoundedRect(QRectF(2, self.height() / 2 - 8, 3.5, 16), 1.75, 1.75)
        elif self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t['hover']))
            p.drawRoundedRect(r, 9, 9)
        tint = t['accent'] if self.selected else (t['text'] if self._hover else t['muted'])
        ix = (self.width() - 18) / 2 if self.collapsed else r.left() + 12
        p.drawPixmap(QPointF(ix, (self.height() - 18) / 2), icons.pixmap(self.icon_name, tint, 18))
        if self.collapsed:
            return
        f = QFont(self.font())
        f.setPixelSize(13)
        f.setWeight(QFont.Weight.DemiBold if self.selected else QFont.Weight.Medium)
        p.setFont(f)
        p.setPen(QColor(t['text'] if (self.selected or self._hover) else t['muted']))
        avail = int(r.width() - 44 - (30 if self._star_visible() else 0))
        txt = QFontMetrics(f).elidedText(self.text_, Qt.TextElideMode.ElideRight, avail)
        p.drawText(QRectF(r.left() + 40, 0, avail + 4, self.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, txt)
        if self._star_visible():
            col = t['warn'] if self.fav else (t['text'] if self._star_hover else t['faint'])
            p.drawPixmap(QPointF(self.width() - 31, (self.height() - 16) / 2),
                         icons.pixmap('star', col, 16, 2.0, self.fav))


class NavHeader(QWidget):
    """Collapsible category heading inside the sidebar."""
    clicked = Signal()

    def __init__(self, text, color, count, expanded=True):
        super().__init__()
        self.text_, self.color, self.count, self.expanded = text, color, count, expanded
        self.collapsed_rail = False
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.collapsed_rail:
            p.setPen(QPen(QColor(t['border']), 1))
            p.drawLine(QPointF(20, self.height() / 2), QPointF(self.width() - 20, self.height() / 2))
            return
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.color))
        p.drawEllipse(QPointF(22, self.height() / 2 + 1), 3.2, 3.2)
        f = QFont(self.font())
        f.setPixelSize(11)
        f.setWeight(QFont.Weight.DemiBold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        p.setFont(f)
        p.setPen(QColor(t['faint']))
        p.drawText(QRectF(34, 1, self.width() - 80, self.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text_.upper())
        p.drawText(QRectF(0, 1, self.width() - 42, self.height()),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, str(self.count))
        p.drawPixmap(QPointF(self.width() - 32, (self.height() - 12) / 2 + 1),
                     icons.pixmap('chevron_down' if self.expanded else 'chevron_right', t['faint'], 12, 2.0, False, 2.2))


class BrandMark(QWidget):
    """The Caldera logo, drawn with the active theme's accent gradient."""

    def __init__(self, size=34):
        super().__init__()
        self.setFixedSize(size, size)

    def paintEvent(self, _ev):
        t = T()
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">'
               '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="%s"/>'
               '<stop offset="1" stop-color="%s"/></linearGradient></defs>'
               '<rect width="256" height="256" rx="60" fill="url(#g)"/>'
               '<path d="M53 160 113 58l35 61 20-32 36 73" fill="none" stroke="%s" stroke-width="17" '
               'stroke-linejoin="round" stroke-linecap="round"/>'
               '<path d="M52 183q76 36 152 0" fill="none" stroke="%s" stroke-width="14" stroke-linecap="round" '
               'opacity=".72"/></svg>') % (t['accent'], t['accent2'], t['on_accent'], t['on_accent'])
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        QSvgRenderer(QByteArray(svg.encode('utf-8'))).render(p, QRectF(self.rect()))


class ThemeSwatch(QWidget):
    """Clickable mini-preview of a theme."""
    clicked = Signal(str)

    def __init__(self, theme, selected):
        super().__init__()
        self.theme, self.selected = theme, selected
        self.setFixedSize(168, 112)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(theme['name'])

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.theme['name'])

    def paintEvent(self, _ev):
        th = self.theme
        cur = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        frame = QRectF(1.5, 1.5, self.width() - 3, 84)
        p.setPen(QPen(QColor(cur['accent'] if self.selected else cur['border2']), 2 if self.selected else 1))
        p.setBrush(QColor(th['bg']))
        p.drawRoundedRect(frame, 11, 11)
        # sidebar
        clip = QPainterPath()
        clip.addRoundedRect(frame, 11, 11)
        p.save()
        p.setClipPath(clip)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(th['side']))
        p.drawRect(QRectF(frame.left(), frame.top(), 38, frame.height()))
        p.setBrush(QColor(th['accent']))
        p.drawRoundedRect(QRectF(frame.left() + 9, frame.top() + 11, 20, 6), 3, 3)
        for i in range(3):
            p.setBrush(QColor(th['border2']))
            p.drawRoundedRect(QRectF(frame.left() + 9, frame.top() + 26 + i * 12, 20, 5), 2.5, 2.5)
        # cards
        p.setBrush(QColor(th['surface']))
        p.setPen(QPen(QColor(th['border']), 1))
        p.drawRoundedRect(QRectF(frame.left() + 50, frame.top() + 11, 50, 30), 6, 6)
        p.drawRoundedRect(QRectF(frame.left() + 106, frame.top() + 11, frame.width() - 118, 30), 6, 6)
        p.drawRoundedRect(QRectF(frame.left() + 50, frame.top() + 49, frame.width() - 62, 26), 6, 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(th['text']))
        p.drawRoundedRect(QRectF(frame.left() + 57, frame.top() + 19, 26, 5), 2.5, 2.5)
        p.setBrush(QColor(th['accent']))
        p.drawRoundedRect(QRectF(frame.left() + 57, frame.top() + 56, 56, 5), 2.5, 2.5)
        p.restore()
        # caption
        f = QFont(self.font())
        f.setPixelSize(12)
        f.setWeight(QFont.Weight.DemiBold)
        p.setFont(f)
        p.setPen(QColor(cur['text'] if self.selected else cur['muted']))
        p.drawText(QRectF(2, 90, self.width() - 4, 20), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                   th['name'])
        if self.selected:
            p.drawPixmap(QPointF(self.width() - 18, 93), icons.pixmap('check_circle', cur['accent'], 15))


class Toast(QFrame):
    """Transient confirmation pill anchored to the bottom centre of its parent window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._icon = QLabel()
        self._icon.setFixedSize(18, 18)
        self._text = QLabel()
        lay = hbox(self, (16, 11, 18, 11), 10)
        lay.addWidget(self._icon)
        lay.addWidget(self._text)
        self._fx = QGraphicsOpacityEffect(self)
        self._fx.setOpacity(0.0)
        self.setGraphicsEffect(self._fx)
        self._anim = QPropertyAnimation(self._fx, b'opacity', self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide)
        self.hide()

    def show_message(self, text, kind='good'):
        t = T()
        self.setStyleSheet('QFrame { background: %s; border: 1px solid %s; border-radius: 12px; } '
                           'QLabel { background: transparent; border: 0; }' % (t['raised'], t['border2']))
        color = {'good': t['good'], 'bad': t['bad'], 'warn': t['warn'], 'info': t['accent']}.get(kind, t['accent'])
        name = {'good': 'check_circle', 'bad': 'x_circle', 'warn': 'alert', 'info': 'info'}.get(kind, 'info')
        self._icon.setPixmap(icons.pixmap(name, color, 18))
        self._text.setText(text)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setDuration(160)
        self._anim.setStartValue(self._fx.opacity())
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(2300)

    def reposition(self):
        par = self.parentWidget()
        if par is not None:
            self.move(int((par.width() - self.width()) / 2), par.height() - self.height() - 28)

    def _hide(self):
        self._anim.stop()
        self._anim.setDuration(260)
        self._anim.setStartValue(self._fx.opacity())
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self._after_hide)
        self._anim.start()

    def _after_hide(self):
        try:
            self._anim.finished.disconnect(self._after_hide)
        except (RuntimeError, TypeError):
            pass
        if self._fx.opacity() <= 0.01:
            self.hide()
