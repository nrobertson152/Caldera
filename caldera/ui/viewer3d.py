"""Painted 3D viewer for the reservoir / drip pan preview (software projection from caldera.model3d)."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from .. import model3d
from .theme import current as T, mix


class Viewer3D(QWidget):
    DEFAULT_YAW, DEFAULT_PITCH = -0.62, 0.52

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(360)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.parts, self.caption, self.message = [], '', ''
        self.yaw, self.pitch, self.zoom = self.DEFAULT_YAW, self.DEFAULT_PITCH, 1.0
        self._drag = None

    # ------------------------------------------------------------------ api
    def set_scene(self, parts, caption=''):
        self.parts, self.caption, self.message = parts, caption, ''
        self.update()

    def set_message(self, text):
        self.parts, self.caption, self.message = [], '', text
        self.update()

    def reset_view(self):
        self.yaw, self.pitch, self.zoom = self.DEFAULT_YAW, self.DEFAULT_PITCH, 1.0
        self.update()

    # ------------------------------------------------------------------ interaction
    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._drag = QPointF(ev.position())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, ev):
        if self._drag is not None:
            d = ev.position() - self._drag
            self._drag = QPointF(ev.position())
            self.yaw -= d.x() * 0.01
            self.pitch = min(max(self.pitch + d.y() * 0.01, 0.03), 1.5)
            self.update()

    def mouseReleaseEvent(self, ev):
        self._drag = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseDoubleClickEvent(self, ev):
        self.reset_view()

    def wheelEvent(self, ev):
        self.zoom = min(max(self.zoom * (1.0015 ** ev.angleDelta().y()), 0.35), 6.0)
        self.update()

    # ------------------------------------------------------------------ painting
    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        full = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        p.setPen(QPen(QColor(t['border']), 1))
        p.setBrush(QColor(mix(t['bg'], t['surface'], 0.5)))
        p.drawRoundedRect(full, 12, 12)
        small = QFont(self.font())
        small.setPixelSize(11)
        p.setFont(small)
        if not self.parts:
            p.setPen(QColor(t['muted']))
            p.drawText(full.adjusted(20, 0, -20, 0), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                       self.message or 'Nothing to show.')
            return
        out = model3d.project(self.parts, self.yaw, self.pitch)
        x0, y0, x1, y1 = out['bounds']
        area = QRectF(18, 30, self.width() - 36, self.height() - 30 - 40)
        bw, bh = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)
        scale = min(area.width() / bw, area.height() / bh) * self.zoom
        ox = area.center().x() - (x0 + x1) / 2 * scale
        oy = area.center().y() - (y0 + y1) / 2 * scale

        def pt(q):
            return QPointF(ox + q[0] * scale, oy + q[1] * scale)

        p.save()
        p.setClipRect(full.adjusted(1, 1, -1, -1))
        grid = QColor(t['border2'])
        grid.setAlpha(90)
        p.setPen(QPen(grid, 1))
        for a, b in out['grid']:
            p.drawLine(pt(a), pt(b))
        edge_dark = QColor(0, 0, 0, 95 if t['dark'] else 70)
        for pts, color, alpha in out['polys']:
            c = QColor(color)
            c.setAlphaF(alpha)
            p.setBrush(c)
            p.setPen(QPen(edge_dark if alpha >= 0.999 else QColor(color), 1))
            p.drawPolygon(QPolygonF([pt(q) for q in pts]))
        p.restore()

        p.setPen(QColor(t['faint']))
        p.drawText(QRectF(14, 8, self.width() - 28, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                   'Drag to rotate  ·  scroll to zoom  ·  double-click to reset')
        p.setPen(QColor(t['muted']))
        fm = QFontMetrics(small)
        text = fm.elidedText(self.caption, Qt.TextElideMode.ElideRight, int(self.width() - 28))
        p.drawText(QRectF(14, self.height() - 30, self.width() - 28, 20),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
