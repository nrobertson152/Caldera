"""Design tokens and the global Qt stylesheet.

Everything visual flows from the token dicts below. Only opaque hex colours are used in the
stylesheet (blended in Python) so rendering is identical across Qt styles and platforms."""
import tempfile
from pathlib import Path

from .icons import svg_markup


def _rgb(h):
    h = h.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def mix(a, b, t):
    """Blend colour `a` toward `b` by fraction t (0..1). Returns '#rrggbb'."""
    ra, ga, ba = _rgb(a)
    rb, gb, bb = _rgb(b)
    return '#%02x%02x%02x' % (round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t))


def _theme(name, dark, bg, side, surface, raised, border, text, muted, faint, accent, accent2, **extra):
    t = dict(name=name, dark=dark, bg=bg, side=side, surface=surface, raised=raised, border=border,
             text=text, muted=muted, faint=faint, accent=accent, accent2=accent2,
             good='#34d399' if dark else '#15803d', warn='#fbbf24' if dark else '#b45309',
             bad='#f87171' if dark else '#b91c1c', serif=False)
    t.update(extra)
    # derived tones
    t['accent_soft'] = mix(t['surface'], t['accent'], 0.16 if dark else 0.12)
    t['accent_line'] = mix(t['border'], t['accent'], 0.55)
    t['hover'] = mix(t['surface'], t['text'], 0.05)
    t['border2'] = mix(t['border'], t['text'], 0.14)
    t['good_soft'] = mix(t['surface'], t['good'], 0.14)
    t['warn_soft'] = mix(t['surface'], t['warn'], 0.14)
    t['bad_soft'] = mix(t['surface'], t['bad'], 0.14)
    t['on_accent'] = '#ffffff' if not dark else '#1a1208'
    t['cats'] = {
        'Hydraulic': '#58a6ff' if dark else '#1d6fd8',
        'Pneumatic': '#2dd4bf' if dark else '#0f8f84',
        'Mechanical': '#fbbf24' if dark else '#b7791f',
        'Electrical': '#a78bfa' if dark else '#6d4bd8',
        'Utilities': '#94a3b8' if dark else '#5b6b80',
    }
    return t


THEMES = {
    'Obsidian': _theme('Obsidian', True, '#0e1014', '#0a0c0f', '#15181e', '#1b1f26', '#262b33',
                       '#e9ebee', '#9aa3af', '#667080', '#f08a4b', '#f6b45f'),
    'Midnight': _theme('Midnight', True, '#0a0f1e', '#070b16', '#111a30', '#16213b', '#22304f',
                       '#e6edfb', '#97a8c8', '#62759a', '#5b9dff', '#8b7bff'),
    'Graphite': _theme('Graphite', True, '#101213', '#0b0c0d', '#171a1b', '#1e2223', '#2a2f31',
                       '#e8eceb', '#98a3a1', '#657270', '#2dd4bf', '#5eead4'),
    'Light': _theme('Light', False, '#f4f5f8', '#ffffff', '#ffffff', '#f1f3f6', '#e3e6ec',
                    '#18202b', '#5a687a', '#8794a6', '#d4561f', '#ef8a3c'),
    'Terracotta': _theme('Terracotta', False, '#f3eee6', '#ebe4d9', '#fffdf9', '#f6f0e7', '#e1d7c8',
                         '#2e2924', '#74695d', '#a09384', '#b5573a', '#d68a54', serif=True),
}
DEFAULT_THEME = 'Obsidian'

SANS = ['Inter', 'Noto Sans', 'Ubuntu', 'Cantarell', 'DejaVu Sans']
SERIF = ['Source Serif 4', 'Noto Serif', 'DejaVu Serif']
MONO = ['JetBrains Mono', 'Cascadia Mono', 'Ubuntu Mono', 'DejaVu Sans Mono', 'Monospace']


def font_css(families):
    return ', '.join('"%s"' % f for f in families)


def _asset_dir():
    d = Path(tempfile.gettempdir()) / 'caldera-ui-cache'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _chevron_file(color, name):
    """Write a small SVG used for combo-box arrows; returns forward-slash path for QSS url()."""
    path = _asset_dir() / ('chev-%s-%s.svg' % (name, color.lstrip('#')))
    if not path.exists():
        path.write_text(svg_markup('chevron_down', color, stroke=2.2))
    return path.as_posix()


def _check_file(color):
    path = _asset_dir() / ('check-%s.svg' % color.lstrip('#'))
    if not path.exists():
        path.write_text(svg_markup('check', color, stroke=3.2))
    return path.as_posix()


