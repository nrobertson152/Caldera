"""Application chrome: sidebar, top bar, command palette and modal sheets."""
from PySide6.QtCore import QEasingCurve, QEvent, QPoint, QRectF, QSize, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (QDialog, QFrame, QLineEdit, QListWidget, QListWidgetItem, QMenu,
                               QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QWidget)

from ..toolmeta import CATEGORIES, SYSTEM_PAGES, icon_of
from ..registry import TOOLS
from . import icons
from .kit import IconTile, clear_layout
from .theme import current as T
from .widgets import (BrandMark, Field, NavHeader, NavItem, button, hbox, icon_button, icon_label, label, vbox)


# =========================================================================== modal sheets
def _size_button(b):
    """Make a dialog button big enough for its text (the stylesheet adds padding and a heavier weight)."""
    b.setMinimumHeight(40)
    b.setMinimumWidth(max(104, b.fontMetrics().horizontalAdvance(b.text()) + 56))
    return b


class Sheet(QDialog):
    """Small frameless modal used for confirmations and prompts. `.body` takes extra widgets."""

    def __init__(self, parent, title, text='', ok='OK', danger=False, width=460, cancel='Cancel', extra=None):
        super().__init__(parent)
        self.setObjectName('sheet')
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setFixedWidth(width)
        lay = vbox(self, (28, 26, 28, 22), 12)
        lay.addWidget(label(title, 'h2'))
        if text:
            lay.addWidget(label(text, 'muted', wrap=True))
        self.body = vbox(None, (0, 4, 0, 4), 10)
        lay.addLayout(self.body)
        row = hbox(None, (0, 10, 0, 0), 10)
        row.addStretch(1)
        if cancel:
            row.addWidget(_size_button(button(cancel, 'ghost', None, self.reject)))
        if extra:
            row.addWidget(_size_button(button(extra, '', None, self._pick_extra)))
        self.ok_btn = _size_button(button(ok, 'danger' if danger else 'primary', None, self.accept))
        row.addWidget(self.ok_btn)
        lay.addLayout(row)
        self._accepted, self.picked = False, None
        self.accepted.connect(self._mark)

    def _mark(self):
        self._accepted = True
        if self.picked is None:
            self.picked = 'ok'

    def _pick_extra(self):
        self.picked = 'extra'
        self.accept()

    def _fit(self):
        """Give the dialog the height its wrapped text really needs. A word-wrapped QLabel reports its height for an
        unwrapped width, which is what used to squeeze the buttons."""
        self.ensurePolished()
        lay = self.layout()
        lay.activate()
        need = lay.sizeHint().height()
        if lay.hasHeightForWidth():
            need = max(need, lay.heightForWidth(self.width()))
        self.setFixedHeight(need + 4)

    def run(self):
        """Show modally; True only when a primary/extra button (not Cancel) was used."""
        self._fit()
        self.exec()
        return self._accepted

    def showEvent(self, ev):
        super().showEvent(ev)
        par = self.parentWidget()
        if par is not None:
            win = par.window()
            c = win.mapToGlobal(win.rect().center())
            self.move(c.x() - self.width() // 2, c.y() - self.height() // 2 - 40)


def confirm(parent, title, text, ok='Confirm', danger=True):
    return Sheet(parent, title, text, ok, danger).run()


def choose(parent, title, text, primary, secondary, cancel='Cancel'):
    """Three-way decision. Returns 'primary', 'secondary' or None (cancelled)."""
    dlg = Sheet(parent, title, text, primary, False, 520, cancel, extra=secondary)
    if not dlg.run():
        return None
    return 'primary' if dlg.picked == 'ok' else 'secondary'


def prompt(parent, title, caption, value='', ok='Save', placeholder=''):
    """Ask for one line of text. Returns the stripped string, or None when cancelled/empty."""
    dlg = Sheet(parent, title, '', ok)
    dlg.body.addWidget(label(caption, 'muted'))
    field = Field(value, '', numeric=False)
    if placeholder:
        field.edit.setPlaceholderText(placeholder)
    field.edit.returnPressed.connect(dlg.accept)
    dlg.body.addWidget(field)
    QTimer.singleShot(0, lambda: (field.edit.setFocus(), field.edit.selectAll()))
    if dlg.run() and field.text().strip():
        return field.text().strip()
    return None


def prompt_multiline(parent, title, caption, value=''):
    dlg = Sheet(parent, title, '', 'Save', width=580)
    dlg.body.addWidget(label(caption, 'muted'))
    edit = QPlainTextEdit(value)
    edit.setMinimumHeight(190)
    edit.setPlaceholderText('Write anything worth remembering about this project…')
    dlg.body.addWidget(edit)
    QTimer.singleShot(0, edit.setFocus)
    if dlg.run():
        return edit.toPlainText()
    return None


# =========================================================================== sidebar
class Sidebar(QFrame):
    EXPANDED, RAIL = 272, 68

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName('sidebar')
        self.collapsed = bool(win.data.get('sidebar_collapsed', False))
        self.items = {}
        self.setFixedWidth(self.RAIL if self.collapsed else self.EXPANDED)
        outer = vbox(self)

        self.brand = QWidget()
        row = hbox(self.brand, (18, 20, 12, 14), 11)
        row.addWidget(BrandMark(34))
        self.brand_text = QWidget()
        col = vbox(self.brand_text, (0, 0, 0, 0), 0)
        col.addWidget(label('Caldera', 'brandName'))
        col.addWidget(label('Engineering workbench', 'faint'))
        row.addWidget(self.brand_text, 1)
        outer.addWidget(self.brand)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.viewport().setAutoFillBackground(False)
        self.inner = QWidget()
        self.inner.setObjectName('navInner')
        self.inner.setStyleSheet('QWidget#navInner { background: transparent; }')
        self.inner_lay = vbox(self.inner, (0, 2, 0, 10), 1)
        self.scroll.setWidget(self.inner)
        outer.addWidget(self.scroll, 1)

        self.bottom = QWidget()
        self.bottom_lay = vbox(self.bottom, (0, 8, 0, 12), 1)
        outer.addWidget(self.bottom)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(170)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(lambda v: self.setFixedWidth(int(v)))
        self.brand_text.setVisible(not self.collapsed)
        self.rebuild()

    # ------------------------------------------------------------------ building
    def _add(self, lay, key, text, icon_name, favourable=False):
        win = self.win
        item = NavItem(win, key, text, icon_name, favourable)
        item.set_state(selected=(key == win.current), fav=win.is_favorite(key), collapsed=self.collapsed)
        lay.addWidget(item)
        self.items.setdefault(key, []).append(item)

    def _header(self, text, color, count):
        hidden = text in self.win.data.get('nav_collapsed', [])
        head = NavHeader(text, color, count, expanded=not hidden)
        head.collapsed_rail = self.collapsed
        head.clicked.connect(lambda t=text: self.toggle_section(t))
        self.inner_lay.addWidget(head)
        return not hidden or self.collapsed

    def rebuild(self):
        t = T()
        clear_layout(self.inner_lay)
        clear_layout(self.bottom_lay)
        self.items = {}
        for key in ('Overview', 'Calculation History', 'Project Dashboard'):
            icon_name, short = SYSTEM_PAGES[key]
            self._add(self.inner_lay, key, short, icon_name)
        pinned = [n for n in self.win.data.get('favorites', []) if n in TOOLS]
        if pinned:
            if self._header('Pinned', t['warn'], len(pinned)):
                for n in pinned:
                    self._add(self.inner_lay, n, n, icon_of(n), True)
        for cat, names in CATEGORIES.items():
            if self._header(cat, t['cats'][cat], len(names)):
                for n in names:
                    self._add(self.inner_lay, n, n, icon_of(n), n in TOOLS)
        self.inner_lay.addStretch(1)
        for key in ('Settings', 'About Caldera'):
            icon_name, short = SYSTEM_PAGES[key]
            self._add(self.bottom_lay, key, short, icon_name)

    def toggle_section(self, name):
        hidden = self.win.data.setdefault('nav_collapsed', [])
        if name in hidden:
            hidden.remove(name)
        else:
            hidden.append(name)
        self.win.schedule_save()
        self.rebuild()

    # ------------------------------------------------------------------ state
    def set_selected(self, key):
        for k, lst in self.items.items():
            for item in lst:
                item.set_state(selected=(k == key))

    def set_collapsed(self, flag):
        self.collapsed = bool(flag)
        self.win.data['sidebar_collapsed'] = self.collapsed
        self.win.schedule_save()
        self.brand_text.setVisible(not self.collapsed)
        self.rebuild()
        self._anim.stop()
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(self.RAIL if self.collapsed else self.EXPANDED)
        self._anim.start()


# =========================================================================== tabs
class TabChip(QWidget):
    """One browser-style tab: icon, title, close button. Drawn by hand so it matches the theme exactly."""

    H = 36

    def __init__(self, bar, index, title, icon_name, active, closable):
        super().__init__()
        self.bar, self.index, self.title, self.icon_name = bar, index, title, icon_name
        self.active, self.closable, self._hover, self._hover_close = active, closable, False, False
        self.setFixedHeight(self.H)
        self.setMinimumWidth(112)
        self.setMaximumWidth(236)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setToolTip(title)

    def sizeHint(self):
        return QSize(200, self.H)

    def _close_rect(self):
        return QRectF(self.width() - 30, (self.H - 20) / 2, 20, 20)

    def enterEvent(self, ev):
        self._hover = True
        self.update()
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        self._hover = self._hover_close = False
        self.update()
        super().leaveEvent(ev)

    def mouseMoveEvent(self, ev):
        over = self._show_close() and self._close_rect().contains(ev.position())
        if over != self._hover_close:
            self._hover_close = over
            self.update()

    def _show_close(self):
        return self.closable and (self.active or self._hover)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.MiddleButton:
            if self.closable:
                self.bar.win.close_tab(self.index)
        elif ev.button() == Qt.MouseButton.LeftButton:
            if self._show_close() and self._close_rect().contains(ev.position()):
                self.bar.win.close_tab(self.index)
            else:
                self.bar.win.activate_tab(self.index)

    def contextMenuEvent(self, ev):
        win = self.bar.win
        menu = QMenu(self)
        menu.addAction('New tab').triggered.connect(lambda checked=False: win.new_tab())
        menu.addAction('Duplicate tab').triggered.connect(lambda checked=False: win.duplicate_tab(self.index))
        menu.addSeparator()
        close = menu.addAction('Close tab')
        close.setEnabled(self.closable)
        close.triggered.connect(lambda checked=False: win.close_tab(self.index))
        others = menu.addAction('Close other tabs')
        others.setEnabled(len(win.tabs) > 1)
        others.triggered.connect(lambda checked=False: win.close_other_tabs(self.index))
        menu.exec(ev.globalPos())

    def paintEvent(self, _ev):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        body = QRectF(0.5, 0.5, self.width() - 1, self.H + 12)       # bottom corners hang below the widget (clipped)
        if self.active:
            p.setPen(QPen(QColor(t['border2']), 1))
            p.setBrush(QColor(t['bg']))
            p.drawRoundedRect(body, 10, 10)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t['accent']))
            p.drawRoundedRect(QRectF(14, 0.5, self.width() - 28, 2.2), 1.1, 1.1)
        elif self._hover:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t['hover']))
            p.drawRoundedRect(body, 10, 10)
        tint = t['accent'] if self.active else t['muted']
        p.drawPixmap(14, (self.H - 16) // 2 + 1, icons.pixmap(self.icon_name, tint, 16))
        f = QFont(self.font())
        f.setPixelSize(13)
        f.setWeight(QFont.Weight.DemiBold if self.active else QFont.Weight.Medium)
        p.setFont(f)
        p.setPen(QColor(t['text'] if self.active else t['muted']))
        room = int(self.width() - 14 - 16 - 10 - (34 if self.closable else 12))
        text = QFontMetrics(f).elidedText(self.title, Qt.TextElideMode.ElideRight, max(room, 10))
        p.drawText(QRectF(38, 1, room + 4, self.H), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        if self._show_close():
            r = self._close_rect()
            if self._hover_close:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(t['border']))
                p.drawRoundedRect(r, 6, 6)
            p.drawPixmap(int(r.left() + 4), int(r.top() + 4), icons.pixmap('x', t['text'] if self._hover_close else t['faint'], 12, 2.0, False, 2.2))


class TabBar(QFrame):
    """Browser-style tab strip. Navigating changes the active tab; only the + button (or Ctrl+T) opens a new one."""

    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName('tabbar')
        self.setFixedHeight(48)
        outer = hbox(self, (14, 12, 14, 0), 4)
        self.chips = hbox(None, (0, 0, 0, 0), 4)
        outer.addLayout(self.chips)
        self.plus = icon_button('plus', 'New tab   Ctrl+T', win.new_tab, 32)
        outer.addWidget(self.plus, 0, Qt.AlignmentFlag.AlignTop)
        outer.addStretch(1)
        self.refresh()

    def refresh(self):
        win = self.win
        clear_layout(self.chips)
        for i, tab in enumerate(win.tabs):
            title = SYSTEM_PAGES[tab.page][1] if tab.page in SYSTEM_PAGES else tab.page
            self.chips.addWidget(TabChip(self, i, title, icon_of(tab.page), i == win.active, len(win.tabs) > 1), 1)
        self.plus.setIcon(icons.icon('plus', T()['muted'], 18))


# =========================================================================== top bar
class Topbar(QFrame):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.setObjectName('topbar')
        self.setFixedHeight(60)
        lay = hbox(self, (14, 10, 18, 10), 8)
        self.toggle = icon_button('layout', 'Toggle sidebar   Ctrl+B', win.toggle_sidebar, 36)
        self.back = icon_button('chevron_left', 'Back   Alt+←', win.go_back, 36)
        self.fwd = icon_button('chevron_right', 'Forward   Alt+→', win.go_forward, 36)
        for w in (self.toggle, self.back, self.fwd):
            lay.addWidget(w)
        lay.addSpacing(8)

        self.search = QPushButton()
        self.search.setObjectName('searchBtn')
        self.search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search.setFixedHeight(38)
        self.search.setMinimumWidth(220)
        self.search.setMaximumWidth(500)
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search.clicked.connect(lambda checked=False: win.open_palette())
        inner = hbox(self.search, (12, 0, 10, 0), 9)
        inner.addWidget(icon_label('search', T()['faint'], 16))
        inner.addWidget(label('Search calculators, pages and actions…', 'faint'), 1)
        for child in self.search.findChildren(QWidget):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        lay.addWidget(self.search, 1)
        lay.addStretch(2)

        self.project_btn = QPushButton()
        self.project_btn.setObjectName('projBtn')
        self.project_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.project_btn.setToolTip('Active project')
        self.project_btn.clicked.connect(lambda checked=False: self.project_menu())
        lay.addWidget(self.project_btn)
        self.theme_btn = icon_button('moon', 'Switch light / dark', win.toggle_dark, 38)
        lay.addWidget(self.theme_btn)
        self.refresh()

    def refresh(self):
        t = T()
        win = self.win
        self.back.setEnabled(bool(win._back))
        self.fwd.setEnabled(bool(win._fwd))
        self.back.setIcon(icons.icon('chevron_left', t['muted'] if win._back else t['border2'], 18))
        self.fwd.setIcon(icons.icon('chevron_right', t['muted'] if win._fwd else t['border2'], 18))
        self.toggle.setIcon(icons.icon('layout', t['muted'], 18))
        self.theme_btn.setIcon(icons.icon('sun' if t['dark'] else 'moon', t['muted'], 18))
        self.project_btn.setIcon(icons.icon('folder', t['accent'], 16))
        self.project_btn.setIconSize(QSize(16, 16))
        self.project_btn.setText('  ' + win.data['active_project'] + '  ')

    def project_menu(self):
        win = self.win
        menu = QMenu(self)
        for name in win.data['projects']:
            act = menu.addAction(('✓  ' if name == win.data['active_project'] else '      ') + name)
            act.triggered.connect(lambda checked=False, n=name: win.set_active_project(n))
        menu.addSeparator()
        menu.addAction('New project…').triggered.connect(lambda checked=False: win.new_project())
        menu.addAction('Manage projects').triggered.connect(lambda checked=False: win.navigate('Project Dashboard'))
        menu.exec(self.project_btn.mapToGlobal(QPoint(0, self.project_btn.height() + 6)))


# =========================================================================== command palette
def _subsequence(needle, hay):
    it = iter(hay)
    return all(ch in it for ch in needle)


def _score(q, e):
    """Lower is better; None means no match."""
    title = e['title'].lower()
    if title.startswith(q):
        return 0
    words = title.replace('/', ' ').replace('&', ' ').replace(',', ' ').split()
    if any(w.startswith(q) for w in words):
        return 1
    if q in title:
        return 2
    if len(q) > 1 and _subsequence(q, title):
        return 3
    if q in (e.get('hint', '') + ' ' + e.get('group', '')).lower():
        return 4
    return None


class CommandPalette(QDialog):
    """Ctrl+K launcher: type to filter every calculator, page and quick action."""

    def __init__(self, win, entries):
        super().__init__(win)
        self.win, self.entries, self.shown = win, entries, []
        self.setObjectName('palette')
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(660)
        t = T()
        outer = vbox(self)
        bar = QFrame()
        bar.setObjectName('paletteInput')
        row = hbox(bar, (20, 10, 20, 10), 12)
        row.addWidget(icon_label('search', t['muted'], 20))
        self.edit = QLineEdit()
        self.edit.setFrame(False)
        self.edit.setPlaceholderText('Search calculators, pages and actions…')
        self.edit.textChanged.connect(self.refilter)
        self.edit.installEventFilter(self)
        row.addWidget(self.edit, 1)
        row.addWidget(label('esc', 'kbd'))
        outer.addWidget(bar)

        self.list = QListWidget()
        self.list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setFixedHeight(392)
        self.list.itemClicked.connect(lambda _it: self.activate())
        outer.addWidget(self.list)

        foot = QFrame()
        foot.setObjectName('paletteFoot')
        fr = hbox(foot, (20, 9, 20, 9), 8)
        for key, text in (('↑ ↓', 'navigate'), ('↵', 'open'), ('esc', 'close')):
            fr.addWidget(label(key, 'kbd'))
            fr.addWidget(label(text, 'faint'))
            fr.addSpacing(10)
        fr.addStretch(1)
        outer.addWidget(foot)
        self.refilter()

    # ------------------------------------------------------------------ filtering
    def refilter(self, *_):
        q = self.edit.text().strip().lower()
        if q:
            scored = []
            for i, e in enumerate(self.entries):
                s = _score(q, e)
                if s is not None:
                    scored.append((s, i, e))
            scored.sort(key=lambda x: (x[0], x[1]))
            self.shown = [e for _s, _i, e in scored][:40]
        else:
            self.shown = list(self.entries)
        t = T()
        self.list.clear()
        for e in self.shown:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 54))
            self.list.addItem(item)
            w = QWidget()
            w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            r = hbox(w, (10, 5, 12, 5), 12)
            r.addWidget(IconTile(e['icon'], e['color'], 34))
            mid = vbox(None, (0, 0, 0, 0), 1)
            mid.addWidget(label(e['title'], 'h3'))
            if e.get('hint'):
                hint = label(e['hint'], 'faint')
                mid.addWidget(hint)
            r.addLayout(mid, 1)
            tag = label(e['group'], 'faint')
            tag.setStyleSheet('color: %s;' % e['color'])
            r.addWidget(tag)
            self.list.setItemWidget(item, w)
        if self.shown:
            self.list.setCurrentRow(0)
        else:
            self.list.addItem(QListWidgetItem())
            self.list.item(0).setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.item(0).setSizeHint(QSize(0, 90))
            empty = label('No matches for “%s”' % self.edit.text().strip(), 'muted')
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list.setItemWidget(self.list.item(0), empty)

    def _move(self, delta):
        if not self.shown:
            return
        row = min(max(self.list.currentRow() + delta, 0), len(self.shown) - 1)
        self.list.setCurrentRow(row)

    def activate(self):
        row = self.list.currentRow()
        if not (0 <= row < len(self.shown)):
            return
        action = self.shown[row]['run']
        self.close()
        QTimer.singleShot(0, action)

    # ------------------------------------------------------------------ events
    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() == QEvent.Type.KeyPress:
            key = ev.key()
            if key == Qt.Key.Key_Down:
                self._move(1)
                return True
            if key == Qt.Key.Key_Up:
                self._move(-1)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.activate()
                return True
        return super().eventFilter(obj, ev)

    def showEvent(self, ev):
        super().showEvent(ev)
        win = self.win
        top = win.mapToGlobal(QPoint(0, 0))
        self.move(top.x() + (win.width() - self.width()) // 2, top.y() + 84)
        self.edit.setFocus()
