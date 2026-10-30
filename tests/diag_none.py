import os, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import PySide6
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                           QPolygonF, QMouseEvent)
from PySide6.QtWidgets import QApplication
app = QApplication([])
img = QImage(200, 200, QImage.Format.Format_ARGB32)
p = QPainter(img)
c = QColor('#336699'); pen = QPen(c, 1); poly = QPolygonF([QPointF(0, 0), QPointF(10, 0), QPointF(5, 9)])
path = QPainterPath(QPointF(0, 0)); path.lineTo(QPointF(20, 20))
grad = QLinearGradient(QPointF(0, 0), QPointF(0, 10))
f = QFont(); fm = QFontMetrics(f)
tests = {
 'QColor.setAlphaF': lambda: c.setAlphaF(0.5), 'QColor.setAlpha': lambda: c.setAlpha(9),
 'setBrush(QColor)': lambda: p.setBrush(c), 'setBrush(NoBrush)': lambda: p.setBrush(Qt.BrushStyle.NoBrush),
 'setBrush(QBrush)': lambda: p.setBrush(QBrush(grad)),
 'setPen(QPen)': lambda: p.setPen(pen), 'setPen(QColor)': lambda: p.setPen(c), 'setPen(NoPen)': lambda: p.setPen(Qt.PenStyle.NoPen),
 'drawPolygon(QPolygonF)': lambda: p.drawPolygon(poly), 'drawPolygon(list)': lambda: p.drawPolygon([QPointF(0,0),QPointF(4,4),QPointF(0,4)]),
 'drawLine(pt,pt)': lambda: p.drawLine(QPointF(0, 0), QPointF(3, 3)), 'drawPath': lambda: p.drawPath(path),
 'drawEllipse(pt,r,r)': lambda: p.drawEllipse(QPointF(5, 5), 3, 3), 'drawRoundedRect': lambda: p.drawRoundedRect(QRectF(0, 0, 9, 9), 2, 2),
 'drawText(rect,flags,str)': lambda: p.drawText(QRectF(0, 0, 50, 9), Qt.AlignmentFlag.AlignCenter, 'x'),
 'setFont': lambda: p.setFont(f), 'setRenderHint': lambda: p.setRenderHint(QPainter.RenderHint.Antialiasing),
 'save/restore': lambda: (p.save(), p.restore()), 'setClipRect': lambda: p.setClipRect(QRectF(0, 0, 100, 100)),
 'path.lineTo': lambda: QPainterPath(QPointF(0,0)).lineTo(QPointF(1,1)), 'grad.setColorAt': lambda: grad.setColorAt(0, c),
 'fm.elidedText': lambda: fm.elidedText('abc', Qt.TextElideMode.ElideRight, 20), 'fm.horizontalAdvance': lambda: fm.horizontalAdvance('abc'),
 'QPolygonF(list)': lambda: QPolygonF([QPointF(0, 0), QPointF(1, 1)]), 'QPointF-QPointF': lambda: QPointF(1, 1) - QPointF(0, 0),
}
lines = ['PySide6 %s, Python %s' % (PySide6.__version__, sys.version.split()[0])]
for name, fn in tests.items():
    fn()
    before = sys.getrefcount(None)
    for _ in range(1000):
        fn()
    lost = before - sys.getrefcount(None)
    lines.append('%-28s None refs lost per 1000 calls: %d%s' % (name, lost, '   <-- LEAK' if lost >= 900 else ''))
p.end()
print('\n'.join(lines))
