"""Composite UI helpers shared by the page modules."""
from datetime import datetime

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QPushButton, QSizePolicy, QWidget

from . import icons
from .theme import current as T, mix
from .widgets import Card, ClickCard, eyebrow, hbox, label, vbox


class IconTile(QWidget):
    """Rounded square with a tinted icon, used as a visual anchor on cards."""

    def __init__(self, icon_name, color, size=40):
        super().__init__()
        self.icon_name, self.color, self.size_ = icon_name, color, size
        self.setFixedSize(size, size)

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(mix(t['surface'], self.color, 0.16 if t['dark'] else 0.13)))
        p.drawRoundedRect(QRectF(0, 0, self.size_, self.size_), self.size_ * 0.28, self.size_ * 0.28)
        ic = int(self.size_ * 0.5)
        p.drawPixmap(int((self.size_ - ic) / 2), int((self.size_ - ic) / 2), icons.pixmap(self.icon_name, self.color, ic))


def page_header(title, desc='', category=None, actions=()):
    w = QWidget()
    lay = hbox(w, (0, 0, 0, 0), 12)
    col = vbox(None, (0, 0, 0, 0), 4)
    if category:
        e = eyebrow(category)
        e.setStyleSheet('color: %s;' % T()['cats'].get(category, T()['faint']))
        col.addWidget(e)
    col.addWidget(label(title, 'h1'))
    if desc:
        col.addWidget(label(desc, 'muted', wrap=True))
    lay.addLayout(col, 1)
    for a in actions:
        lay.addWidget(a, 0, Qt.AlignmentFlag.AlignTop)
    return w


def section_title(text, sub='', color=None, right=None):
    w = QWidget()
    lay = hbox(w, (0, 0, 0, 0), 10)
    if color:
        dot = QWidget()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet('background: %s; border-radius: 4px;' % color)
        lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
    lay.addWidget(label(text, 'h2'))
    if sub:
        lay.addWidget(label(sub, 'faint'))
    lay.addStretch(1)
    if right is not None:
        lay.addWidget(right)
    return w


def setting_row(title, desc, control):
    w = QWidget()
    lay = hbox(w, (0, 4, 0, 4), 16)
    col = vbox(None, (0, 0, 0, 0), 2)
    col.addWidget(label(title, 'h3'))
    if desc:
        col.addWidget(label(desc, 'faint', wrap=True))
    lay.addLayout(col, 1)
    lay.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)
    return w


def stat_card(icon_name, caption, value, color):
    c = Card(padding=18, spacing=0)
    row = hbox(None, (0, 0, 0, 0), 14)
    row.addWidget(IconTile(icon_name, color, 42))
    col = vbox(None, (0, 0, 0, 0), 0)
    v = label(str(value), 'h1')
    col.addWidget(v)
    col.addWidget(label(caption, 'muted'))
    row.addLayout(col, 1)
    c.body.addLayout(row)
    return c


def tool_card(name, icon_name, color, blurb, on_click, favourite=False):
    c = ClickCard(padding=16, spacing=0)
    c.setMinimumHeight(98)
    c.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    row = hbox(None, (0, 0, 0, 0), 14)
    row.addWidget(IconTile(icon_name, color, 40), 0, Qt.AlignmentFlag.AlignTop)
    col = vbox(None, (0, 0, 0, 0), 3)
    head = hbox(None, (0, 0, 0, 0), 6)
    head.addWidget(label(name, 'h3'))
    if favourite:
        head.addWidget(label('★', 'muted'))
    head.addStretch(1)
    col.addLayout(head)
    col.addWidget(label(blurb, 'faint', wrap=True))
    col.addStretch(1)
    row.addLayout(col, 1)
    c.body.addLayout(row)
    c.clicked.connect(on_click)
    return c


def ago(iso):
    try:
        d = datetime.fromisoformat(str(iso))
    except ValueError:
        return ''
    secs = (datetime.now() - d).total_seconds()
    if secs < 45:
        return 'just now'
    if secs < 3600:
        return '%d min ago' % max(1, int(secs // 60))
    if secs < 86400:
        return '%d h ago' % int(secs // 3600)
    if secs < 172800:
        return 'yesterday'
    if secs < 86400 * 14:
        return '%d days ago' % int(secs // 86400)
    return d.strftime('%b %d, %Y')


def clear_layout(layout):
    """Remove and schedule deletion of everything in a layout (recursively)."""
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


class ClickRow(QPushButton):
    """A full-width, hoverable row that hosts arbitrary child widgets (add them to `.body`, then call `.seal()`)."""

    def __init__(self, padding=(10, 8, 10, 8), spacing=12):
        super().__init__()
        self.setObjectName('rowBtn')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.body = hbox(self, padding, spacing)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        # A QPushButton sizes itself from its (empty) text and ignores the layout inside it, which clipped tall
        # children such as icon tiles. Report the layout's size instead so the row grows to fit its content.
        return self.body.sizeHint().expandedTo(QSize(40, 0))

    def minimumSizeHint(self):
        return self.body.minimumSize()

    def seal(self):
        """Let clicks fall through the children to the row itself."""
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        return self


def fit_table_height(table, extra=4):
    """Size a table to its content so the surrounding page scrolls instead of the table."""
    h = table.horizontalHeader().height() + extra
    for r in range(table.rowCount()):
        h += table.rowHeight(r)
    table.setFixedHeight(h)