def stylesheet(t):
    heading_font = font_css(SERIF if t['serif'] else SANS)
    arrow = _chevron_file(t['muted'], 'm')
    check = _check_file(t['on_accent'])
    return f'''
QMainWindow, QDialog, QMessageBox, QInputDialog {{ background: {t['bg']}; }}
QWidget {{ color: {t['text']}; font-size: 13px; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {t['raised']}; color: {t['text']}; border: 1px solid {t['border2']};
           border-radius: 6px; padding: 5px 8px; }}

QFrame#card {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 14px; }}
QFrame#cardLink {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 14px; }}
QFrame#cardLink:hover {{ border: 1px solid {t['accent_line']}; background: {t['hover']}; }}
QFrame#tile {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 12px; }}
QFrame#hero {{ background: {t['accent_soft']}; border: 1px solid {t['accent_line']}; border-radius: 14px; }}
QFrame#banner_good {{ background: {t['good_soft']}; border: 1px solid {mix(t['border'], t['good'], .5)}; border-radius: 10px; }}
QFrame#banner_bad {{ background: {t['bad_soft']}; border: 1px solid {mix(t['border'], t['bad'], .5)}; border-radius: 10px; }}
QFrame#banner_warn {{ background: {t['warn_soft']}; border: 1px solid {mix(t['border'], t['warn'], .5)}; border-radius: 10px; }}
QFrame#divider {{ background: {t['border']}; border: 0; max-height: 1px; min-height: 1px; }}
QFrame#sidebar {{ background: {t['side']}; border: 0; border-right: 1px solid {t['border']}; }}
QFrame#tabbar {{ background: {t['side']}; border: 0; }}
QFrame#topbar {{ background: {t['bg']}; border: 0; border-bottom: 1px solid {t['border']}; }}

QLabel#display {{ font-family: {heading_font}; font-size: 30px; font-weight: 700; }}
QLabel#h1 {{ font-family: {heading_font}; font-size: 26px; font-weight: 700; }}
QLabel#h2 {{ font-family: {heading_font}; font-size: 16px; font-weight: 600; }}
QLabel#h3 {{ font-size: 13px; font-weight: 600; }}
QLabel#muted {{ color: {t['muted']}; }}
QLabel#faint {{ color: {t['faint']}; font-size: 12px; }}
QLabel#eyebrow {{ color: {t['faint']}; font-size: 11px; font-weight: 600; }}
QLabel#metricValue {{ font-size: 22px; font-weight: 600; }}
QLabel#heroValue {{ font-size: 44px; font-weight: 700; color: {t['text']}; }}
QLabel#unit {{ color: {t['muted']}; font-size: 13px; font-weight: 500; }}
QLabel#mono {{ font-family: {font_css(MONO)}; font-size: 12px; color: {t['text']}; }}
QLabel#pill {{ background: {t['accent_soft']}; color: {t['accent']}; border-radius: 9px; padding: 2px 9px;
              font-size: 11px; font-weight: 600; }}
QLabel#pillMuted {{ background: {t['raised']}; color: {t['muted']}; border-radius: 9px; padding: 2px 9px;
                   font-size: 11px; font-weight: 600; }}
QLabel#pillGood {{ background: {t['good_soft']}; color: {t['good']}; border-radius: 9px; padding: 2px 9px;
                  font-size: 11px; font-weight: 600; }}
QLabel#pillWarn {{ background: {t['warn_soft']}; color: {t['warn']}; border-radius: 9px; padding: 2px 9px;
                  font-size: 11px; font-weight: 600; }}
QLabel#pillBad {{ background: {t['bad_soft']}; color: {t['bad']}; border-radius: 9px; padding: 2px 9px;
                 font-size: 11px; font-weight: 600; }}

QFrame#field {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px; }}
QFrame#field:hover {{ border: 1px solid {t['border2']}; }}
QFrame#field[focused="true"] {{ border: 1px solid {t['accent']}; }}
QFrame#field[invalid="true"] {{ border: 1px solid {t['bad']}; }}
QFrame#field QLineEdit {{ background: transparent; border: 0; padding: 0; font-size: 14px;
                          selection-background-color: {t['accent']}; selection-color: {t['on_accent']}; }}
QFrame#field QLabel {{ color: {t['faint']}; font-size: 12px; font-weight: 500; }}

QLineEdit, QTextEdit, QPlainTextEdit {{ background: {t['raised']}; border: 1px solid {t['border']};
    border-radius: 10px; padding: 8px 11px; selection-background-color: {t['accent']};
    selection-color: {t['on_accent']}; }}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {t['accent']}; }}
QLineEdit:read-only, QTextEdit:read-only {{ background: {t['raised']}; }}

QComboBox {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px;
             padding: 0px 12px; min-height: 38px; font-size: 14px; }}
QComboBox:hover {{ border: 1px solid {t['border2']}; }}
QComboBox:focus, QComboBox:on {{ border: 1px solid {t['accent']}; }}
QComboBox::drop-down {{ border: 0; width: 28px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url({arrow}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{ background: {t['raised']}; border: 1px solid {t['border2']}; border-radius: 8px;
    padding: 4px; outline: 0; selection-background-color: {t['accent_soft']}; selection-color: {t['text']}; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 2px 8px; border-radius: 6px; }}

QPushButton {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px;
               padding: 8px 14px; font-weight: 500; }}
QPushButton:hover {{ background: {mix(t['raised'], t['text'], .06)}; border: 1px solid {t['border2']}; }}
QPushButton:pressed {{ background: {mix(t['raised'], t['text'], .1)}; }}
QPushButton:disabled {{ color: {t['faint']}; }}
QPushButton:focus {{ outline: 0; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t['accent']}, stop:1 {t['accent2']});
    color: {t['on_accent']}; border: 0; font-weight: 600; padding: 9px 18px; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
    stop:0 {mix(t['accent'], '#ffffff', .12)}, stop:1 {mix(t['accent2'], '#ffffff', .12)}); }}
QPushButton#primary:pressed {{ background: {mix(t['accent'], '#000000', .12)}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid transparent; color: {t['muted']}; }}
QPushButton#ghost:hover {{ background: {t['hover']}; color: {t['text']}; border: 1px solid {t['border']}; }}
QPushButton#danger {{ color: {t['bad']}; }}
QPushButton#danger:hover {{ background: {t['bad_soft']}; border: 1px solid {mix(t['border'], t['bad'], .5)}; }}
QPushButton#iconBtn {{ background: transparent; border: 1px solid transparent; border-radius: 9px; padding: 0; }}
QPushButton#iconBtn:hover {{ background: {t['hover']}; border: 1px solid {t['border']}; }}
QPushButton#searchBtn {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px;
    text-align: left; padding: 9px 12px; color: {t['faint']}; font-weight: 400; }}
QPushButton#searchBtn:hover {{ border: 1px solid {t['border2']}; color: {t['muted']}; }}
QPushButton#rowBtn {{ background: transparent; border: 0; border-radius: 10px; text-align: left; padding: 0; }}
QPushButton#rowBtn:hover {{ background: {t['hover']}; }}
QPushButton#chip {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 14px;
    padding: 5px 12px; font-size: 12px; color: {t['muted']}; }}
QPushButton#chip:hover {{ border: 1px solid {t['accent_line']}; color: {t['text']}; }}
QPushButton#linkBtn {{ background: transparent; border: 0; color: {t['accent']}; padding: 2px 4px; font-weight: 600; }}
QPushButton#linkBtn:hover {{ color: {t['accent2']}; }}

QTableWidget, QTableView {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 12px;
    gridline-color: {t['border']}; outline: 0; selection-background-color: {t['accent_soft']};
    selection-color: {t['text']}; alternate-background-color: {t['surface']}; }}
QTableWidget::item {{ padding: 6px 10px; border: 0; border-bottom: 1px solid {t['border']}; }}
QTableWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
QTableWidget QLineEdit {{ background: {t['raised']}; border: 1px solid {t['accent']}; border-radius: 6px; padding: 2px 6px; }}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{ background: {t['surface']}; color: {t['faint']}; border: 0;
    border-bottom: 1px solid {t['border']}; padding: 10px 12px; font-size: 11px; font-weight: 600; }}
QTableCornerButton::section {{ background: {t['surface']}; border: 0; }}

QListWidget {{ background: transparent; border: 0; outline: 0; }}
QListWidget::item {{ border-radius: 8px; padding: 2px; }}
QListWidget::item:selected {{ background: {t['accent_soft']}; color: {t['text']}; }}
QListWidget::item:hover {{ background: {t['hover']}; }}

QScrollArea {{ background: transparent; border: 0; }}
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 2px 2px 2px 0; }}
QScrollBar::handle:vertical {{ background: {t['border2']}; border-radius: 4px; min-height: 36px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: {t['faint']}; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0 2px 2px 2px; }}
QScrollBar::handle:horizontal {{ background: {t['border2']}; border-radius: 4px; min-width: 36px; margin: 2px 0; }}
QScrollBar::handle:horizontal:hover {{ background: {t['faint']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; background: none; border: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMenu {{ background: {t['raised']}; border: 1px solid {t['border2']}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 8px 16px 8px 12px; border-radius: 6px; margin: 1px 0; }}
QMenu::item:selected {{ background: {t['accent_soft']}; }}
QMenu::item:disabled {{ color: {t['faint']}; }}
QMenu::separator {{ height: 1px; background: {t['border']}; margin: 5px 8px; }}

QSplitter::handle {{ background: transparent; }}
QToolButton {{ background: transparent; border: 0; }}
QStatusBar {{ background: {t['bg']}; color: {t['faint']}; }}
QProgressBar {{ background: {t['raised']}; border: 0; border-radius: 3px; max-height: 6px; }}
QProgressBar::chunk {{ background: {t['accent']}; border-radius: 3px; }}

QDialog#sheet {{ background: {t['surface']}; border: 1px solid {t['border2']}; }}
QDialog#palette {{ background: {t['surface']}; border: 1px solid {t['border2']}; }}
QDialog#palette QLineEdit {{ background: transparent; border: 0; border-radius: 0; padding: 4px 2px; font-size: 16px; }}
QDialog#palette QListWidget {{ background: transparent; border: 0; outline: 0; }}
QDialog#palette QListWidget::item {{ border-radius: 9px; margin: 1px 6px; }}
QFrame#paletteInput {{ background: transparent; border: 0; border-bottom: 1px solid {t['border']}; }}
QFrame#paletteFoot {{ background: {t['raised']}; border: 0; border-top: 1px solid {t['border']}; }}
QLabel#kbd {{ background: {t['raised']}; color: {t['muted']}; border: 1px solid {t['border2']};
             border-radius: 5px; padding: 1px 6px; font-size: 11px; font-weight: 600; }}
QPushButton#projBtn {{ background: {t['raised']}; border: 1px solid {t['border']}; border-radius: 10px;
    padding: 0 12px; min-height: 36px; font-weight: 500; }}
QPushButton#projBtn:hover {{ border: 1px solid {t['border2']}; }}
QPushButton#projBtn::menu-indicator {{ image: none; width: 0; }}
QLabel#brandName {{ font-family: {heading_font}; font-size: 19px; font-weight: 700; }}
QPlainTextEdit {{ font-size: 13px; }}
QCheckBox {{ spacing: 10px; background: transparent; }}
QCheckBox:disabled {{ color: {t['faint']}; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1.5px solid {t['border2']};
    background: {t['raised']}; }}
QCheckBox::indicator:hover {{ border: 1.5px solid {t['accent_line']}; }}
QCheckBox::indicator:checked {{ background: {t['accent']}; border: 1.5px solid {t['accent']}; image: url({check}); }}
QCheckBox::indicator:disabled {{ background: {t['surface']}; border: 1.5px solid {t['border']}; }}
'''


