"""Caldera - Qt 6 engineering workbench. This module is the main window: navigation, persistence and actions.
The look lives in caldera/ui/ (theme, widgets, chrome, pages_*)."""
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QWidget

from . import __version__, exports, workspace
from .registry import TOOL_PAGES, TOOLS
from .toolmeta import CATEGORIES, SYSTEM_PAGES, blurb_of, icon_of
from .ui import pages_core, pages_data, pages_tools, theme
from .ui.chrome import CommandPalette, Sidebar, TabBar, Topbar, choose, confirm, prompt, prompt_multiline
from .ui.pages_data import empty_state
from .ui.widgets import ScrollPage, Toast, button, fade_in, hbox, vbox

ASSETS = Path(__file__).parent / 'assets'
DATA = workspace.data_dir()
STORE = DATA / 'workspace.json'

TABLE_PAGES = {
    'Electrical Load Summary': ['Load name', 'Voltage (V)', 'Phase', 'Current (A)'],
    'Wire List / CSV Generator': ['Wire ID', 'From', 'To', 'Gauge', 'Color', 'Notes'],
}
PAGE_BUILDERS = {
    'Overview': pages_core.overview_page,
    'Calculation History': pages_data.history_page,
    'Project Dashboard': pages_data.project_page,
    'Compare Calculations': pages_data.compare_page,
    'Settings': pages_tools.settings_page,
    'About Caldera': pages_tools.about_page,
    'Reference Tables': pages_tools.reference_page,
    'Seal Compatibility': pages_tools.seals_page,
    'Methodology': pages_tools.methodology_page,
    'Test Report Generator': pages_tools.report_page,
}
PAGE_HINTS = {'Overview': 'Dashboard, pinned tools and recent activity', 'Calculation History': 'Every saved result',
              'Project Dashboard': 'Organise results into projects', 'Settings': 'Theme, precision and backups',
              'About Caldera': 'Version, license and disclaimer'}
PAGE_TITLES = {'Overview': 'Home', 'Project Dashboard': 'Projects'}


