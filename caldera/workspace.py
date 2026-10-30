"""Workspace persistence: defaults, validation and atomic save. Pure Python (no Qt) so it is unit-testable."""
import copy
import json
import os
from datetime import datetime
from pathlib import Path

DEFAULTS = {
    'theme': 'Obsidian', 'projects': ['General'], 'active_project': 'General', 'history': [], 'presets': {},
    'drafts': {}, 'favorites': [], 'project_notes': {}, 'archived_projects': [], 'tables': {},
    'methodology_notes': {}, 'units': 'US Customary', 'precision': 3, 'auto_save': False, 'nav_collapsed': [],
    'sidebar_collapsed': False, 'report_draft': {},
}
_DICT_KEYS = ('presets', 'drafts', 'project_notes', 'tables', 'report_draft', 'methodology_notes')
_LIST_KEYS = ('favorites', 'archived_projects', 'nav_collapsed')


def data_dir():
    base = os.environ.get('CALDERA_DATA')
    if base:
        return Path(base)
    xdg = os.environ.get('XDG_DATA_HOME')
    return (Path(xdg) if xdg else Path.home() / '.local' / 'share') / 'caldera'


def sanitize(data):
    """Coerce a loaded/restored workspace into the shape the UI assumes, without losing user data."""
    d = copy.deepcopy(DEFAULTS)
    if isinstance(data, dict):
        d.update(data)
    for k in _DICT_KEYS:
        if not isinstance(d.get(k), dict):
            d[k] = {}
    for k in _LIST_KEYS:
        if not isinstance(d.get(k), list):
            d[k] = []
    seen, projects = set(), []
    for p in (d['projects'] if isinstance(d.get('projects'), list) else []):
        if isinstance(p, str) and p.strip() and p not in seen:
            seen.add(p)
            projects.append(p)
    if 'General' not in seen:
        projects.insert(0, 'General')
    d['projects'] = projects
    if d.get('active_project') not in projects:
        d['active_project'] = 'General'
    d['history'] = [r for r in (d['history'] if isinstance(d.get('history'), list) else []) if isinstance(r, dict)]
    try:
        d['precision'] = min(max(int(d.get('precision', 3)), 1), 10)
    except (TypeError, ValueError):
        d['precision'] = 3
    d['auto_save'] = bool(d.get('auto_save'))
    d['sidebar_collapsed'] = bool(d.get('sidebar_collapsed'))
    d['favorites'] = [f for f in d['favorites'] if isinstance(f, str)]
    return d


def load(path):
    """Return (data, notice). A corrupt file is set aside - never silently overwritten."""
    path = Path(path)
    try:
        raw = path.read_text(encoding='utf-8')
    except OSError:
        return sanitize({}), None
    try:
        saved = json.loads(raw)
        if not isinstance(saved, dict):
            raise ValueError('workspace is not an object')
    except ValueError:
        aside = path.with_name('workspace.corrupt-%s.json' % datetime.now().strftime('%Y%m%d-%H%M%S'))
        try:
            path.replace(aside)
            return sanitize({}), 'Your workspace file could not be read. A copy was kept as %s.' % aside.name
        except OSError:
            return sanitize({}), 'Your workspace file could not be read and was ignored.'
    return sanitize(saved), None


def save(path, data):
    """Atomic write: temp file then rename, so a crash can never leave half a workspace on disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(path)


# --------------------------------------------------------------------------- .caldera project files + backups
PROJECT_FORMAT, BACKUP_FORMAT = 'caldera-project', 'caldera-backup'
PROJECT_EXT, BACKUP_EXT = '.caldera', '.caldera_backup'


def ensure_ext(path, ext):
    """Qt's save dialog does not append an extension for us."""
    path = str(path)
    return path if path.lower().endswith(ext) else path + ext


def _stamp():
    return datetime.now().isoformat(timespec='seconds')