def palette(t):
    """A QPalette matching the theme so any widget we do not style explicitly still looks native to it."""
    from PySide6.QtGui import QColor, QPalette
    p = QPalette()
    role = QPalette.ColorRole
    pairs = {role.Window: t['bg'], role.WindowText: t['text'], role.Base: t['raised'], role.AlternateBase: t['surface'],
             role.Text: t['text'], role.Button: t['raised'], role.ButtonText: t['text'], role.ToolTipBase: t['raised'],
             role.ToolTipText: t['text'], role.Highlight: t['accent'], role.HighlightedText: t['on_accent'],
             role.PlaceholderText: t['faint'], role.Link: t['accent']}
    for r, c in pairs.items():
        p.setColor(r, QColor(c))
    return p


def load_fonts(asset_dir):
    """Register the bundled Inter weights so the UI looks identical on every distro."""
    from PySide6.QtGui import QFontDatabase
    ok = False
    for f in sorted(Path(asset_dir).glob('fonts/*.otf')):
        ok = QFontDatabase.addApplicationFont(str(f)) >= 0 or ok
    return ok


def apply(app, name):
    """Install a theme on the whole application: base style, palette, default font and stylesheet."""
    from PySide6.QtGui import QFont
    t = set_current(name)
    app.setStyle('Fusion')
    app.setPalette(palette(t))
    font = QFont('Inter')
    font.setPixelSize(13)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    app.setStyleSheet(stylesheet(t))
    return t


# --------------------------------------------------------------------------- live theme state
_state = {'t': THEMES[DEFAULT_THEME]}


def current():
    """The active theme token dict (custom-painted widgets read this on every paint)."""
    return _state['t']


def set_current(name):
    _state['t'] = THEMES.get(name, THEMES[DEFAULT_THEME])
    return _state['t']