class Tab:
    """One tab: which page it shows plus its own back / forward history."""

    def __init__(self, page='Overview'):
        self.page, self.back, self.fwd = page, [], []


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.store_path = STORE
        self.data, self.notice = workspace.load(STORE)
        self.page = None
        self.tabs, self.active = self._restore_tabs()
        self.history_project = 'All projects'
        self._palette = None
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(700)
        self._save_timer.timeout.connect(self.save)

        name = self.data.get('theme')
        self._apply_theme(name if name in theme.THEMES else theme.DEFAULT_THEME)
        self.setWindowTitle('Caldera')
        self.setWindowIcon(QIcon(str(ASSETS / 'caldera.svg')))
        try:
            w, h = (int(v) for v in self.data['window'][:2])
        except (KeyError, TypeError, ValueError):
            w, h = 1360, 860
        self.resize(max(w, 1000), max(h, 660))
        self.setMinimumSize(1000, 660)

        self.central = QWidget()
        self.setCentralWidget(self.central)
        root = hbox(self.central)
        self.sidebar = Sidebar(self)
        root.addWidget(self.sidebar)
        right = QWidget()
        col = vbox(right)
        self.tabbar = TabBar(self)
        col.addWidget(self.tabbar)
        self.topbar = Topbar(self)
        col.addWidget(self.topbar)
        self.host = QWidget()
        self.host_lay = vbox(self.host)
        col.addWidget(self.host, 1)
        root.addWidget(right, 1)
        self.toast_w = Toast(self.central)

        for keys, fn in (('Ctrl+K', self.open_palette), ('Ctrl+L', self.open_palette), ('Ctrl+B', self.toggle_sidebar),
                         ('Ctrl+Return', self.commit_page), ('Ctrl+Enter', self.commit_page),
                         ('Ctrl+S', self.save_page_result), ('Alt+Left', self.go_back), ('Alt+Right', self.go_forward),
                         ('Ctrl+T', self.new_tab), ('Ctrl+W', self.close_current_tab), ('Ctrl+Tab', self.next_tab),
                         ('Ctrl+Shift+Tab', self.prev_tab), ('Ctrl+PgDown', self.next_tab), ('Ctrl+PgUp', self.prev_tab)):
            QShortcut(QKeySequence(keys), self).activated.connect(fn)

        self._show_current()
        if self.notice:
            QTimer.singleShot(500, lambda: self.toast(self.notice, 'warn'))

    # ------------------------------------------------------------------ persistence
    @property
    def precision(self):
        return int(self.data.get('precision', 3))

    def save(self):
        self._save_timer.stop()
        try:
            workspace.save(self.store_path, self.data)
        except OSError as e:
            self.toast('Could not save workspace: %s' % e, 'bad')

    def schedule_save(self):
        self._save_timer.start()

    def update_option(self, key, value):
        self.data[key] = value
        self.schedule_save()

    def closeEvent(self, ev):
        self.data['window'] = [self.width(), self.height()]
        self.save()
        super().closeEvent(ev)

    # ------------------------------------------------------------------ feedback + dialogs
    def toast(self, text, kind='good'):
        self.toast_w.show_message(text, kind)

    def confirm(self, title, text, ok='Delete', danger=True):
        return confirm(self, title, text, ok, danger)

    def ask_text(self, title, caption, value='', ok='Save'):
        return prompt(self, title, caption, value, ok)

    def pick_save(self, title, default_name, filt, ext=None):
        start = Path(self.data.get('last_dir') or Path.home())
        path, _ = QFileDialog.getSaveFileName(self, title, str(start / default_name), filt)
        if path:
            if ext:
                path = workspace.ensure_ext(path, ext)
            self.data['last_dir'] = str(Path(path).parent)
        return path

    def pick_open(self, title, filt):
        path, _ = QFileDialog.getOpenFileName(self, title, str(self.data.get('last_dir') or Path.home()), filt)
        return path

    # ------------------------------------------------------------------ theme
    def _apply_theme(self, name):
        self.data['theme'] = name
        self.data['dark_theme' if theme.THEMES[name]['dark'] else 'light_theme'] = name
        theme.apply(QApplication.instance(), name)

    def set_theme(self, name):
        if name not in theme.THEMES or name == self.data.get('theme'):
            return
        self._apply_theme(name)
        self.schedule_save()
        QTimer.singleShot(0, self._reskin)   # deferred: the click that triggered this may live on a page we rebuild

    def _reskin(self):
        self.sidebar.rebuild()
        self.topbar.refresh()
        self.navigate(self.current, force=True, record=False)

    def toggle_dark(self):
        if theme.current()['dark']:
            self.set_theme(self.data.get('light_theme', 'Light'))
        else:
            self.set_theme(self.data.get('dark_theme', 'Obsidian'))

    # ------------------------------------------------------------------ navigation
    def known(self, name):
        return name in TOOL_PAGES or name in SYSTEM_PAGES

    def build_page(self, name):
        try:
            if name in TOOLS:
                return pages_core.calculator_page(self, name)
            if name in TABLE_PAGES:
                return pages_tools.table_editor_page(self, name, TABLE_PAGES[name])
            return PAGE_BUILDERS[name](self)
        except Exception as e:   # a broken page must never take the whole app down
            traceback.print_exc()
            page = ScrollPage(max_width=720)
            page.col.addWidget(empty_state('alert', 'This page could not be displayed', '%s: %s' % (type(e).__name__, e),
                                           button('Back to Home', 'primary', 'home', lambda: self.navigate('Overview'))))
            page.col.addStretch(1)
            return page

    # ------------------------------------------------------------------ tabs
    @property
    def tab(self):
        return self.tabs[self.active]

    @property
    def current(self):
        return self.tab.page

    @property
    def _back(self):
        return self.tab.back

    @property
    def _fwd(self):
        return self.tab.fwd

    def _restore_tabs(self):
        saved = self.data.get('tabs')
        try:
            pages = [p for p in saved['pages'] if self.known(p)]
            if pages:
                return [Tab(p) for p in pages], min(max(int(saved.get('active', 0)), 0), len(pages) - 1)
        except (TypeError, KeyError, ValueError, AttributeError):
            pass
        return [Tab('Overview')], 0

    def _tabs_changed(self):
        self.data['tabs'] = {'pages': [t.page for t in self.tabs], 'active': self.active}
        self.schedule_save()
        self.tabbar.refresh()

    def new_tab(self, page='Overview'):
        """Open a new tab (only ever triggered explicitly: + button, Ctrl+T, palette)."""
        self.tabs.append(Tab(page if self.known(page) else 'Overview'))
        self.active = len(self.tabs) - 1
        self._show_current()

    def duplicate_tab(self, index):
        src = self.tabs[index]
        tab = Tab(src.page)
        tab.back = list(src.back)
        self.tabs.insert(index + 1, tab)
        self.active = index + 1
        self._show_current()

    def activate_tab(self, index):
        if 0 <= index < len(self.tabs) and (index != self.active or self.page is None):
            self.active = index
            self._show_current()

    def close_tab(self, index):
        if not 0 <= index < len(self.tabs):
            return
        if len(self.tabs) == 1:                      # never leave the window with no tab: reset it to Home instead
            self.tabs[0] = Tab('Overview')
            self._show_current()
            return
        was_active = index == self.active
        del self.tabs[index]
        if index < self.active:
            self.active -= 1
        self.active = min(self.active, len(self.tabs) - 1)
        if was_active:
            self._show_current()
        else:
            self._tabs_changed()
            self.topbar.refresh()

    def close_current_tab(self):
        self.close_tab(self.active)

    def close_other_tabs(self, index):
        if 0 <= index < len(self.tabs):
            self.tabs = [self.tabs[index]]
            self.active = 0
            self._show_current()

    def next_tab(self):
        self.activate_tab((self.active + 1) % len(self.tabs))

    def prev_tab(self):
        self.activate_tab((self.active - 1) % len(self.tabs))

    # ------------------------------------------------------------------ navigation
    def navigate(self, name, force=False, record=True):
        """Show `name` in the CURRENT tab. (Tabs are only created by new_tab.)"""
        if not self.known(name):
            name = 'Overview'
        tab = self.tab
        if name == tab.page and not force and self.page is not None:
            return
        if record and tab.page and tab.page != name:
            tab.back.append(tab.page)
            del tab.back[:-60]
            tab.fwd.clear()
        tab.page = name
        self._show_current()

    def _show_current(self):
        name = self.current
        new = self.build_page(name)
        old, self.page = self.page, new
        self.host_lay.addWidget(new)
        if old is not None:
            self.host_lay.removeWidget(old)
            old.setParent(None)
            old.deleteLater()
        fade_in(new, 170)
        self.sidebar.set_selected(name)
        self.topbar.refresh()
        self._tabs_changed()
        self.setWindowTitle('%s — Caldera' % PAGE_TITLES.get(name, name))

    def open_page(self, name):
        """Rebuild a page in place (used after data changes)."""
        self.navigate(name, force=True, record=False)

    def go_back(self):
        if self._back:
            self._fwd.append(self.current)
            self.navigate(self._back.pop(), force=True, record=False)

    def go_forward(self):
        if self._fwd:
            self._back.append(self.current)
            self.navigate(self._fwd.pop(), force=True, record=False)

    def toggle_sidebar(self):
        self.sidebar.set_collapsed(not self.sidebar.collapsed)

    def open_methodology(self, tool):
        self.methodology_focus = tool
        self.navigate('Methodology')

    def open_with_inputs(self, tool, inputs):
        self.data['drafts'][tool] = [str(v) for v in inputs]
        self.navigate(tool, force=True)

    def commit_page(self):
        if hasattr(self.page, 'commit'):
            self.page.commit()

    def save_page_result(self):
        if hasattr(self.page, 'save_result'):
            self.page.save_result()

    # ------------------------------------------------------------------ command palette
    def palette_entries(self):
        t = theme.current()
        out = []
        for key, (icon_name, short) in SYSTEM_PAGES.items():
            out.append(dict(title=PAGE_TITLES.get(key, key), hint=PAGE_HINTS.get(key, ''), icon=icon_name,
                            color=t['accent'], group='Page', run=lambda k=key: self.navigate(k)))
        for cat, names in CATEGORIES.items():
            for n in names:
                out.append(dict(title=n, hint=blurb_of(n), icon=icon_of(n), color=t['cats'][cat], group=cat,
                                run=lambda n=n: self.navigate(n)))
        for title, icon_name, fn in (('New tab', 'plus', self.new_tab),
                                     ('New project…', 'plus', self.new_project),
                                     ('Import project (.caldera)…', 'upload', self.import_project),
                                     ('Export active project (.caldera)…', 'download', lambda: self.export_project(self.data['active_project'])),
                                     ('Switch light / dark theme', 'sun', self.toggle_dark),
                                     ('Collapse or expand sidebar', 'layout', self.toggle_sidebar),
                                     ('Export history as CSV…', 'download', self.export_history),
                                     ('Export history as Excel…', 'table', self.export_history_xlsx),
                                     ('Back up workspace…', 'download', self.export_data),
                                     ('Restore workspace backup…', 'upload', self.restore_data)):
            out.append(dict(title=title, hint='', icon=icon_name, color=t['muted'], group='Action', run=fn))
        return out

    def open_palette(self):
        if self._palette is not None:
            try:
                self._palette.close()
            except RuntimeError:
                pass
            self._palette = None
            return
        dlg = CommandPalette(self, self.palette_entries())
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dlg.finished.connect(lambda _r=0: setattr(self, '_palette', None))
        self._palette = dlg
        dlg.show()

    # ------------------------------------------------------------------ favourites + history
    def is_favorite(self, name):
        return name in self.data.get('favorites', [])

    def toggle_favorite(self, name):
        fav = self.data.setdefault('favorites', [])
        if name in fav:
            fav.remove(name)
            self.toast('Unpinned “%s”' % name, 'info')
        else:
            fav.append(name)
            self.toast('Pinned “%s” to the sidebar' % name)
        self.save()
        self.sidebar.rebuild()
        if hasattr(self.page, 'on_fav_changed'):
            self.page.on_fav_changed()

    def add_history(self, tool, values, text):
        project = self.data['active_project']
        self.data['history'].append({'date': datetime.now().isoformat(timespec='seconds'), 'tool': tool,
                                     'project': project, 'inputs': list(values), 'result': text})
        self.save()
        self.toast('Saved to “%s”' % project)

    # ------------------------------------------------------------------ projects
    def new_project(self):
        name = self.ask_text('New project', 'Project name', '', 'Create')
        if not name:
            return
        if name in self.data['projects'] or name in self.data['archived_projects']:
            self.toast('A project named “%s” already exists' % name, 'warn')
            return
        self.data['projects'].append(name)
        self.data['active_project'] = name
        self.save()
        self.topbar.refresh()
        self.navigate('Project Dashboard', force=True)
        self.toast('Created “%s” and made it active' % name)

    def set_active_project(self, name):
        if name not in self.data['projects']:
            return
        self.data['active_project'] = name
        self.save()
        self.topbar.refresh()
        if self.current == 'Project Dashboard':
            self.open_page(self.current)
        self.toast('Active project: %s' % name, 'info')

    def show_history_for(self, name):
        self.history_project = name
        self.navigate('Calculation History', force=True)

    def rename_project(self, old):
        new = self.ask_text('Rename project', 'New name', old)
        if not new or new == old:
            return
        if new in self.data['projects'] or new in self.data['archived_projects']:
            self.toast('A project named “%s” already exists' % new, 'warn')
            return
        d = self.data
        d['projects'] = [new if p == old else p for p in d['projects']]
        for r in d['history']:
            if r.get('project') == old:
                r['project'] = new
        notes = d.setdefault('project_notes', {})
        if old in notes:
            notes[new] = notes.pop(old)
        if d['active_project'] == old:
            d['active_project'] = new
        if self.history_project == old:
            self.history_project = new
        self.save()
        self.topbar.refresh()
        self.open_page('Project Dashboard')
        self.toast('Renamed to “%s”' % new)

    def archive_project(self, name):
        if name == 'General':
            self.toast('The General project cannot be archived', 'info')
            return
        if not self.confirm('Archive project', 'Archive “%s”? Its saved calculations are kept and you can restore it '
                            'at any time.' % name, 'Archive', danger=False):
            return
        d = self.data
        d['projects'].remove(name)
        d.setdefault('archived_projects', []).append(name)
        if d['active_project'] == name:
            d['active_project'] = 'General'
        self.save()
        self.topbar.refresh()
        self.open_page('Project Dashboard')
        self.toast('Archived “%s”' % name, 'info')

    def restore_project(self, name):
        d = self.data
        if name in d.get('archived_projects', []):
            d['archived_projects'].remove(name)
            if name not in d['projects']:
                d['projects'].append(name)
            self.save()
            self.open_page('Project Dashboard')
            self.toast('Restored “%s”' % name)

    def edit_project_notes(self, name):
        notes = self.data.setdefault('project_notes', {})
        text = prompt_multiline(self, 'Project notes', name, notes.get(name, ''))
        if text is not None:
            notes[name] = text
            self.save()
            self.open_page('Project Dashboard')
            self.toast('Notes saved')

    # ------------------------------------------------------------------ exports
    def write_pdf(self, path, title, blocks, subtitle=''):
        try:
            exports.build_pdf(path, title, blocks, subtitle)
        except ImportError:
            self.toast('Install reportlab to export PDF files', 'bad')
        except Exception as e:
            self.toast('PDF export failed: %s' % e, 'bad')
        else:
            self.toast('PDF exported')

    def export_project_pdf(self, name):
        path = self.pick_save('Export project PDF', 'caldera_%s.pdf' % name.replace(' ', '_'), 'PDF (*.pdf)')
        if not path:
            return
        rows = [r for r in self.data['history'] if r.get('project') == name]
        notes = self.data.get('project_notes', {}).get(name, '')
        self.write_pdf(path, 'Project: %s' % name, exports.project_blocks(name, notes, rows),
                       '%d saved calculation%s' % (len(rows), '' if len(rows) == 1 else 's'))

    def export_history(self):
        path = self.pick_save('Export history', 'caldera_history.csv', 'CSV (*.csv)')
        if path:
            try:
                exports.write_history_csv(path, self.data['history'])
                self.toast('History exported')
            except OSError as e:
                self.toast('Export failed: %s' % e, 'bad')

    def export_history_xlsx(self):
        path = self.pick_save('Export Excel history', 'caldera_history.xlsx', 'Excel (*.xlsx)')
        if not path:
            return
        try:
            exports.write_history_xlsx(path, self.data['history'])
            self.toast('Excel workbook exported')
        except ImportError:
            self.toast('Install openpyxl to export Excel workbooks', 'bad')
        except OSError as e:
            self.toast('Export failed: %s' % e, 'bad')

    def export_data(self):
        name = 'caldera_workspace_%s%s' % (datetime.now().strftime('%Y-%m-%d'), workspace.BACKUP_EXT)
        path = self.pick_save('Back up workspace', name, 'Caldera backup (*.caldera_backup)', workspace.BACKUP_EXT)
        if path:
            try:
                Path(path).write_text(json.dumps(workspace.backup_payload(self.data, __version__), indent=2,
                                                 ensure_ascii=False), encoding='utf-8')
                self.toast('Backup written')
            except OSError as e:
                self.toast('Backup failed: %s' % e, 'bad')

    def restore_data(self):
        path = self.pick_open('Restore Caldera backup', 'Caldera backup (*.caldera_backup *.json);;All files (*)')
        if not path:
            return
        try:
            loaded = workspace.parse_backup(Path(path).read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError):
            self.toast('Could not read that file', 'bad')
            return
        except ValueError as e:
            self.toast(str(e), 'bad')
            return
        if not self.confirm('Restore backup', 'Replace the current workspace with this backup? This cannot be undone.',
                            'Replace workspace'):
            return
        self.data = workspace.sanitize(loaded)
        self.history_project = 'All projects'
        self.tabs, self.active = self._restore_tabs()
        self.save()
        name = self.data.get('theme')
        self._apply_theme(name if name in theme.THEMES else theme.DEFAULT_THEME)
        self.sidebar.set_collapsed(bool(self.data.get('sidebar_collapsed')))
        QTimer.singleShot(0, lambda: (self._reskin(), self.navigate('Overview')))
        self.toast('Workspace restored')

    # ------------------------------------------------------------------ .caldera project files
    def export_project(self, name):
        safe = ''.join(c if c.isalnum() or c in '-_ ' else '_' for c in name).strip().replace(' ', '_') or 'project'
        path = self.pick_save('Export project', safe + workspace.PROJECT_EXT, 'Caldera project (*.caldera)',
                              workspace.PROJECT_EXT)
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(workspace.project_payload(self.data, name, __version__), indent=2,
                                             ensure_ascii=False), encoding='utf-8')
            self.toast('Exported “%s”' % name)
        except OSError as e:
            self.toast('Export failed: %s' % e, 'bad')

    def import_project(self):
        path = self.pick_open('Import project', 'Caldera project (*.caldera);;All files (*)')
        if not path:
            return
        try:
            proj = workspace.parse_project(Path(path).read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError):
            self.toast('Could not read that file', 'bad')
            return
        except ValueError as e:
            self.toast(str(e), 'bad')
            return
        mode = 'new'
        if proj['name'] in set(self.data['projects']) | set(self.data['archived_projects']):
            pick = choose(self, 'Project already exists',
                          '“%s” is already in this workspace. Merge the imported results into it (results you already '
                          'have are skipped), or keep them separate as a new copy?' % proj['name'],
                          'Merge into existing', 'Import as a copy')
            if pick is None:
                return
            mode = 'merge' if pick == 'primary' else 'new'
        name, added, skipped = workspace.import_project(self.data, proj, mode)
        self.save()
        self.topbar.refresh()
        self.navigate('Project Dashboard', force=True)
        extra = ' (%d already present)' % skipped if skipped else ''
        self.toast('Imported “%s”: %d result%s%s' % (name, added, '' if added == 1 else 's', extra))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Caldera')
    app.setApplicationVersion(__version__)
    app.setOrganizationName('Nate Robertson')
    app.setDesktopFileName('caldera')
    theme.load_fonts(ASSETS)
    win = Window()
    win.show()
    return app.exec()