def project_payload(data, name, app_version=''):
    """Everything that belongs to one project, ready to write as a .caldera file."""
    rows = [r for r in data.get('history', []) if isinstance(r, dict) and r.get('project') == name]
    return {'format': PROJECT_FORMAT, 'format_version': 1, 'app_version': app_version, 'exported': _stamp(),
            'project': {'name': name, 'notes': str(data.get('project_notes', {}).get(name, '')), 'history': rows}}


def parse_project(text):
    """Validate the text of a .caldera file. Returns {'name', 'notes', 'history'} or raises ValueError (user-readable)."""
    try:
        obj = json.loads(text)
    except ValueError:
        raise ValueError('That file is not a Caldera project (it could not be read).')
    if not isinstance(obj, dict):
        raise ValueError('That file is not a Caldera project.')
    if obj.get('format') == BACKUP_FORMAT or (obj.get('format') is None and 'projects' in obj and 'history' in obj):
        raise ValueError('That is a workspace backup, not a project. Use Settings → Restore backup instead.')
    if obj.get('format') != PROJECT_FORMAT:
        raise ValueError('That file is not a Caldera project.')
    proj = obj.get('project')
    if not isinstance(proj, dict) or not isinstance(proj.get('name'), str) or not proj['name'].strip():
        raise ValueError('The project file is missing its name.')
    rows = proj.get('history', [])
    if not isinstance(rows, list):
        raise ValueError('The project file has a damaged history.')
    clean = [r for r in rows if isinstance(r, dict) and isinstance(r.get('tool'), str)]
    return {'name': proj['name'].strip(), 'notes': str(proj.get('notes', '')), 'history': clean}


def unique_name(name, taken):
    if name not in taken:
        return name
    base, n = '%s (imported)' % name, 1
    cand = base
    while cand in taken:
        n += 1
        cand = '%s %d' % (base, n)
    return cand


def import_project(data, proj, mode='new'):
    """Add a parsed project to `data` in place. mode 'new' never touches existing projects (a clashing name gets
    '(imported)'); 'merge' adds into the project of the same name, skipping results it already has.
    Returns (final_name, added, skipped)."""
    taken = set(data['projects']) | set(data.get('archived_projects', []))
    name = proj['name']
    if mode == 'merge' and name in taken:
        target = name
    else:
        target = unique_name(name, taken)
    if target in data.get('archived_projects', []):
        data['archived_projects'].remove(target)
    if target not in data['projects']:
        data['projects'].append(target)
    notes = data.setdefault('project_notes', {})
    if proj['notes'].strip() and not str(notes.get(target, '')).strip():
        notes[target] = proj['notes']
    have = {(r.get('date'), r.get('tool'), r.get('result')) for r in data['history'] if r.get('project') == target}
    added = skipped = 0
    for r in proj['history']:
        key = (r.get('date'), r.get('tool'), r.get('result'))
        if key in have:
            skipped += 1
            continue
        rec = dict(r)
        rec['project'] = target
        data['history'].append(rec)
        have.add(key)
        added += 1
    return target, added, skipped


def backup_payload(data, app_version=''):
    return {'format': BACKUP_FORMAT, 'format_version': 1, 'app_version': app_version, 'exported': _stamp(),
            'workspace': data}


def parse_backup(text):
    """Accepts new .caldera_backup files and legacy raw-JSON backups. Returns the workspace dict."""
    try:
        obj = json.loads(text)
    except ValueError:
        raise ValueError('That file could not be read as a Caldera backup.')
    if not isinstance(obj, dict):
        raise ValueError('That file is not a Caldera backup.')
    if obj.get('format') == PROJECT_FORMAT:
        raise ValueError('That is a single project (.caldera), not a workspace backup. Use Projects → Import project.')
    if obj.get('format') == BACKUP_FORMAT:
        obj = obj.get('workspace')
    if not isinstance(obj, dict) or not isinstance(obj.get('projects'), list) or not isinstance(obj.get('history'), list):
        raise ValueError('This file is not a Caldera workspace backup.')
    return obj
