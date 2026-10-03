"""Static contract for the mobile kanban page. Reads dashboard/dashboard.html only."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / 'dashboard' / 'dashboard.html'

SINGLE_COLUMN = (
    '.edict-grid',
    '.duty-grid',
    '.model-grid',
    '.skills-grid',
    '.sess-grid',
    '.mn-cats',
    '.mb-cats',
    '.tpl-grid',
    '.m-rows',
    '.od-stats',
)

TOUCH = (
    '.nav-toggle', '.tab', '.btn', '.btn-refresh', '.btn-action',
    '.btn-morning-refresh', '.theme-toggle', '.ab-btn', '.ab-scan',
    '.ab-archive-all', '.ab-scan-detail', '.ab-scan-copy', '.sched-btn',
    '.tpl-cat', '.tpl-go', '.sess-filter', '.modal-close', '.as-wake-btn',
)

CLAMPED = (
    '.logo', '.modal-title', '.ec-title', '.od-name', '.mn-date', '.mb-title', '.crm-line1',
)


def _html():
    return PAGE.read_text(encoding='utf-8')


def _media_block(html, query):
    """Brace-match the @media rule that contains query. Return its body."""
    hits = list(re.finditer(re.escape(query), html))
    assert len(hits) == 1, query
    at = html.rfind('@media', 0, hits[0].start())
    assert at != -1
    open_brace = html.find('{', hits[0].end())
    assert open_brace != -1 and html.find('{', at) == open_brace
    depth = 0
    for i in range(open_brace, len(html)):
        if html[i] == '{':
            depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                return html[open_brace + 1:i]
    raise AssertionError('unclosed @media for ' + query)


def _rules(block):
    found = {}
    for sel_text, body in re.findall(r'([^{}]+)\{([^{}]*)\}', block):
        for sel in sel_text.split(','):
            sel = sel.strip()
            if sel:
                found.setdefault(sel, []).append(body)
    return found


def _prop(body, name):
    for chunk in body.split(';'):
        if ':' not in chunk:
            continue
        key, val = chunk.split(':', 1)
        if key.strip() == name:
            return re.sub(r'\s+', '', val)
    return None


def test_single_viewport_meta():
    html = _html()
    metas = re.findall(r'<meta\b[^>]*>', html, flags=re.I)
    viewports = [m for m in metas if re.search(r'name\s*=\s*["\']viewport["\']', m, flags=re.I)]
    assert len(viewports) == 1
    assert 'width=device-width' in viewports[0]


def test_mobile_block_contract():
    block = _media_block(_html(), 'max-width: 767px')
    rules = _rules(block)

    for sel in SINGLE_COLUMN:
        assert any(_prop(body, 'grid-template-columns') == '1fr' for body in rules[sel]), sel
    assert any(_prop(body, 'grid-template-columns') == '1fr' for body in rules['.off-layout'])
    for sel in ('.sched-grid', '.off-kpi'):
        assert any((_prop(body, 'grid-template-columns') or '').startswith('repeat(2,') for body in rules[sel]), sel

    assert any(_prop(body, 'overflow-x') == 'auto' for body in rules['.sk-md'])
    assert any(
        _prop(body, 'width') == 'max-content' and _prop(body, 'min-width') == '100%'
        for body in rules['.sk-md table']
    )
    for sel in ('.modal', '.sk-modal-body', '.sk-md'):
        assert any(
            _prop(body, 'max-width') == '100%' and _prop(body, 'min-width') == '0'
            for body in rules[sel]
        ), sel

    assert '44px' in block
    assert 'clamp(' in block
    for sel in TOUCH:
        assert any(
            _prop(body, 'min-height') == '44px'
            and _prop(body, 'min-width') == '44px'
            and _prop(body, 'touch-action') == 'manipulation'
            for body in rules[sel]
        ), sel
    for sel in CLAMPED:
        assert any((_prop(body, 'font-size') or '').startswith('clamp(') for body in rules[sel]), sel

    assert any(_prop(body, 'display') == 'none' and _prop(body, 'flex-direction') == 'column' for body in rules['.tabs'])
    assert any('var(--panel)' in body and 'var(--line)' in body for body in rules['.tabs'])
    assert any(_prop(body, 'width') == '100%' for body in rules['.tabs'])
    assert any(_prop(body, 'display') == 'flex' for body in rules['.tabs.open'])
    assert any(_prop(body, 'display') == 'flex' for body in rules['.nav-toggle'])


def test_nav_toggle_closes_with_tab_and_escape():
    html = _html()
    assert 'id="nav-toggle"' in html
    assert 'id="main-tabs"' in html
    assert 'aria-controls="main-tabs"' in html
    assert "classList.toggle('open')" in html

    tab_at = html.find("querySelectorAll('.tab')")
    assert tab_at != -1
    listener = html[tab_at:html.find('/* ══ COUNTDOWN', tab_at)]
    assert "classList.remove('open')" in listener
    assert "aria-expanded" in listener

    key = re.search(r"addEventListener\('keydown',e=>\{(.*?)\}\);", html, re.S)
    assert key, 'Escape listener missing'
    body = key.group(1)
    assert "getElementById('modal-bg').classList.remove('open')" in body
    assert "getElementById('main-tabs').classList.remove('open')" in body
    assert "aria-expanded" in body


def test_desktop_rules_stay_outside_mobile_block():
    html = _html()
    block = _media_block(html, 'max-width: 767px')
    outside = html.replace(block, '', 1)
    assert re.search(r'\.nav-toggle\s*\{[^}]*display\s*:\s*none', outside)
    assert re.search(r'\.tabs\s*\{[^}]*overflow-x\s*:\s*auto', outside)
    assert re.search(r'\.edict-grid\s*\{[^}]*minmax\(340px,\s*1fr\)', outside)
    assert re.search(r'\.off-layout\s*\{[^}]*260px\s+1fr', outside)
    assert 'prefers-reduced-motion' in outside
