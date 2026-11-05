"""RevisionWorx integration (optional). Pure Python, no Qt, so it is unit-testable.

Caldera talks to RevisionWorx only through `revisionworx link` (caldera/rwx_client.py, a copy of RevisionWorx's
contrib/rwx_client.py). Nothing here is needed for Caldera to work: without RevisionWorx the commands are hidden.

Two links are kept in the workspace:
- data['rwx_links'][project name] -> the RevisionWorx document that holds the project's calculation report
  ({'document', 'number', 'project', 'project_name'}). Publishing again adds a revision to that document; publishing
  an identical report records nothing.
- history record ['rwx'] -> a RevisionWorx document the calculation belongs to (a drawing, schematic, ...):
  {'id', 'number', 'title'}. Its live revision and state are shown beside the result.
"""
import re
import tempfile
from pathlib import Path

from .rwx_client import RevisionWorx, RwxError, describe  # noqa: F401  (re-exported for the UI)

KIND_FOR_STATE = {'released': 'Good', 'approved': 'Good', 'in_review': 'Warn', 'obsolete': 'Muted'}


def probe():
    """A ready RevisionWorx client, or None when it is not installed (slow: runs a process; call off the UI)."""
    try:
        rwx = RevisionWorx()
        return rwx if rwx.available() else None
    except Exception:
        return None


def links(data):
    got = data.get('rwx_links')
    if not isinstance(got, dict):
        got = data['rwx_links'] = {}
    return got


def project_link(data, name):
    link = links(data).get(name)
    return link if isinstance(link, dict) and link.get('document') else None


def default_number(name):
    slug = re.sub(r'[^A-Za-z0-9]+', '-', name).strip('-').upper()
    return 'CALC-' + (slug[:32] or 'PROJECT')


def rename_project(data, old, new):
    lk = links(data)
    if old in lk:
        lk[new] = lk.pop(old)


def unlink_project(data, name):
    return links(data).pop(name, None) is not None


def doc_line(doc):
    """('DWG-100 rev B · Released', pill kind) for a RevisionWorx document dict."""
    latest = doc.get('latest') or {}
    text = '%s rev %s · %s' % (doc.get('number') or doc.get('title') or 'Document', latest.get('label', '?'),
                               latest.get('state_name', ''))
    if doc.get('checkout'):
        text += ' · checked out'
    return text.rstrip(' ·'), KIND_FOR_STATE.get(latest.get('state'), '')


def publish_project(rwx, data, name, write_pdf, number='', title='', rwx_project='', app_version=''):
    """Publish the project's PDF summary to RevisionWorx. ``write_pdf(path)`` writes the report.

    First time: a new document ``number`` in RevisionWorx project ``rwx_project``. Afterwards: a new revision of the
    linked document (unchanged reports record nothing). Returns the RevisionWorx answer and updates the link."""
    link = project_link(data, name)
    rows = [r for r in data.get('history', []) if isinstance(r, dict) and r.get('project') == name]
    message = 'Caldera %s: %d calculation%s in project %s' % (app_version, len(rows), '' if len(rows) == 1 else 's',
                                                              name)
    with tempfile.TemporaryDirectory(prefix='caldera-rwx-') as tmp:
        stem = (link or {}).get('number') or number or default_number(name)
        path = Path(tmp) / ('%s.pdf' % re.sub(r'[^A-Za-z0-9._-]+', '_', stem))
        write_pdf(path)
        if link:
            got = rwx.publish(str(path), document=link['document'], message=message)
        else:
            if not rwx_project:
                raise ValueError('Choose the RevisionWorx project to publish to.')
            got = rwx.publish(str(path), project=rwx_project, number=number or default_number(name),
                              title=title or 'Calculations: %s' % name, message=message)
    doc = got['document']
    project = doc.get('project') or {}
    links(data)[name] = {'document': doc['id'], 'number': doc.get('number', ''),
                         'project': project.get('id', rwx_project) if isinstance(project, dict) else rwx_project,
                         'project_name': project.get('name', '') if isinstance(project, dict) else ''}
    return got


def link_record(rec, doc):
    rec['rwx'] = {'id': doc['id'], 'number': doc.get('number', ''), 'title': doc.get('title', '')}


def unlink_record(rec):
    return rec.pop('rwx', None) is not None


def record_link(rec):
    got = rec.get('rwx')
    return got if isinstance(got, dict) and got.get('id') else None
