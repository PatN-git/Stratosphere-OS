"""BT-221: `issues.py`, the local tracker backend: one file per issue on the `<repo>/issues` branch.

Each test runs in a fresh git repo (`repo` fixture) and drives `issues.main(argv, out)`; the store is read back
through git, never from the working tree, which the script must not touch.
"""
import json
import re
import subprocess
import sys
import threading

import pytest

from conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src" / "scripts"))
import issues


def git(cwd, *args):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "shop"
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 't@example.com')
    git(root, 'config', 'user.name', 'T')
    (root / 'app.txt').write_text('x\n')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'init')
    monkeypatch.chdir(root)
    monkeypatch.setattr(issues, 'today', lambda: '2026-10-27')
    return root


def run(*argv):
    lines = []
    code = issues.main(list(argv), out=lines.append)
    return code, '\n'.join(lines)


def ok(*argv):
    code, text = run(*argv)
    assert code == 0, text
    return text


def body(tmp, text, name='body.md'):
    p = tmp / name
    p.write_text(text, encoding='utf-8')
    return str(p)


SLICE = 'type:feature,mode:AFK,tier:slice,size:medium'
BODY = "### Overview\nLogin.\n\n### ICE Priorities\n- **Impact:** 2.0\n- **Confidence:** 80%\n\n### Acceptance Criteria (Verifiable)\n- [ ] Logs in\n"


# --- branch and init --------------------------------------------------------------------------------------------

def test_branch_is_the_repo_name_plus_issues_and_the_architecture_key_wins(repo):
    assert ok('branch') == 'shop/issues'
    git(repo, 'remote', 'add', 'origin', 'git@github.com:acme/web-app.git')
    assert ok('branch') == 'web-app/issues'
    for url in ('https://github.com/acme/api.git/', 'C:\\work\\bare\\api.git', '/srv/git/api'):
        git(repo, 'remote', 'set-url', 'origin', url)
        assert ok('branch') == 'api/issues', url
    git(repo, 'remote', 'set-url', 'origin', 'git@github.com:acme/web-app.git')
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'ARCHITECTURE.md').write_text('---\ntype: architecture\ntracker: local\ntracker_branch: tracker/issues\n---\n')
    assert ok('branch') == 'tracker/issues'


def test_every_command_refuses_under_tracker_github_and_runs_as_before_otherwise(repo):
    arch = repo / '.memory' / 'ARCHITECTURE.md'
    arch.parent.mkdir()
    arch.write_text('---\ntype: architecture\ntracker: github\n---\n')
    msg = '[TRACKER-GITHUB] issues.py is the local backend; use the gh forms (references/tracker-verbs-github.md)'
    for argv in (('list',), ('init',), ('branch',), ('create', '--title', 'A')):
        assert run(*argv) == (1, msg), argv
    assert git(repo, 'branch', '--list', 'shop/issues') == ''
    arch.write_text('---\ntype: architecture\ntracker: local\n---\n')
    assert ok('init') == '[INIT shop/issues]' and json.loads(ok('list')) == []
    arch.unlink()
    assert json.loads(ok('list')) == []


def test_init_creates_the_branch_once_and_never_touches_the_working_tree(repo):
    assert ok('init') == '[INIT shop/issues]'
    assert ok('init') == '[INIT-EXISTS shop/issues]'
    assert git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues') == 'docs/issues/README.md\n'
    assert git(repo, 'branch', '--show-current') == 'main\n'
    assert git(repo, 'status', '--porcelain') == ''
    assert not (repo / 'docs').exists()


def test_reads_halt_without_a_store_and_ask_for_migration_when_a_map_exists(repo):
    assert run('list') == (1, '[NO-STORE] branch shop/issues does not exist: run `python .agents/scripts/issues.py init`')
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'BACKLOG_MAP.md').write_text('# map\n')
    code, text = run('create', '--title', 'X')
    assert code == 1 and text.startswith('[MIGRATE-FIRST]')


# --- create, get, list ------------------------------------------------------------------------------------------

def test_create_persists_the_body_and_get_returns_it(repo, tmp_path):
    ok('init')
    bt = ok('create', '--title', 'Login form: email link', '--label', SLICE, '--milestone', 'v1.0.0',
            '--body-file', body(tmp_path, BODY))
    assert bt == 'BT-L-001-login-form-email-link'
    issue = json.loads(ok('get', bt))
    assert issue['status'] == 'planned' and issue['state'] == 'OPEN'
    assert issue['labels'] == SLICE.split(',') and issue['milestone'] == 'v1.0.0'
    assert '### Acceptance Criteria (Verifiable)\n- [ ] Logs in' in issue['body']
    text = git(repo, 'show', f'shop/issues:docs/issues/{bt}.md')
    assert text.startswith('---\ntype: issue\nid: BT-L-001-login-form-email-link\ntitle: "Login form: email link"\n')
    assert git(repo, 'status', '--porcelain') == ''


def test_create_takes_a_status_label_as_the_status_field_and_suffixes_a_clashing_slug(repo):
    ok('init')
    assert ok('create', '--title', 'Spike', '--label', 'type:research,status:needs_spec') == 'BT-L-001-spike'
    assert json.loads(ok('get', 'BT-L-001-spike'))['status'] == 'needs_spec'
    assert json.loads(ok('get', 'BT-L-001-spike'))['labels'] == ['type:research']
    assert ok('create', '--title', 'Spike!') == 'BT-L-002-spike'


def test_create_refuses_an_unknown_parent_or_blocker(repo):
    ok('init')
    assert run('create', '--title', 'A', '--parent', 'BT-LOCAL-nope') == (1, '[ERROR] parent or blocker BT-LOCAL-nope not found')


def test_list_filters_and_wip_children_blockers(repo):
    ok('init')
    epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--parent', epic)
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--parent', epic, '--blocked-by', db)
    ok('set', db, '--status', 'in progress')
    assert [i['id'] for i in json.loads(ok('wip'))] == [db]
    assert [i['id'] for i in json.loads(ok('children', epic))] == [db, ui]
    assert json.loads(ok('blockers', ui)) == [{'id': db, 'title': 'DB', 'status': 'in progress'}]
    assert [i['id'] for i in json.loads(ok('list', '--label', 'tier:epic'))] == [epic]
    assert 'body' not in json.loads(ok('list'))[0]


# --- set, comment, claim, close, reopen -------------------------------------------------------------------------

def test_set_rejects_status_labels_cycles_and_self_blocks(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    b = ok('create', '--title', 'B', '--blocked-by', a)
    assert run('set', a, '--add-blocker', b) == (1, f'[ERROR] blocked-by cycle: {a} <- {b} <- {a}')
    assert run('set', a, '--add-blocker', a) == (1, f'[ERROR] {a} cannot block itself')
    assert run('set', a, '--add-label', 'status:done') == (1, '[ERROR] status is a field: use --status')
    assert run('set', a, '--status', 'shipped')[0] == 1
    ok('set', b, '--remove-blocker', a, '--milestone', 'v1.0.1')
    got = json.loads(ok('get', b))
    assert got['blocked_by'] == [] and got['milestone'] == 'v1.0.1'


def test_comment_appends_dated_entries_under_comments(repo):
    ok('init')
    a = ok('create', '--title', 'A', '--body-file', body(repo.parent, 'Body'))
    ok('comment', a, '--body', 'Shipped in commit abc')
    ok('comment', a, '--body', 'line one\nline two')
    assert json.loads(ok('get', a))['comments'] == ['- 2026-10-27: Shipped in commit abc',
                                                    '- 2026-10-27: line one\n  line two']
    assert git(repo, 'show', f'shop/issues:docs/issues/{a}.md').endswith(
        '---\nBody\n\n<!-- issues.py: comments -->\n## Comments\n- 2026-10-27: Shipped in commit abc\n- 2026-10-27: line one\n  line two\n')


RESUME = '<!-- stratos:resume -->'


def test_a_resume_note_comment_is_the_resume_file_replaced_whole_and_makes_no_commit(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    before = git(repo, 'rev-parse', 'shop/issues')
    assert ok('comment', a, '--body', f'{RESUME}\nfirst') == a
    note = repo / '.memory' / 'resume' / f'{a}.md'
    assert note.read_text(encoding='utf-8') == f'{RESUME}\nfirst'
    ok('comment', a, '--body', f'{RESUME}\nsecond')
    assert note.read_text(encoding='utf-8') == f'{RESUME}\nsecond'
    assert git(repo, 'rev-parse', 'shop/issues') == before and json.loads(ok('get', a))['comments'] == []
    ok('comment', a, '--body', 'plain')
    assert json.loads(ok('get', a))['comments'] == ['- 2026-10-27: plain'] and note.read_text(encoding='utf-8').endswith('second')
    assert run('comment', 'BT-LOCAL-nope', '--body', f'{RESUME}\nx')[0] == 1


def test_claim_is_compare_and_set(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    ok('claim', a, '--by', 'feat/x')
    assert ok('claim', a, '--by', 'feat/x') == a
    assert run('claim', a, '--by', 'feat/y') == (1, f'[CLAIMED {a} by feat/x]')
    got = json.loads(ok('get', a))
    assert (got['status'], got['claimed_by']) == ('in progress', 'feat/x')


def test_two_concurrent_claims_exactly_one_wins(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    results = []
    threads = [threading.Thread(target=lambda who=who: results.append(run('claim', a, '--by', who)))
               for who in ('one', 'two')]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(code for code, _ in results) == [0, 1]
    assert json.loads(ok('get', a))['claimed_by'] in ('one', 'two')


def test_close_archives_with_a_reason_and_reopen_brings_it_back(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    ok('close', a, '--reason', 'not planned')
    assert git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues', 'docs/issues/') == \
        f'docs/issues/README.md\ndocs/issues/archive/{a}.md\n'
    got = json.loads(ok('get', a))
    assert (got['status'], got['state'], got['close_reason'], got['closed']) == ('done', 'CLOSED', 'not planned', '2026-10-27')
    assert json.loads(ok('list')) == []
    assert [i['id'] for i in json.loads(ok('list', '--all'))] == [a]
    assert run('set', a, '--status', 'planned') == (1, f'[ERROR] {a} is closed: `reopen` it first')
    ok('reopen', a)
    assert json.loads(ok('get', a))['state'] == 'OPEN'
    assert f'docs/issues/{a}.md' in git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues')


def test_label_adds_area_slugs_only(repo):
    ok('init')
    assert ok('label', 'area:BE-api') == 'area:BE-api'
    assert ok('label', 'area:BE-api') == 'area:BE-api'
    assert git(repo, 'show', 'shop/issues:docs/issues/README.md').endswith('## Area labels\n- area:BE-api\n')
    assert run('label', 'type:chore')[0] == 1


# --- ready and check --------------------------------------------------------------------------------------------

def test_ready_lists_unblocked_candidates_with_ice_on_read(repo, tmp_path):
    ok('init')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--body-file', body(tmp_path, BODY))
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--blocked-by', db)
    bare = ok('create', '--title', 'Bare', '--label', 'type:feature,tier:slice')
    out = ok('ready')
    assert f'{db} | planned | DB | mode:AFK size:medium type:feature | — | ICE 0.8' in out
    assert f'[BLOCKED {ui} <- {db}]' in out
    assert f'[MISSING-LABELS] {bare} - Bare (mode:, size:)' in out
    assert f'{ui} |' not in out
    ok('close', db)
    assert f'{ui} | planned | UI' in ok('ready')


def test_check_reports_label_composition_unknown_labels_and_dangling_ids(repo):
    ok('init')
    ok('label', 'area:BE-api')
    good = ok('create', '--title', 'Good', '--label', SLICE + ',area:BE-api')
    assert ok('check') == '[CHECK-OK 1 issue(s)]'
    bad = ok('create', '--title', 'Bad', '--label', 'type:feature,tier:slice,area:nope')
    epic = ok('create', '--title', 'Epic', '--label', 'type:feature,tier:epic,mode:AFK')
    code, text = run('check')
    assert code == 1
    assert f'[CHECK-FAIL {bad}] unknown label area:nope' in text
    assert f'[CHECK-FAIL {bad}] a slice needs exactly one type:, mode: and size:' in text
    assert f'[CHECK-FAIL {epic}] an epic needs one type: and no mode: or size:' in text
    assert good not in text


def test_canonical_labels_match_the_taxonomy():
    text = (REPO_ROOT / 'src' / 'references' / 'label-taxonomy.md').read_text(encoding='utf-8')
    for prefix, values in issues.CANONICAL.items():
        for v in values:
            assert f'`{prefix}:{v}`' in text, f'{prefix}:{v}'


# --- sync -------------------------------------------------------------------------------------------------------

@pytest.fixture
def clones(repo, tmp_path):
    """`repo` with a bare `origin` holding its tracker branch, plus a second clone `other`."""
    origin = tmp_path / 'origin.git'
    git(tmp_path, 'init', '-q', '--bare', str(origin))
    git(repo, 'remote', 'add', 'origin', str(origin))
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'ARCHITECTURE.md').write_text('---\ntracker: local\ntracker_branch: shop/issues\n---\n')
    ok('init')
    git(repo, 'push', '-q', 'origin', 'main', 'shop/issues')
    other = tmp_path / 'other'
    git(tmp_path, 'clone', '-q', str(origin), str(other))
    git(other, 'config', 'user.email', 'o@example.com')
    git(other, 'config', 'user.name', 'O')
    (other / '.memory').mkdir()
    (other / '.memory' / 'ARCHITECTURE.md').write_text('---\ntracker: local\ntracker_branch: shop/issues\n---\n')
    return repo, other


def test_sync_fast_forwards_a_new_clone_and_reports_local_only(clones, monkeypatch):
    repo, other = clones
    a = ok('create', '--title', 'A')
    git(repo, 'push', '-q', 'origin', 'shop/issues')
    monkeypatch.chdir(other)
    assert ok('sync') == '[SYNC-FF]'
    assert json.loads(ok('get', a))['title'] == 'A'
    assert ok('sync') == '[SYNC-UP-TO-DATE]'


def test_sync_field_merges_divergent_edits(clones, monkeypatch):
    repo, other = clones
    a = ok('create', '--title', 'A')
    git(repo, 'push', '-q', 'origin', 'shop/issues')
    monkeypatch.chdir(other)
    ok('sync')
    ok('set', a, '--milestone', 'v1.0.1')
    ok('comment', a, '--body', 'from other')
    ok('create', '--title', 'B')
    git(other, 'push', '-q', 'origin', 'shop/issues')
    monkeypatch.chdir(repo)
    monkeypatch.setattr(issues, 'today', lambda: '2026-10-28')
    ok('set', a, '--status', 'in progress')
    ok('comment', a, '--body', 'from repo')
    assert ok('sync').startswith('[SYNC-MERGED]')
    got = json.loads(ok('get', a))
    assert (got['status'], got['milestone']) == ('in progress', 'v1.0.1')
    assert got['comments'] == ['- 2026-10-28: from repo', '- 2026-10-27: from other']
    assert json.loads(ok('get', 'BT-L-002-b'))['title'] == 'B'
    parents = git(repo, 'log', '-1', '--format=%P', 'shop/issues').split()
    assert len(parents) == 2
    assert ok('sync') == '[SYNC-AHEAD] local shop/issues has commits origin lacks; push it with the next ship push'


# --- migrate ----------------------------------------------------------------------------------------------------

MAP = """---
type: backlog
---
# BACKLOG MAP
## Label Registry
- **Area (`area:xxx`)**: `area:BE-api`, `area:FE-<page_name>` (placeholder)
## Backlog
| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| BT-LOCAL-auth | Auth epic | in progress | type:feature, tier:epic | — | — | — | ICE: - | — |
| BT-LOCAL-db | DB setup | done | type:feature, mode:AFK, tier:slice, size:small | — | BT-LOCAL-auth | — | ICE: - | — |
| BT-LOCAL-login | Login page | planned | type:feature, mode:HITL, tier:slice, size:small, area:BE-api | v1.0.1 | BT-LOCAL-auth | BT-LOCAL-db | ICE: 0.27 (I: 2.0, C: 80%) | [[L-001]], [[A-002]] |
"""


def test_migrate_moves_every_row_to_the_branch_and_archives_the_map(repo):
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'BACKLOG_MAP.md').write_text(MAP, encoding='utf-8')
    assert ok('migrate') == '[MIGRATED] 3 issue(s) to shop/issues; map moved to .memory/archive/BACKLOG_MAP.2026-10-27.md'
    assert not (repo / '.memory' / 'BACKLOG_MAP.md').exists()
    login = json.loads(ok('get', 'BT-LOCAL-login'))
    assert (login['parent'], login['blocked_by'], login['milestone']) == ('BT-LOCAL-auth', ['BT-LOCAL-db'], 'v1.0.1')
    assert '- **Impact:** 2.0\n- **Confidence:** 80%' in login['body'] and 'Refs: [[L-001]], [[A-002]]' in login['body']
    assert json.loads(ok('get', 'BT-LOCAL-db'))['state'] == 'CLOSED'
    assert ok('check') == '[CHECK-OK 3 issue(s)]'
    assert 'BT-LOCAL-login | planned | Login page' in ok('ready')
    assert run('migrate')[0] == 1


# --- round trip of the file format ------------------------------------------------------------------------------

@pytest.mark.parametrize('title', ['Plain title', 'Colon: inside', 'Quote "x"', 'Ünïcode — dash', '[bracket] start'])
def test_issue_file_round_trips(title):
    issue = {k: None for k in issues.FIELDS} | {'type': 'issue', 'id': 'BT-LOCAL-x', 'title': title,
                                                 'status': 'in progress', 'labels': ['type:feature', 'area:FE-a'],
                                                 'blocked_by': [], 'body': 'B\n\n## Not comments', 'comments': ['- d: c']}
    assert issues.parse_issue(issues.render_issue(issue)) == issue


# --- the other scripts read the store on the local backend ------------------------------------------------------

def test_reconcile_edges_and_ice_read_candidates_read_the_store(repo, tmp_path, capsys):
    import ice_read
    import reconcile
    (repo / '.memory').mkdir()
    arch = repo / '.memory' / 'ARCHITECTURE.md'
    arch.write_text('---\ntracker: local\n---\n')
    ok('init')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--body-file', body(tmp_path, BODY))
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--blocked-by', db)
    assert reconcile.main(['--edges', 'blockers', '--ids', ui, '--arch', str(arch)]) == 1
    assert f'[BLOCKER-UNMET {ui} <- {db}]' in capsys.readouterr().out
    assert ice_read.main(['candidates', '--arch', str(arch)]) == 0
    out = capsys.readouterr().out
    assert f'{db} | planned | DB' in out and f'{ui} | planned | UI' in out
    ok('close', db)
    assert reconcile.main(['--edges', 'dependents', '--all-open', '--arch', str(arch)]) == 0
    assert f'[CLEAR {ui} <- {db}]' in capsys.readouterr().out


def test_merged_of_reads_the_blockers_unit_branch(repo):
    ok('init')
    epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--parent', epic)
    merged_of = lambda: issues.make_merged_of(issues.Tracker().store())
    assert merged_of()(db) == 'none'
    git(repo, 'checkout', '-qb', f'feature/{epic}-auth')
    (repo / 'db.txt').write_text('db\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'db')
    assert merged_of()(db) == 'open'
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '-q', '--ff-only', f'feature/{epic}-auth')
    assert merged_of()(db) == 'merged'


def test_a_run_from_a_subdirectory_reads_the_same_store(repo, monkeypatch):
    ok('init')
    a = ok('create', '--title', 'A')
    (repo / 'sub' / 'dir').mkdir(parents=True)
    monkeypatch.chdir(repo / 'sub' / 'dir')
    assert ok('init') == '[INIT-EXISTS shop/issues]'
    assert [i['id'] for i in json.loads(ok('list'))] == [a]
    assert git(repo, 'rev-list', '--count', 'shop/issues') == '2\n'


# --- grader findings (BT-221 review) ------------------------------------------------------------------------------

def test_writes_and_the_tracker_branch_key_work_from_a_subdirectory(repo, monkeypatch):
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'ARCHITECTURE.md').write_text('---\ntracker: local\ntracker_branch: custom/issues\n---\n')
    (repo / 'sub').mkdir()
    monkeypatch.chdir(repo / 'sub')
    assert ok('branch') == 'custom/issues'
    ok('init')
    a = ok('create', '--title', 'A')
    assert json.loads(ok('get', a))['title'] == 'A'
    assert 'custom/issues' in git(repo, 'branch', '--list', 'custom/issues')


def test_a_body_with_its_own_comments_heading_round_trips(repo, tmp_path):
    ok('init')
    text = 'Intro\n\n## Comments\nOur API comments policy.'
    a = ok('create', '--title', 'A', '--body-file', body(tmp_path, text))
    assert json.loads(ok('get', a))['body'] == text
    ok('comment', a, '--body', 'later')
    got = json.loads(ok('get', a))
    assert (got['body'], got['comments']) == (text, ['- 2026-10-27: later'])


def test_set_status_done_closes_and_archives_like_close(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    ok('set', a, '--status', 'done')
    got = json.loads(ok('get', a))
    assert (got['state'], got['close_reason']) == ('CLOSED', 'completed')
    assert ok('close', a) == a
    assert json.loads(ok('get', a))['state'] == 'CLOSED'


def test_claim_refuses_a_holder_on_any_open_status(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    ok('claim', a, '--by', 'x')
    ok('set', a, '--status', 'in review')
    assert run('claim', a, '--by', 'y') == (1, f'[CLAIMED {a} by x]')


def test_updated_is_a_timestamp_so_same_day_edits_order(repo):
    ok('init')
    a = ok('create', '--title', 'A')
    assert re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\S*', json.loads(ok('get', a))['updated'])


def test_self_parent_and_yaml_keyword_titles(repo):
    ok('init')
    a = ok('create', '--title', 'null')
    assert json.loads(ok('get', a))['title'] == 'null'
    assert run('set', a, '--parent', a) == (1, f'[ERROR] {a} cannot be its own parent')


def test_merged_of_ignores_a_longer_id_sharing_the_prefix(repo):
    ok('init')
    login = ok('create', '--title', 'Login', '--label', SLICE)
    form = ok('create', '--title', 'Login form', '--label', SLICE)
    git(repo, 'checkout', '-qb', f'feature/{form}-x')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    assert issues.make_merged_of(issues.Tracker().store())(login) == 'none'


def test_a_write_that_loses_the_compare_and_set_rereads_and_retries(repo, monkeypatch):
    ok('init')
    a = ok('create', '--title', 'A')
    real, olds = issues.update_ref, []

    def racing(ref, new, old):
        olds.append(old)
        if len(olds) == 1:  # another writer lands between this write's read and its update-ref
            monkeypatch.setattr(issues, 'update_ref', real)
            ok('comment', a, '--body', 'from the other writer')
            monkeypatch.setattr(issues, 'update_ref', racing)
        return real(ref, new, old)

    monkeypatch.setattr(issues, 'update_ref', racing)
    ok('set', a, '--add-label', 'type:bug')
    monkeypatch.setattr(issues, 'update_ref', real)
    assert len(olds) == 2 and olds[0] != olds[1], "the retry re-read the moved ref"
    got = json.loads(ok('get', a))
    assert got['labels'] == ['type:bug'] and len(got['comments']) == 1, "neither write was lost"
    assert git(repo, 'rev-list', '--count', 'shop/issues') == '4\n'  # init, create, the other comment, the retried set


def test_a_write_that_loses_every_attempt_raises_conflict_and_writes_nothing(repo, monkeypatch):
    ok('init')
    a = ok('create', '--title', 'A')
    before = git(repo, 'rev-parse', 'shop/issues')
    calls, real = [], issues.update_ref
    monkeypatch.setattr(issues, 'update_ref', lambda ref, new, old: calls.append(old) and False)
    code, text = run('set', a, '--add-label', 'type:bug')
    assert code == 1 and text.startswith('[CONFLICT] shop/issues moved 4 times'), text
    assert len(calls) == issues.MAX_RETRIES + 1
    monkeypatch.setattr(issues, 'update_ref', real)
    assert git(repo, 'rev-parse', 'shop/issues') == before
    assert json.loads(ok('get', a))['labels'] == []


def test_merged_of_ignores_a_longer_parent_id_sharing_the_prefix(repo):
    ok('init')
    epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    epic2 = ok('create', '--title', 'Auth v2', '--label', 'type:feature,tier:epic')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--parent', epic)
    git(repo, 'checkout', '-qb', f'feature/{epic2}-x')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    assert issues.make_merged_of(issues.Tracker().store())(db) == 'none'


def test_merged_reports_no_merges_when_branches_unmerged(repo):
    ok('init')
    epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    ok('set', epic, '--status', 'in review')
    git(repo, 'checkout', '-qb', f'feature/{epic}-work')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    code, text = run('merged')
    assert code == 0 and text == '[NO-MERGES]'


def test_merged_detects_ancestor_branch_and_closes_with_flag(repo):
    ok('init')
    epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    ok('set', epic, '--status', 'in review')
    git(repo, 'checkout', '-qb', f'feature/{epic}-work')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge auth', f'feature/{epic}-work')

    code, text = run('merged')
    assert code == 0 and f'[MERGED {epic}]' in text
    issue = json.loads(ok('get', epic))
    assert issue['status'] == 'in review' and not issue['closed']

    code, text = run('merged', '--close')
    assert code == 0 and f'[MERGED {epic}]' in text
    issue = json.loads(ok('get', epic))
    assert issue['status'] == 'done' and issue['closed'] == '2026-10-27'


def test_merged_close_sets_the_full_closed_state_on_a_claimed_epic_and_a_merged_slice(repo, monkeypatch):
    monkeypatch.setattr(issues, 'now', lambda: '2026-10-27T10:00:00+00:00')
    ok('init')
    epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    ok('claim', epic, '--by', 'feat/auth')
    ok('set', epic, '--status', 'in review')
    assert json.loads(ok('get', epic))['claimed_by'] == 'feat/auth'
    git(repo, 'checkout', '-qb', f'feature/{epic}-work')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge auth', f'feature/{epic}-work')
    slice_id = ok('create', '--title', 'Billing', '--label', SLICE)
    ok('set', slice_id, '--status', 'in review')
    tip = _ship(repo, f'feature/{slice_id}-work', 'b.txt')
    git(repo, 'merge', '--no-ff', '-qm', 'merge billing', f'feature/{slice_id}-work')
    git(repo, 'branch', '-D', f'feature/{slice_id}-work')
    ok('comment', slice_id, '--body', f"Shipped on feature/{slice_id}-work @ {tip}")

    code, text = run('merged', '--close')
    assert code == 0 and text.splitlines() == [f'[MERGED {epic}]', f'[MERGED {slice_id}]']
    for bt in (epic, slice_id):
        issue = json.loads(ok('get', bt))
        assert issue['status'] == 'done' and issue['closed'] == '2026-10-27'
        assert issue['close_reason'] == 'completed' and issue['claimed_by'] is None
        assert issue['updated'] == '2026-10-27T10:00:00+00:00'
    files = git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues').split()
    for bt in (epic, slice_id):
        assert f'docs/issues/archive/{bt}.md' in files and f'docs/issues/{bt}.md' not in files
    assert git(repo, 'show', f'shop/issues:docs/issues/archive/{epic}.md') == (
        f'---\ntype: issue\nid: {epic}\ntitle: Auth\nstatus: done\nlabels: [type:feature, tier:epic]\nmilestone: null\n'
        'parent: null\nblocked_by: []\nclaimed_by: null\ncreated: 2026-10-27\nupdated: 2026-10-27T10:00:00+00:00\n'
        'closed: 2026-10-27\nclose_reason: completed\n---\n\n')
    assert git(repo, 'show', f'shop/issues:docs/issues/archive/{slice_id}.md').endswith(
        f'close_reason: completed\n---\n\n\n<!-- issues.py: comments -->\n## Comments\n- 2026-10-27: Shipped on feature/{slice_id}-work @ {tip}\n')


def test_merged_detects_recorded_sha_after_branch_deletion(repo):
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    ok('set', epic, '--status', 'in review')
    git(repo, 'checkout', '-qb', f'feature/{epic}-work')
    (repo / 'b.txt').write_text('b\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'b')
    tip = git(repo, 'rev-parse', 'HEAD').strip()
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge billing', f'feature/{epic}-work')
    git(repo, 'branch', '-D', f'feature/{epic}-work')

    ok('comment', epic, '--body', f"Shipped on feature/{epic}-work @ {tip}")

    code, text = run('merged')
    assert code == 0 and f'[MERGED {epic}]' in text


def _ship(repo, branch, name):
    """Commit `name` on `branch` (created or reused), return the tip SHA, end on main."""
    rc = subprocess.run(['git', 'rev-parse', '--verify', '-q', branch], cwd=repo, capture_output=True).returncode
    git(repo, 'checkout', '-q' if rc == 0 else '-qb', branch)
    (repo / name).write_text(name + '\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', name)
    tip = git(repo, 'rev-parse', 'HEAD').strip()
    git(repo, 'checkout', '-q', 'main')
    return tip


def test_merged_detects_epic_via_the_closed_child_slices_tip_after_branch_deletion(repo):
    """4a posts `Shipped on <branch> @ <sha>` on the shipped SLICE (then closes it), never on the epic."""
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    ok('set', epic, '--status', 'in review')
    child = ok('create', '--title', 'Invoices', '--label', SLICE, '--parent', epic)
    tip = _ship(repo, f'feature/{epic}-work', 'b.txt')
    git(repo, 'merge', '--no-ff', '-qm', 'merge billing', f'feature/{epic}-work')
    git(repo, 'branch', '-D', f'feature/{epic}-work')
    ok('comment', child, '--body', f"Shipped on feature/{epic}-work @ {tip}")
    ok('set', child, '--status', 'done')
    ok('close', child)

    code, text = run('merged')
    assert code == 0 and f'[MERGED {epic}]' in text
    run('merged', '--close')
    assert json.loads(ok('get', epic))['status'] == 'done'


def test_merged_epic_with_one_unmerged_child_tip_is_not_merged(repo):
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    ok('set', epic, '--status', 'in review')
    c1 = ok('create', '--title', 'Invoices', '--label', SLICE, '--parent', epic)
    c2 = ok('create', '--title', 'Refunds', '--label', SLICE, '--parent', epic)
    t1 = _ship(repo, f'feature/{epic}-work', 'b1.txt')
    git(repo, 'merge', '--no-ff', '-qm', 'merge billing', f'feature/{epic}-work')
    t2 = _ship(repo, f'feature/{epic}-work', 'b2.txt')  # second slice, not merged
    git(repo, 'branch', '-D', f'feature/{epic}-work')
    ok('comment', c1, '--body', f"Shipped on feature/{epic}-work @ {t1}")
    ok('comment', c2, '--body', f"Shipped on feature/{epic}-work @ {t2}")

    code, text = run('merged', '--close')
    assert code == 0 and '[MERGED' not in text
    assert json.loads(ok('get', epic))['status'] == 'in review'


def test_merged_uses_only_the_newest_tip_a_reshipped_issue_is_not_merged(repo):
    """An older tip that merged must not hide a newer, unmerged re-ship (the branch is still open)."""
    ok('init')
    item = ok('create', '--title', 'Search', '--label', SLICE)
    ok('set', item, '--status', 'in review')
    t1 = _ship(repo, f'feature/{item}-x', 's1.txt')
    git(repo, 'merge', '--no-ff', '-qm', 'merge search', f'feature/{item}-x')
    ok('comment', item, '--body', f"Shipped on feature/{item}-x @ {t1}")
    t2 = _ship(repo, f'feature/{item}-x', 's2.txt')  # re-shipped, not merged, branch alive
    ok('comment', item, '--body', f"Shipped on feature/{item}-x @ {t2}")

    code, text = run('merged')
    assert code == 0 and '[MERGED' not in text and f'[STALE-TIP {item}]' in text
    code, text = run('merged', '--close')
    assert code == 0 and '[MERGED' not in text
    issue = json.loads(ok('get', item))
    assert issue['status'] == 'in review' and not issue['closed']

    git(repo, 'merge', '--no-ff', '-qm', 'merge search again', f'feature/{item}-x')
    code, text = run('merged')
    assert f'[MERGED {item}]' in text and 'STALE-TIP' not in text


def test_merged_squash_commit_is_advisory_and_not_auto_closed(repo):
    ok('init')
    item = ok('create', '--title', 'Search', '--label', 'type:feature,tier:slice,size:small,mode:AFK')
    ok('set', item, '--status', 'in review')
    (repo / 's.txt').write_text('s\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', f"feat({item}): squash commit directly on main")

    code, text = run('merged')
    assert code == 0 and f'[PROBABLY-MERGED {item}]' in text

    code, text = run('merged', '--close')
    assert code == 0 and f'[PROBABLY-MERGED {item}]' in text
    issue = json.loads(ok('get', item))
    assert issue['status'] == 'in review' and not issue['closed']


def test_merged_squash_advisory_ignores_the_docs_commit_that_names_an_open_epic(repo):
    """2a/2b commit `docs(<epic>): PRD` to the default branch; an `in review` epic with an open PR is not squash-merged."""
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    ok('set', epic, '--status', 'in review')
    child = ok('create', '--title', 'Invoices', '--label', SLICE, '--parent', epic)
    git(repo, 'commit', '--allow-empty', '-qm', f"docs({epic}): PRD")
    tip = _ship(repo, f'feature/{epic}-work', 'b.txt')  # shipped, branch alive, PR open
    ok('comment', child, '--body', f"Shipped on feature/{epic}-work @ {tip}")
    ok('set', child, '--status', 'done')
    ok('close', child)
    assert run('merged') == (0, '[NO-MERGES]')


def test_merged_squash_advisory_never_matches_a_docs_commit_even_without_a_recorded_tip(repo):
    ok('init')
    item = ok('create', '--title', 'Search', '--label', SLICE)
    ok('set', item, '--status', 'in review')
    git(repo, 'commit', '--allow-empty', '-qm', f"docs({item}): interface design")
    assert run('merged') == (0, '[NO-MERGES]')


def test_merged_squash_advisory_counts_only_commits_after_the_recorded_ship(repo, monkeypatch):
    ok('init')
    item = ok('create', '--title', 'Search', '--label', SLICE)
    ok('set', item, '--status', 'in review')
    monkeypatch.setenv('GIT_COMMITTER_DATE', '2020-01-01T00:00:00')
    git(repo, 'commit', '--allow-empty', '-qm', f"chore({item}): groundwork, long before the ship")
    monkeypatch.delenv('GIT_COMMITTER_DATE')
    tip = _ship(repo, f'feature/{item}-x', 's.txt')
    ok('comment', item, '--body', f"Shipped on feature/{item}-x @ {tip}")
    assert run('merged') == (0, '[NO-MERGES]')

    git(repo, 'merge', '--squash', f'feature/{item}-x')
    git(repo, 'commit', '-qm', f"feat({item}): search")
    git(repo, 'branch', '-D', f'feature/{item}-x')
    code, text = run('merged', '--close')
    assert code == 0 and f'[PROBABLY-MERGED {item}]' in text and '[MERGED' not in text
    assert json.loads(ok('get', item))['status'] == 'in review'


def _blocker_with_tip_and_deleted_branch(repo, merge):
    """An epic `Billing` whose slice `db` shipped one tip on a unit branch that is then deleted (merged or not)."""
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--parent', epic)
    tip = _ship(repo, f'feature/{epic}-work', 'b.txt')
    ok('comment', db, '--body', f"Shipped on feature/{epic}-work @ {tip}")
    ok('set', db, '--status', 'done')
    ok('close', db)
    if merge:
        git(repo, 'merge', '--no-ff', '-qm', 'merge billing', f'feature/{epic}-work')
    git(repo, 'branch', '-D', f'feature/{epic}-work')
    return epic, db


def test_merged_of_a_deleted_unmerged_branch_with_a_recorded_tip_is_open(repo, tmp_path, capsys):
    import reconcile
    (repo / '.memory').mkdir()
    arch = repo / '.memory' / 'ARCHITECTURE.md'
    arch.write_text('---\ntracker: local\n---\n')
    epic, db = _blocker_with_tip_and_deleted_branch(repo, merge=False)
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--blocked-by', db)
    assert issues.make_merged_of(issues.Tracker().store())(db) == 'open'
    reconcile.main(['--edges', 'dependents', '--all-open', '--arch', str(arch)])
    assert f'[KEEP {ui} <- {db}]' in capsys.readouterr().out


def test_merged_of_a_deleted_merged_branch_with_a_recorded_tip_is_merged(repo, capsys):
    import reconcile
    (repo / '.memory').mkdir()
    arch = repo / '.memory' / 'ARCHITECTURE.md'
    arch.write_text('---\ntracker: local\n---\n')
    epic, db = _blocker_with_tip_and_deleted_branch(repo, merge=True)
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--blocked-by', db)
    assert issues.make_merged_of(issues.Tracker().store())(db) == 'merged'
    reconcile.main(['--edges', 'dependents', '--all-open', '--arch', str(arch)])
    assert f'[CLEAR {ui} <- {db}]' in capsys.readouterr().out


def test_merged_of_an_epic_blocker_reads_its_child_slices_tip(repo):
    epic, db = _blocker_with_tip_and_deleted_branch(repo, merge=False)
    assert issues.make_merged_of(issues.Tracker().store())(epic) == 'open'


def test_merged_of_with_no_recorded_tip_and_no_branch_stays_none(repo):
    ok('init')
    spike = ok('create', '--title', 'Spike', '--label', 'type:research,tier:slice,mode:HITL,size:medium')
    ok('close', spike)
    assert issues.make_merged_of(issues.Tracker().store())(spike) == 'none'


def test_board_text_kanban(repo):
    ok('init')
    p = ok('create', '--title', 'Setup DB', '--label', 'type:feature,tier:slice,size:small,mode:AFK')
    w = ok('create', '--title', 'API routes', '--label', 'type:feature,tier:slice,size:medium,mode:AFK')
    ok('set', w, '--status', 'in progress')
    d = ok('create', '--title', 'Docs', '--label', 'type:documentation,tier:slice,size:small,mode:AFK')
    ok('set', d, '--status', 'done')
    ok('close', d)

    code, text = run('board')
    assert code == 0
    assert '=== Planned (1) ===' in text
    assert f'{p}  Setup DB  [size:small]' in text
    assert '=== In Progress (1) ===' in text
    assert f'{w}  API routes  [size:medium]' in text
    assert '=== Done (1) ===' in text
    assert f'{d}  Docs  [size:small]' in text


def test_board_markdown_export(repo, tmp_path):
    ok('init')
    p = ok('create', '--title', 'Setup DB', '--label', 'type:feature,tier:slice,size:small,mode:AFK')
    md_file = tmp_path / "board.md"

    code, text = run('board', '--md', str(md_file))
    assert code == 0
    assert f"[BOARD] wrote {md_file}" in text
    assert md_file.exists()
    content = md_file.read_text(encoding='utf-8')
    assert '## Planned (1)' in content
    assert f'- **{p}** Setup DB `size:small`' in content


def test_board_text_and_markdown_keep_their_blocked_by_wording(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'DB', '--label', SLICE)
    b = ok('create', '--title', 'API', '--label', SLICE, '--blocked-by', a)
    assert f'{b}  API  [size:medium] [BLOCKED by {a}]' in run('board')[1].splitlines()
    md_file = tmp_path / 'board.md'
    ok('board', '--md', str(md_file))
    assert f'- **{b}** API `size:medium` *(blocked by {a})*' in md_file.read_text(encoding='utf-8').splitlines()


def test_board_web_card_meta_carries_blocked_by_and_the_page_renders_a_badge(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'DB', '--label', SLICE)
    b = ok('create', '--title', 'API', '--label', SLICE, '--blocked-by', a)
    out_html = tmp_path / 'blocked.html'
    ok('board', '--web', '--out', str(out_html))
    content = out_html.read_text(encoding='utf-8')
    data = json.loads(_data_block(content).group(1))
    assert next(c for c in data['cards'] if c['id'] == b)['meta']['blocked_by'] == a
    assert 'blocked_by' not in next(c for c in data['cards'] if c['id'] == a)['meta']
    assert 'meta.blocked_by' in content and 'blocked by ' in content


def test_board_web_generation(repo, tmp_path):
    ok('init')
    p = ok('create', '--title', 'Setup DB', '--label', 'type:feature,tier:slice,size:small,mode:AFK')
    w = ok('create', '--title', 'API routes', '--label', 'type:feature,tier:slice,size:medium,mode:AFK', '--parent', p)
    ok('set', w, '--status', 'in progress')
    out_html = tmp_path / "custom_board.html"

    code, text = run('board', '--web', '--out', str(out_html))
    assert code == 0
    assert f"[BOARD] wrote {out_html}" in text
    assert "(2 card(s))" in text
    assert out_html.exists()

    content = out_html.read_text(encoding='utf-8')
    assert '<script id="plan-data" type="application/json">' in content
    assert 'Backlog Board' in content

    # Extract and verify JSON payload
    m = re.search(r'<script id="plan-data" type="application/json">\s*(.*?)\s*</script>', content, re.DOTALL)
    assert m is not None
    data = json.loads(m.group(1))
    assert len(data['columns']) == 6
    assert len(data['cards']) == 2

    # Check cards
    card_p = next(c for c in data['cards'] if c['id'] == p)
    assert card_p['column'] == 'planned'
    assert 'type:feature' in card_p['labels']

    card_w = next(c for c in data['cards'] if c['id'] == w)
    assert card_w['column'] == 'in progress'
    assert card_w['meta']['parent'] == p


def test_board_web_empty_store(repo, tmp_path):
    ok('init')
    out_html = tmp_path / "empty_board.html"
    code, text = run('board', '--web', '--out', str(out_html))
    assert code == 0
    assert "(0 card(s))" in text
    assert out_html.exists()
    content = out_html.read_text(encoding='utf-8')
    m = re.search(r'<script id="plan-data" type="application/json">\s*(.*?)\s*</script>', content, re.DOTALL)
    assert m is not None
    data = json.loads(m.group(1))
    assert data['cards'] == []


def test_board_web_puts_a_closed_issue_in_the_done_column(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Closed one', '--label', SLICE)
    ok('close', a)
    out_html = tmp_path / 'closed_board.html'
    ok('board', '--web', '--out', str(out_html))
    data = json.loads(_data_block(out_html.read_text(encoding='utf-8')).group(1))
    assert next(c for c in data['cards'] if c['id'] == a)['column'] == 'done'


def test_board_open_implies_web(repo, tmp_path, monkeypatch):
    ok('init')
    ok('create', '--title', 'Setup DB', '--label', SLICE)
    opened = []
    import webbrowser
    monkeypatch.setattr(webbrowser, 'open', opened.append)
    out_html = tmp_path / 'open_board.html'
    code, text = run('board', '--open', '--out', str(out_html))
    assert code == 0
    assert f"[BOARD] wrote {out_html}" in text
    assert len(opened) == 1
    assert out_html.resolve().as_uri() in opened[0]


def test_summary_markdown_table(repo):
    ok('init')
    e = ok('create', '--title', 'Auth epic', '--label', 'type:feature,tier:epic,size:large,mode:HITL')
    s1 = ok('create', '--title', 'Login flow', '--label', SLICE, '--parent', e, '--milestone', 'v1.0')
    s2 = ok('create', '--title', 'Logout flow', '--label', SLICE, '--parent', e, '--blocked-by', s1)
    ok('claim', s1, '--by', 'agent-a')

    code, text = run('summary')
    assert code == 0
    assert "| ID | Title | Status | Milestone | Blocked By | Claimed By |" in text
    assert f"| {e} | Auth epic | planned | — | — | — |" in text
    assert f"| {s1} | Login flow | in progress | v1.0 | — | agent-a |" in text
    assert f"| {s2} | Logout flow | planned | — | {s1} | — |" in text

    code, text = run('summary', '--milestone', 'v1.0')
    assert code == 0
    assert s1 in text
    assert s2 not in text
    assert e not in text

    code, text = run('summary', '--parent', e)
    assert code == 0
    assert s1 in text
    assert s2 in text
    assert e in text

    ok('close', e)
    ok('close', s1)
    ok('close', s2)
    code, text = run('summary')
    assert code == 0
    assert "[NO-ISSUES]" in text


def test_apply_moves_atomic(repo, tmp_path):
    ok('init')
    b1 = ok('create', '--title', 'Task 1', '--label', SLICE)
    b2 = ok('create', '--title', 'Task 2', '--label', SLICE)
    b3 = ok('create', '--title', 'Task 3', '--label', SLICE)

    payload = f"""# Kanban Move Batch
{b1}: Task 1 -> in progress
{b2} -> done
{b3} -> blocked
"""
    move_file = tmp_path / "moves.txt"
    move_file.write_text(payload, encoding='utf-8')

    code, text = run('apply-moves', str(move_file))
    assert code == 0
    assert "[APPLY-MOVES] applied 3 move(s)" in text

    # Verify statuses
    i1 = json.loads(ok('get', b1))
    assert i1['status'] == 'in progress'

    i2 = json.loads(ok('get', b2))
    assert i2['status'] == 'done'
    assert i2['closed'] == '2026-10-27'
    assert i2['close_reason'] == 'completed'

    i3 = json.loads(ok('get', b3))
    assert i3['status'] == 'blocked'


def test_apply_moves_unarchive_and_reopen(repo, tmp_path):
    ok('init')
    b1 = ok('create', '--title', 'Task 1', '--label', SLICE)
    # First close it to done
    ok('apply-moves', body(tmp_path, f"{b1} -> done\n", "m1.txt"))
    i1 = json.loads(ok('get', b1))
    assert i1['status'] == 'done' and i1['closed'] is not None

    # Move back to planned
    ok('apply-moves', body(tmp_path, f"{b1} -> planned\n", "m2.txt"))
    i2 = json.loads(ok('get', b1))
    assert i2['status'] == 'planned'
    assert i2['closed'] is None
    assert i2['close_reason'] is None


def test_apply_moves_claim_protection(repo, tmp_path):
    ok('init')
    b1 = ok('create', '--title', 'Task 1', '--label', SLICE)
    ok('claim', b1, '--by', 'feature/other-branch')

    # Attempt move without --force
    code, text = run('apply-moves', body(tmp_path, f"{b1} -> done\n", "claim_move.txt"))
    assert code != 0
    assert f"[CLAIMED {b1} by feature/other-branch]" in text

    # Move with --force
    code, text = run('apply-moves', body(tmp_path, f"{b1} -> done\n", "claim_move.txt"), '--force')
    assert code == 0
    i1 = json.loads(ok('get', b1))
    assert i1['status'] == 'done'


def test_apply_moves_validation_failure(repo, tmp_path):
    ok('init')
    b1 = ok('create', '--title', 'Task 1', '--label', SLICE)

    # Invalid status
    code, text = run('apply-moves', body(tmp_path, f"{b1} -> non_existent_status\n", "bad1.txt"))
    assert code != 0
    assert "line 1: unknown status 'non_existent_status'" in text

    # Non-existent issue
    code, text = run('apply-moves', body(tmp_path, "BT-999 -> done\n", "bad2.txt"))
    assert code != 0
    assert "line 1: unknown id BT-999" in text

    # Ensure b1 remained untouched (planned)
    i1 = json.loads(ok('get', b1))
    assert i1['status'] == 'planned'


# --- board --web: data is data, never markup; a browser only on --open --------------------------------------------

NASTY_TITLES = ['Fix C:\\path\\n handling', 'Evil </script><img src=x onerror=alert(1)>', "Quote ' and \" here",
                'Amp & <b>bold</b> &lt;', 'Sep \u2028 and \u2029 end']
NASTY_LABEL = "area:it's<b>"


def _data_block(content):
    m = re.search(r'<script id="plan-data" type="application/json">(.*?)</script>', content, re.DOTALL)
    assert m is not None
    return m


def test_board_web_embeds_nasty_titles_and_labels_as_inert_json(repo, tmp_path):
    ok('init')
    ids = {}
    for t in NASTY_TITLES:
        ids[ok('create', '--title', t, '--label', f'{SLICE},{NASTY_LABEL}')] = t
    out_html = tmp_path / 'nasty.html'
    assert run('board', '--web', '--out', str(out_html))[0] == 0
    content = out_html.read_text(encoding='utf-8')

    m = _data_block(content)
    block = m.group(1)
    assert '<' not in block and '>' not in block and '&' not in block   # escaped as \u003c \u003e \u0026
    assert '\u2028' not in block and '\u2029' not in block
    data = json.loads(block)
    assert {c['id']: c['label'] for c in data['cards']} == ids
    assert all(NASTY_LABEL in c['labels'] for c in data['cards'])

    outside = content[:m.start()] + content[m.end():]
    assert content.count('</script>') == content.count('<script')       # only the data block and the page script
    assert not re.search(r'\son[a-z]+\s*=', outside, re.I)              # no inline onclick=/onerror=/...
    assert '<img src=x' not in content


def test_board_web_data_block_holds_the_apply_command_for_the_payload(repo, tmp_path):
    ok('init')
    ok('create', '--title', 'One', '--label', SLICE)
    out_html = tmp_path / 'b.html'
    ok('board', '--web', '--out', str(out_html))
    data = json.loads(_data_block(out_html.read_text(encoding='utf-8')).group(1))
    assert data['apply_cmd'] == 'python .agents/scripts/issues.py apply-moves -'


def test_board_web_hides_filtered_cards_by_class_not_inline_style(repo, tmp_path):
    ok('init')
    ok('create', '--title', 'One', '--label', SLICE)
    out_html = tmp_path / 'b.html'
    ok('board', '--web', '--out', str(out_html))
    content = out_html.read_text(encoding='utf-8')
    assert '[style*="display: none"]' not in content
    assert 'card.style.display' not in content
    assert content.count(".board-card:not(.filtered-out)") == 3
    assert '.board-card.filtered-out { display: none; }' in content
    assert "card.classList.toggle('filtered-out'" in content


def test_board_web_opens_a_browser_only_with_open(repo, tmp_path, monkeypatch):
    import webbrowser
    opened = []
    monkeypatch.setattr(webbrowser, 'open', lambda url, *a, **k: opened.append(url))
    ok('init')
    ok('create', '--title', 'One', '--label', SLICE)
    out_html = tmp_path / 'b.html'
    text = ok('board', '--web', '--out', str(out_html))
    assert opened == [] and str(out_html) in text
    ok('board', '--web', '--open', '--out', str(out_html))
    assert opened == [out_html.resolve().as_uri()] and opened[0].startswith('file:///')


# --- apply-moves: strict, atomic, same invariants as the other writers --------------------------------------------

def _tip(repo):
    return git(repo, 'rev-parse', 'shop/issues').strip()


def test_apply_moves_mixed_good_and_bad_file_applies_nothing_and_lists_every_bad_line(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    b = ok('create', '--title', 'Beta', '--label', SLICE)
    before = _tip(repo)
    moves = (f"Please apply these moves:\n{a} -> in progress\n"          # good
             "BT-LOCAL-ghost -> done\n"                                   # line 3: unknown id
             f"{b} -> sideways\n"                                         # line 4: unknown status
             "this line is not a move\n"                                  # line 5: unparseable
             f"{b} -> blocked\n")                                         # good
    code, text = run('apply-moves', body(tmp_path, moves, 'mixed.txt'))
    assert code == 1 and _tip(repo) == before
    assert 'nothing applied' in text
    assert 'line 3: unknown id BT-LOCAL-ghost' in text
    assert "line 4: unknown status 'sideways'" in text
    assert 'line 5:' in text and 'line 2:' not in text and 'line 6:' not in text
    assert json.loads(ok('get', a))['status'] == 'planned'


def test_apply_moves_with_no_moves_is_an_error(repo, tmp_path):
    ok('init')
    before = _tip(repo)
    for i, text in enumerate(('', '\n\n', '# just a comment\n', 'Please apply these moves:\n')):
        code, out_text = run('apply-moves', body(tmp_path, text, f'empty{i}.txt'))
        assert code == 1 and 'no moves' in out_text, repr(text)
    assert _tip(repo) == before


def test_apply_moves_titles_may_contain_hyphens_and_arrows_and_the_header_is_ignored(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    b = ok('create', '--title', 'Beta', '--label', SLICE)
    c = ok('create', '--title', 'Gamma', '--label', SLICE)
    moves = ("Please apply the following board card moves to the source and rebuild the board:\n"
             "# a comment\n\n"
             f"{a}: add-thing -> in progress\n"
             f"{b} Fix a>b handling -> blocked\n"
             f"{c} x -> y -> needs_spec\n")                                # the LAST arrow separates the status
    code, text = run('apply-moves', body(tmp_path, moves, 'titles.txt'))
    assert code == 0, text
    assert json.loads(ok('get', a))['status'] == 'in progress'
    assert json.loads(ok('get', b))['status'] == 'blocked'
    assert json.loads(ok('get', c))['status'] == 'needs_spec'


def test_apply_moves_accepts_the_board_status_spellings(repo, tmp_path):
    ok('init')
    ids = [ok('create', '--title', t, '--label', SLICE) for t in ('A1', 'A2', 'A3', 'A4')]
    moves = (f"{ids[0]} -> Needs Spec\n{ids[1]} -> IN_PROGRESS\n{ids[2]} ->   in   review\n"
             f"{ids[3]} -> needs_spec\n")
    code, text = run('apply-moves', body(tmp_path, moves, 'spell.txt'))
    assert code == 0, text
    assert [json.loads(ok('get', i))['status'] for i in ids] == ['needs_spec', 'in progress', 'in review', 'needs_spec']


def test_apply_moves_to_done_is_exactly_close_and_away_from_done_is_reopen(repo, tmp_path):
    ok('init')
    ref = ok('create', '--title', 'Ref', '--label', SLICE)
    mv = ok('create', '--title', 'Mv', '--label', SLICE)
    for i in (ref, mv):
        ok('claim', i, '--by', 'main')
    ok('close', ref)
    ok('apply-moves', body(tmp_path, f"{mv} -> done\n", 'd.txt'))
    keys = ('status', 'closed', 'close_reason', 'claimed_by', 'state')
    r, m = json.loads(ok('get', ref)), json.loads(ok('get', mv))
    assert {k: r[k] for k in keys} == {k: m[k] for k in keys}
    assert m['claimed_by'] is None and m['close_reason'] == 'completed'
    tree = git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues')
    assert f'docs/issues/archive/{mv}.md' in tree and f'docs/issues/{mv}.md' not in tree

    ok('reopen', ref, '--status', 'planned')
    ok('apply-moves', body(tmp_path, f"{mv} -> planned\n", 'r.txt'))
    r, m = json.loads(ok('get', ref)), json.loads(ok('get', mv))
    assert {k: r[k] for k in keys} == {k: m[k] for k in keys}
    assert m['closed'] is None and m['state'] == 'OPEN'
    tree = git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues')
    assert f'docs/issues/{mv}.md' in tree and f'docs/issues/archive/{mv}.md' not in tree


def test_apply_moves_other_moves_are_set_status(repo, tmp_path):
    ok('init')
    ref = ok('create', '--title', 'Ref', '--label', SLICE)
    mv = ok('create', '--title', 'Mv', '--label', SLICE)
    ok('claim', ref, '--by', 'main')
    ok('claim', mv, '--by', 'main')
    ok('set', ref, '--status', 'blocked')
    ok('apply-moves', body(tmp_path, f"{mv} -> blocked\n", 'b.txt'))
    r, m = json.loads(ok('get', ref)), json.loads(ok('get', mv))
    for k in ('status', 'claimed_by', 'closed', 'labels'):
        assert r[k] == m[k], k
    assert m['status'] == 'blocked'


def test_apply_moves_twice_to_one_issue_in_one_batch_keeps_the_last(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    code, text = run('apply-moves', body(tmp_path, f"{a} -> done\n{a} -> blocked\n", 'twice.txt'))
    assert code == 0, text
    issue = json.loads(ok('get', a))
    assert issue['status'] == 'blocked' and issue['closed'] is None
    tree = git(repo, 'ls-tree', '-r', '--name-only', 'shop/issues')
    assert f'docs/issues/{a}.md' in tree and f'docs/issues/archive/{a}.md' not in tree


def test_apply_moves_in_review_to_done_needs_a_merge_for_epics_and_standalone_issues(repo, tmp_path):
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    child = ok('create', '--title', 'Invoices', '--label', SLICE, '--parent', epic)
    solo = ok('create', '--title', 'Solo', '--label', 'type:bug,mode:AFK,size:small')
    for i in (epic, child, solo):
        ok('set', i, '--status', 'in review')
    before = _tip(repo)

    code, text = run('apply-moves', body(tmp_path, f"{epic} -> done\n", 'e.txt'))
    assert code == 1 and f'{epic}' in text and 'not merged' in text and _tip(repo) == before
    code, text = run('apply-moves', body(tmp_path, f"{solo} -> done\n", 's.txt'))
    assert code == 1 and 'not merged' in text and _tip(repo) == before
    # a refused move refuses the whole batch, a slice or --force goes through
    code, text = run('apply-moves', body(tmp_path, f"{child} -> done\n{epic} -> done\n", 'both.txt'))
    assert code == 1 and json.loads(ok('get', child))['status'] == 'in review'
    code, text = run('apply-moves', body(tmp_path, f"{child} -> done\n", 'c.txt'))
    assert code == 0 and json.loads(ok('get', child))['status'] == 'done'
    code, text = run('apply-moves', body(tmp_path, f"{epic} -> done\n{solo} -> done\n", 'f.txt'), '--force')
    assert code == 0 and json.loads(ok('get', epic))['closed'] and json.loads(ok('get', solo))['closed']


def test_apply_moves_in_review_epic_to_done_is_allowed_once_merged_and_other_statuses_are_free(repo, tmp_path):
    ok('init')
    merged_epic = ok('create', '--title', 'Auth', '--label', 'type:feature,tier:epic')
    wip_epic = ok('create', '--title', 'Search', '--label', 'type:feature,tier:epic')
    ok('set', merged_epic, '--status', 'in review')
    git(repo, 'checkout', '-qb', f'feature/{merged_epic}-work')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge auth', f'feature/{merged_epic}-work')
    ok('set', wip_epic, '--status', 'in progress')
    code, text = run('apply-moves', body(tmp_path, f"{merged_epic} -> done\n{wip_epic} -> done\n", 'm.txt'))
    assert code == 0, text
    assert json.loads(ok('get', merged_epic))['closed'] and json.loads(ok('get', wip_epic))['closed']


def test_apply_moves_dry_run_validates_and_writes_nothing(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    before = _tip(repo)
    code, text = run('apply-moves', body(tmp_path, f"{a} -> blocked\n", 'dry.txt'), '--dry-run')
    assert code == 0 and _tip(repo) == before
    assert f'{a}: planned -> blocked' in text and 'dry run' in text
    code, text = run('apply-moves', body(tmp_path, f"{a} -> sideways\n", 'dry2.txt'), '--dry-run')
    assert code == 1 and "unknown status 'sideways'" in text and _tip(repo) == before


def test_apply_moves_prints_one_line_per_applied_move_and_a_summary(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    b = ok('create', '--title', 'Beta', '--label', SLICE)
    code, text = run('apply-moves', body(tmp_path, f"{a} -> blocked\n{b} -> planned\n", 'out.txt'))
    lines = text.splitlines()
    assert code == 0 and f'{a}: planned -> blocked' in lines[0]
    assert lines[-1] == '[APPLY-MOVES] applied 1 move(s)' and len(lines) == 2    # b is already planned: no line


def test_apply_moves_reads_stdin(repo, monkeypatch):
    import io
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    monkeypatch.setattr(sys, 'stdin', io.StringIO(f"{a} -> blocked\n"))
    assert run('apply-moves', '-')[0] == 0
    assert json.loads(ok('get', a))['status'] == 'blocked'


# --- apply-moves: a guarded move (in progress / in review / done) is refused while a blocker is open (BT-241) ----------

SOLO = 'type:bug,mode:AFK,size:small'    # a standalone issue: its own ship unit, merged only once done


def _gated(label=SOLO):
    """(blocker, dependent): two standalone issues, the dependent created `--blocked-by` the blocker."""
    blocker = ok('create', '--title', 'Blocker', '--label', label)
    return blocker, ok('create', '--title', 'Dependent', '--label', SLICE, '--blocked-by', blocker)


def _moves(tmp_path, text, name='m.txt'):
    return body(tmp_path, text, name)


@pytest.mark.parametrize('target', ['in progress', 'in review', 'done'])
def test_apply_moves_refuses_a_guarded_target_while_a_blocker_is_open(repo, tmp_path, target):
    ok('init')
    blocker, dep = _gated()
    before = _tip(repo)
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> {target}\n"))
    assert code == 1 and _tip(repo) == before
    assert 'nothing applied' in text and f'line 1: [BLOCKED {dep} <- {blocker}]' in text and '--force' in text
    assert json.loads(ok('get', dep))['status'] == 'planned'


@pytest.mark.parametrize('target', ['in progress', 'in review', 'done'])
def test_apply_moves_force_moves_past_an_open_blocker_and_keeps_the_edge(repo, tmp_path, target):
    ok('init')
    blocker, dep = _gated()
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> {target}\n"), '--force')
    assert code == 0, text
    moved = json.loads(ok('get', dep))
    assert moved['status'] == target and moved['blocked_by'] == [blocker]


def test_apply_moves_to_unguarded_statuses_is_never_refused_and_set_stays_unguarded(repo, tmp_path, monkeypatch):
    ok('init')
    blocker, dep = _gated()
    monkeypatch.setattr(issues, 'make_merged_of', lambda store: pytest.fail('merged_of built without a guarded move'))
    for target in ('blocked', 'needs_spec', 'planned'):
        code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> {target}\n", f'{target}.txt'))
        assert code == 0, (target, text)
        assert json.loads(ok('get', dep))['status'] == target
    ok('set', dep, '--status', 'in progress')          # set, close, reopen, claim are not guarded
    ok('close', dep)
    ok('reopen', dep, '--status', 'planned')


def test_apply_moves_a_done_standalone_blocker_allows_the_move_an_in_review_one_does_not(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    ok('set', blocker, '--status', 'in review')
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"))
    assert code == 1 and f'[BLOCKED {dep} <- {blocker}]' in text      # cross-unit: merged only when done
    ok('close', blocker)
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"))
    assert code == 0, text
    assert json.loads(ok('get', dep))['status'] == 'in progress'


@pytest.mark.parametrize('blocker_status', ['in progress', 'in review', 'done'])
def test_apply_moves_a_same_unit_blocker_clears_once_in_review_or_done(repo, tmp_path, blocker_status):
    ok('init')
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic')
    first = ok('create', '--title', 'DB', '--label', SLICE, '--parent', epic)
    second = ok('create', '--title', 'UI', '--label', SLICE, '--parent', epic, '--blocked-by', first)
    ok('set', first, '--status', blocker_status)
    code, text = run('apply-moves', _moves(tmp_path, f"{second} -> in progress\n"))
    if blocker_status == 'in progress':
        assert code == 1 and f'[BLOCKED {second} <- {first}]' in text
    else:
        assert code == 0, text
        assert json.loads(ok('get', second))['status'] == 'in progress'


def test_apply_moves_a_parent_epics_open_blocker_refuses_a_child_slice(repo, tmp_path):
    ok('init')
    gate = ok('create', '--title', 'Gate', '--label', SOLO)
    epic = ok('create', '--title', 'Billing', '--label', 'type:feature,tier:epic', '--blocked-by', gate)
    child = ok('create', '--title', 'Invoices', '--label', SLICE, '--parent', epic)
    code, text = run('apply-moves', _moves(tmp_path, f"{child} -> in progress\n"))
    assert code == 1 and f'[BLOCKED {child} <- {gate}]' in text
    ok('close', gate)
    assert run('apply-moves', _moves(tmp_path, f"{child} -> in progress\n"))[0] == 0


def test_apply_moves_a_cross_unit_slice_blocker_done_but_unmerged_refuses_until_merged(repo, tmp_path):
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'ARCHITECTURE.md').write_text('---\ntracker: local\n---\n')
    epic, db = _blocker_with_tip_and_deleted_branch(repo, merge=False)
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--blocked-by', db)
    code, text = run('apply-moves', _moves(tmp_path, f"{ui} -> in progress\n"))
    assert code == 1 and f'[BLOCKED {ui} <- {db}]' in text and 'not merged' in text


def test_apply_moves_a_cross_unit_slice_blocker_clears_once_merged(repo, tmp_path):
    (repo / '.memory').mkdir()
    (repo / '.memory' / 'ARCHITECTURE.md').write_text('---\ntracker: local\n---\n')
    epic, db = _blocker_with_tip_and_deleted_branch(repo, merge=True)
    ui = ok('create', '--title', 'UI', '--label', SLICE, '--blocked-by', db)
    code, text = run('apply-moves', _moves(tmp_path, f"{ui} -> in progress\n"))
    assert code == 0, text
    assert json.loads(ok('get', ui))['status'] == 'in progress'


@pytest.mark.parametrize('order', ['blocker first', 'dependent first'])
def test_apply_moves_judges_the_batch_end_state_so_line_order_is_free(repo, tmp_path, order):
    ok('init')
    blocker, dep = _gated()
    lines = [f"{blocker} -> done\n", f"{dep} -> in progress\n"]
    code, text = run('apply-moves', _moves(tmp_path, ''.join(lines if order == 'blocker first' else lines[::-1])))
    assert code == 0, text
    assert json.loads(ok('get', blocker))['closed'] and json.loads(ok('get', dep))['status'] == 'in progress'


def test_apply_moves_moving_only_the_dependent_refuses_where_the_pair_passes(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"))
    assert code == 1 and f'[BLOCKED {dep} <- {blocker}]' in text


def test_apply_moves_a_refused_batch_applies_nothing_and_lists_every_bad_line(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    other_blocker, other_dep = _gated()
    fine = ok('create', '--title', 'Fine', '--label', SLICE)
    before = _tip(repo)
    moves = (f"{fine} -> in progress\n"                      # line 1: good
             f"{dep} -> in progress\n"                       # line 2: blocked
             "BT-LOCAL-ghost -> done\n"                      # line 3: unknown id
             f"{other_dep} -> done\n")                       # line 4: blocked
    code, text = run('apply-moves', _moves(tmp_path, moves))
    assert code == 1 and _tip(repo) == before and 'nothing applied' in text
    assert f'line 2: [BLOCKED {dep} <- {blocker}]' in text and f'line 4: [BLOCKED {other_dep} <- {other_blocker}]' in text
    assert 'line 3: unknown id BT-LOCAL-ghost' in text and 'line 1:' not in text
    assert json.loads(ok('get', fine))['status'] == 'planned'


def test_apply_moves_dry_run_shows_the_same_refusal_and_force_dry_run_passes(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    before = _tip(repo)
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"), '--dry-run')
    assert code == 1 and f'[BLOCKED {dep} <- {blocker}]' in text and _tip(repo) == before
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"), '--dry-run', '--force')
    assert code == 0 and 'dry run' in text and _tip(repo) == before


def test_apply_moves_a_card_already_in_the_target_is_not_refused_when_the_board_resends_it(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    ok('set', dep, '--status', 'in progress')
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"))
    assert code == 0 and '(already in place)' in text


def test_apply_moves_reopening_a_done_card_into_in_progress_is_refused_while_a_blocker_is_open(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    ok('close', dep)
    before = _tip(repo)
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n"))
    assert code == 1 and f'[BLOCKED {dep} <- {blocker}]' in text and _tip(repo) == before
    assert json.loads(ok('get', dep))['closed']


def test_apply_moves_reports_the_line_of_the_last_move_of_a_card(repo, tmp_path):
    ok('init')
    blocker, dep = _gated()
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n\n{dep} -> in review\n"))
    assert code == 1 and f'line 3: [BLOCKED {dep} <- {blocker}]' in text and 'line 1:' not in text
    # a card moved into a guarded status and on to an unguarded one ends unguarded: the end state decides
    code, text = run('apply-moves', _moves(tmp_path, f"{dep} -> in progress\n{dep} -> blocked\n", 'back.txt'))
    assert code == 0, text


def _place_board_template(skills_dir):
    dst = skills_dir / 'plan-html' / 'assets' / 'templates' / 'board.html'
    dst.parent.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / 'src' / 'skills' / 'plan-html' / 'assets' / 'templates' / 'board.html'
    dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
    return dst


def test_find_board_template_resolves_plugin_mode_locations(repo, tmp_path, monkeypatch):
    fake_script = repo / '.agents' / 'scripts' / 'issues.py'
    home = tmp_path / 'home'
    home.mkdir()
    monkeypatch.setattr(issues, '__file__', str(fake_script))
    monkeypatch.delenv('STRATOSPHERE_PLUGIN_SKILLS', raising=False)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('USERPROFILE', str(home))

    # Absent everywhere -> IssuesError
    with pytest.raises(issues.IssuesError):
        issues._find_board_template()

    # 1. STRATOSPHERE_PLUGIN_SKILLS (also overrides sibling src/skills even without __file__ patch)
    env_skills = tmp_path / 'env_skills'
    env_tpl = _place_board_template(env_skills)
    monkeypatch.setenv('STRATOSPHERE_PLUGIN_SKILLS', str(env_skills))
    assert issues._find_board_template() == env_tpl

    # 2. ~/.gemini/config/plugins/<id>/skills (newest match wins)
    monkeypatch.delenv('STRATOSPHERE_PLUGIN_SKILLS', raising=False)
    _place_board_template(home / '.gemini' / 'config' / 'plugins' / '100' / 'skills')
    newer_tpl = _place_board_template(home / '.gemini' / 'config' / 'plugins' / '200' / 'skills')
    assert issues._find_board_template() == newer_tpl

    # 3. Version-sorted ~/.claude/plugins/cache/*/stratosphere-os/<ver>/...
    home_claude = tmp_path / 'home_claude'
    monkeypatch.setenv('HOME', str(home_claude))
    monkeypatch.setenv('USERPROFILE', str(home_claude))
    mkt = home_claude / '.claude' / 'plugins' / 'cache' / 'mkt' / 'stratosphere-os'
    _place_board_template(mkt / '5.2.1' / 'dist' / 'skills')
    tpl_530 = _place_board_template(mkt / '5.3.0' / 'dist' / 'skills')
    assert issues._find_board_template() == tpl_530

    _place_board_template(mkt / '1.9.0' / 'dist' / 'skills')
    tpl_5100 = _place_board_template(mkt / '5.10.0' / 'dist' / 'skills')
    assert issues._find_board_template() == tpl_5100

    # Dedicated 1.9.0 vs 1.10.0 check
    home_claude2 = tmp_path / 'home_claude2'
    monkeypatch.setenv('HOME', str(home_claude2))
    monkeypatch.setenv('USERPROFILE', str(home_claude2))
    mkt2 = home_claude2 / '.claude' / 'plugins' / 'cache' / 'mkt' / 'stratosphere-os'
    _place_board_template(mkt2 / '1.9.0' / 'dist' / 'skills')
    tpl_1100 = _place_board_template(mkt2 / '1.10.0' / 'dist' / 'skills')
    assert issues._find_board_template() == tpl_1100


def test_find_board_template_env_override_beats_src_sibling(repo, tmp_path, monkeypatch):
    env_skills = tmp_path / 'env_skills'
    env_tpl = _place_board_template(env_skills)
    monkeypatch.setenv('STRATOSPHERE_PLUGIN_SKILLS', str(env_skills))
    assert issues._find_board_template() == env_tpl
    ok('init')
    ok('create', '--title', 'Plugin Board', '--label', SLICE)
    out_html = tmp_path / 'plugin_board.html'
    code, text = run('board', '--web', '--out', str(out_html))
    assert code == 0 and out_html.is_file(), text


# --- BT-281: numbered local IDs (`BT-L-<NNN>-<slug>`), shorthand lookup, card IDs on board.html ---------------

def test_create_mints_sequential_bt_l_ids_and_continues_after_closed_and_legacy(repo):
    ok('init')
    c1 = ok('create', '--title', 'Order client', '--label', SLICE)
    assert c1 == 'BT-L-001-order-client'
    c2 = ok('create', '--title', 'Order client', '--label', SLICE)
    assert c2 == 'BT-L-002-order-client'
    ok('close', c1)
    c3 = ok('create', '--title', 'Risk guard', '--label', SLICE)
    assert c3 == 'BT-L-003-risk-guard'


def test_shorthand_numeric_lookup_across_all_commands(repo, tmp_path):
    ok('init')
    epic = ok('create', '--title', 'Order epic', '--label', 'type:feature,tier:epic')
    s1 = ok('create', '--title', 'Order client', '--label', SLICE, '--parent', '1')
    s2 = ok('create', '--title', 'Retry loop', '--label', SLICE, '--parent', '#1', '--blocked-by', '002')
    assert epic == 'BT-L-001-order-epic'
    assert s1 == 'BT-L-002-order-client'
    assert s2 == 'BT-L-003-retry-loop'
    assert json.loads(ok('get', s1))['parent'] == epic
    assert json.loads(ok('get', s2))['blocked_by'] == [s1]

    # get / set / claim / comment / resume note / close / reopen / children / blockers / list / board / summary
    for ident in ('2', '002', '#2', 'BT-L-2', 'BT-L-002', 'BT-LOCAL-2', 'BT-LOCAL-002'):
        assert json.loads(ok('get', ident))['id'] == s1

    assert ok('set', '2', '--status', 'blocked', '--milestone', 'v1.0.0') == s1
    assert run('set', '2', '--parent', '002') == (1, f'[ERROR] {s1} cannot be its own parent')
    assert run('set', '2', '--add-blocker', '#2') == (1, f'[ERROR] {s1} cannot block itself')
    assert run('set', '2', '--add-blocker', '3') == (1, f'[ERROR] blocked-by cycle: {s1} <- {s2} <- {s1}')
    assert ok('set', '3', '--remove-blocker', '002') == s2
    assert json.loads(ok('get', s2))['blocked_by'] == []
    assert ok('set', '3', '--add-blocker', 'BT-L-002') == s2

    assert ok('claim', '#2', '--by', 'feat/order') == s1
    assert json.loads(ok('get', '2'))['claimed_by'] == 'feat/order'

    assert ok('comment', '002', '--body', 'note via shorthand') == s1
    assert json.loads(ok('get', s1))['comments'] == ['- 2026-10-27: note via shorthand']

    assert ok('comment', 'BT-L-002', '--body', f'{RESUME}\nBranch: feat/order') == s1
    resume_file = repo / '.memory' / 'resume' / f'{s1}.md'
    assert resume_file.is_file() and 'Branch: feat/order' in resume_file.read_text(encoding='utf-8')

    assert [i['id'] for i in json.loads(ok('children', '1'))] == [s1, s2]
    assert json.loads(ok('blockers', '3')) == [{'id': s1, 'title': 'Order client', 'status': 'in progress'}]
    assert [i['id'] for i in json.loads(ok('list', '--parent', '#1'))] == [s1, s2]
    assert s1 in ok('board', '--parent', '001') and epic in ok('board', '--parent', '1')
    assert f'| {s1} |' in ok('summary', '--parent', 'BT-L-001')

    assert ok('close', '2') == s1
    assert json.loads(ok('get', s1))['state'] == 'CLOSED'
    assert ok('reopen', '#2', '--status', 'planned') == s1
    assert json.loads(ok('get', s1))['state'] == 'OPEN'

    # apply-moves resolves numeric shorthand and records canonical IDs
    code, text = run('apply-moves', body(tmp_path, '2 -> blocked\n3 -> planned\n', 'shorthand_moves.txt'))
    assert code == 0 and f'{s1}: planned -> blocked' in text
    assert json.loads(ok('get', s1))['status'] == 'blocked'


def test_shorthand_lookup_ambiguous_collision_and_unknown(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    # Seed a second issue sharing numeric sequence 1 under legacy prefix BT-LOCAL-1-beta
    store = issues.Tracker().store()
    b_issue = {k: None for k in issues.FIELDS} | {
        'type': 'issue', 'id': 'BT-LOCAL-1-beta', 'title': 'Beta', 'status': 'planned',
        'labels': SLICE.split(','), 'blocked_by': [], 'body': '', 'comments': [],
    }
    issues.Tracker().write(lambda s: (s.changes(b_issue), 'ok'), 'seed collision')
    assert a == 'BT-L-001-alpha'

    # Exact IDs still resolve cleanly
    assert json.loads(ok('get', a))['id'] == a
    assert json.loads(ok('get', 'BT-LOCAL-1-beta'))['id'] == 'BT-LOCAL-1-beta'

    # Ambiguous shorthand fails cleanly across commands
    for argv in (('get', '1'), ('set', '001', '--status', 'blocked'), ('claim', '#1'),
                 ('close', 'BT-L-1'), ('reopen', 'BT-L-001'), ('comment', '1', '--body', 'x'),
                 ('children', '1'), ('blockers', '1'), ('list', '--parent', '1'),
                 ('board', '--parent', '1'), ('summary', '--parent', '1'),
                 ('create', '--title', 'Child', '--parent', '1')):
        code, text = run(*argv)
        assert code == 1 and '[AMBIGUOUS' in text, (argv, code, text)

    code, text = run('apply-moves', body(tmp_path, '1 -> blocked\n', 'ambig.txt'))
    assert code == 1 and '[AMBIGUOUS' in text

    # Unknown shorthand fails cleanly
    code, text = run('get', '999')
    assert code == 1 and '[UNKNOWN 999]' in text


def test_apply_moves_hash_shorthand_and_comment_skipping(repo, tmp_path):
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    b = ok('create', '--title', 'Beta', '--label', SLICE)
    moves = (
        "Please apply these moves:\n"
        "## Heading to ignore\n"
        "# comment to ignore\n"
        "#1 -> blocked\n"
        "#2: Beta -> in progress\n"
    )
    code, text = run('apply-moves', body(tmp_path, moves, 'hash_moves.txt'))
    assert code == 0, text
    assert '[APPLY-MOVES] applied 2 move(s)' in text
    assert f'{a}: planned -> blocked' in text and f'{b}: planned -> in progress' in text
    assert json.loads(ok('get', a))['status'] == 'blocked'
    assert json.loads(ok('get', b))['status'] == 'in progress'

    code, text = run('apply-moves', body(tmp_path, '## heading\n# comment\n', 'only_comments.txt'))
    assert code == 1 and 'no moves' in text


def test_ambiguous_issue_error_preserved_by_store_apply_moves_and_remove_blocker(repo, tmp_path):
    assert issubclass(issues.AmbiguousIssueError, issues.IssuesError)
    ok('init')
    a = ok('create', '--title', 'Alpha', '--label', SLICE)
    dep = ok('create', '--title', 'Dependent', '--label', SLICE, '--blocked-by', a)
    b_issue = {k: None for k in issues.FIELDS} | {
        'type': 'issue', 'id': 'BT-LOCAL-1-beta', 'title': 'Beta', 'status': 'planned',
        'labels': SLICE.split(','), 'blocked_by': [], 'body': '', 'comments': [],
    }
    issues.Tracker().write(lambda s: (s.changes(b_issue), 'ok'), 'seed collision')

    store = issues.Tracker().store()
    with pytest.raises(issues.AmbiguousIssueError, match=r'\[AMBIGUOUS 1\]') as exc_info:
        store.resolve('1')
    assert isinstance(exc_info.value, issues.IssuesError)
    assert a in str(exc_info.value) and 'BT-LOCAL-1-beta' in str(exc_info.value)

    code, text = run('set', dep, '--remove-blocker', '1')
    assert code == 1 and '[AMBIGUOUS 1]' in text
    assert json.loads(ok('get', dep))['blocked_by'] == [a]

    code, text = run('apply-moves', body(tmp_path, '1 -> blocked\n#1: Alpha -> blocked\n', 'ambig_moves.txt'))
    assert code == 1
    assert 'line 1: [AMBIGUOUS 1]' in text
    assert 'line 2: [AMBIGUOUS #1]' in text


def test_board_web_renders_card_id_div(repo, tmp_path, monkeypatch):
    skills_dir = tmp_path / 'skills'
    _place_board_template(skills_dir)
    monkeypatch.setenv('STRATOSPHERE_PLUGIN_SKILLS', str(skills_dir))
    ok('init')
    bt = ok('create', '--title', 'Order client', '--label', SLICE)
    out_html = tmp_path / 'cards.html'
    ok('board', '--web', '--out', str(out_html))
    content = out_html.read_text(encoding='utf-8')
    assert '<div class="card-id">${esc(c.id)}</div>' in content
    assert '.card-id' in content
    data = json.loads(_data_block(content).group(1))
    assert data['cards'][0]['id'] == bt


# --- BT-293: working-tree views (.memory/BOARD.md + .memory/board.html), refresh, and HTML board enrichments ------

def test_board_web_emits_ready_blocked_pills_meta_and_open_only_details(repo, tmp_path):
    ok('init')
    epic = ok('create', '--title', 'Auth Epic', '--label', 'type:feature,tier:epic', '--milestone', 'v1.0.0')
    a = ok('create', '--title', 'Login', '--label', f'{SLICE},scope:baseline', '--milestone', 'v1.0.0',
           '--parent', epic, '--body-file', body(tmp_path, BODY, 'a.md'))
    ok('comment', a, '--body', 'First note')
    b = ok('create', '--title', 'Sessions', '--label', SLICE, '--milestone', 'v1.0.0',
           '--parent', epic, '--blocked-by', a, '--body-file', body(tmp_path, '### Overview\nBlocked slice.\n', 'b.md'))
    c = ok('create', '--title', 'Audit', '--label', SLICE, '--milestone', 'v1.0.0', '--parent', epic)
    ok('claim', c, '--by', 'feat/audit')
    d = ok('create', '--title', 'Done slice', '--label', SLICE, '--milestone', 'v1.0.0',
           '--parent', epic, '--body-file', body(tmp_path, 'Secret archived body', 'd.md'))
    ok('close', d)

    out_html = tmp_path / 'enriched.html'
    out_text = ok('board', '--web', '--out', str(out_html))
    assert out_html.resolve().as_uri() in out_text

    content = out_html.read_text(encoding='utf-8')
    data = json.loads(_data_block(content).group(1))
    cards = {card['id']: card for card in data['cards']}

    assert 'ready' in cards[a]['labels'] and 'blocked' not in cards[a]['labels']
    assert cards[a]['meta']['milestone'] == 'v1.0.0'
    assert cards[a]['meta']['ice'] == '0.8'
    assert 'Login.' in cards[a]['details'] and 'First note' in cards[a]['details']

    assert 'blocked' in cards[b]['labels'] and 'ready' not in cards[b]['labels']
    assert cards[b]['meta']['blocked_by'] == a
    assert 'Blocked slice.' in cards[b]['details']

    assert cards[c]['meta']['claimed_by'] == 'feat/audit'
    assert 'ready' not in cards[c]['labels'] and 'blocked' not in cards[c]['labels']

    assert 'details' not in cards[d]
    assert 'Secret archived body' not in content


def test_board_web_escapes_nasty_details_and_preserves_drawer_invariants(repo, tmp_path, monkeypatch):
    monkeypatch.setenv('STRATOSPHERE_PLUGIN_SKILLS', str(REPO_ROOT / 'src' / 'skills'))
    ok('init')
    nasty_body = "Evil </script><img src=x onerror=alert(1)> & \u2028 \u2029"
    bt = ok('create', '--title', 'XSS test', '--label', SLICE, '--milestone', 'v1.0.0',
            '--body-file', body(tmp_path, nasty_body, 'nasty.md'))
    ok('comment', bt, '--body', '<b>comment</b>')
    out_html = tmp_path / 'xss.html'
    ok('board', '--web', '--out', str(out_html))
    content = out_html.read_text(encoding='utf-8')

    m = _data_block(content)
    block = m.group(1)
    assert '<' not in block and '>' not in block and '&' not in block
    assert '\u2028' not in block and '\u2029' not in block
    outside = content[:m.start()] + content[m.end():]
    assert content.count('</script>') == content.count('<script')
    assert not re.search(r'\son[a-z]+\s*=', outside, re.I)
    assert content.count('.board-card:not(.filtered-out)') == 3
    assert 'id="card-drawer"' in content
    assert 'data-action="show-details"' in content
    assert 'meta.milestone' in content and 'meta.ice' in content and 'meta.claimed_by' in content


def test_render_board_md_and_refresh_command(repo, tmp_path):
    ok('init')
    epic = ok('create', '--title', 'Core Auth', '--label', 'type:feature,tier:epic', '--milestone', 'v1.0.0')
    done_s = ok('create', '--title', 'Done task', '--label', SLICE, '--milestone', 'v1.0.0', '--parent', epic)
    ok('close', done_s)
    wip_s = ok('create', '--title', 'WIP task', '--label', SLICE, '--milestone', 'v1.0.0', '--parent', epic)
    ok('claim', wip_s, '--by', 'feat/wip')
    rev_s = ok('create', '--title', 'Review task', '--label', SLICE, '--milestone', 'v1.0.0', '--parent', epic, '--status', 'in review')

    base_low = ok('create', '--title', 'Base low', '--label', 'type:feature,mode:AFK,tier:slice,size:large,scope:baseline',
                  '--milestone', 'v1.0.0', '--parent', epic,
                  '--body-file', body(tmp_path, "- **Impact:** 0.6\n- **Confidence:** 100%\n", 'bl.md'))
    base_high = ok('create', '--title', 'Base high', '--label', 'type:feature,mode:AFK,tier:slice,size:small,scope:baseline',
                   '--milestone', 'v1.0.0', '--parent', epic,
                   '--body-file', body(tmp_path, "- **Impact:** 0.9\n- **Confidence:** 100%\n", 'bh.md'))
    diff_s = ok('create', '--title', 'Diff slice', '--label', 'type:feature,mode:AFK,tier:slice,size:small,scope:differentiator',
                '--milestone', 'v1.0.0', '--parent', epic,
                '--body-file', body(tmp_path, "- **Impact:** 0.8\n- **Confidence:** 100%\n", 'df.md'))
    unlbl_s = ok('create', '--title', 'Unlabelled slice', '--label', 'type:feature,mode:AFK,tier:slice,size:small',
                 '--milestone', 'v1.0.0', '--parent', epic,
                 '--body-file', body(tmp_path, "- **Impact:** 1.0\n- **Confidence:** 100%\n", 'un.md'))
    spike_s = ok('create', '--title', 'Spike task', '--label', f'{SLICE},scope:baseline', '--status', 'needs_spec',
                 '--milestone', 'v1.0.0', '--parent', epic)
    blk_edge = ok('create', '--title', 'Edge blocked', '--label', SLICE, '--milestone', 'v1.0.0', '--parent', epic,
                  '--blocked-by', base_high)
    blk_hold = ok('create', '--title', 'On hold', '--label', SLICE, '--status', 'blocked', '--milestone', 'v1.0.0', '--parent', epic)

    out_text = ok('refresh')
    board_md = repo / '.memory' / 'BOARD.md'
    board_html = repo / '.memory' / 'board.html'
    assert board_md.is_file() and board_html.is_file()
    assert str(board_md) in out_text and str(board_html) in out_text
    assert board_html.resolve().as_uri() in out_text

    md_text = board_md.read_text(encoding='utf-8')
    assert md_text.startswith('<!-- GENERATED BY issues.py — DO NOT EDIT -->')
    assert '- **Branch:** shop/issues' in md_text
    assert '- **Ref:** shop/issues@' in md_text
    assert board_html.resolve().as_uri() in md_text

    # Ready / Next ordering: scope:baseline (high -> low -> spike) -> scope:differentiator -> unlabelled
    ready_sec = md_text.split('## Ready / Next', 1)[1].split('\n## ', 1)[0]
    assert ready_sec.index(base_high) < ready_sec.index(base_low) < ready_sec.index(diff_s) < ready_sec.index(unlbl_s)
    assert f'{spike_s}' in ready_sec and '[SPIKE]' in ready_sec
    assert blk_edge not in ready_sec and blk_hold not in ready_sec

    in_prog_sec = md_text.split('## In Progress', 1)[1].split('\n## ', 1)[0]
    assert wip_s in in_prog_sec and 'feat/wip' in in_prog_sec

    in_rev_sec = md_text.split('## In Review', 1)[1].split('\n## ', 1)[0]
    assert rev_s in in_rev_sec

    blocked_sec = md_text.split('## Blocked', 1)[1].split('\n## ', 1)[0]
    assert blk_hold in blocked_sec and 'on hold' in blocked_sec.lower()
    assert blk_edge in blocked_sec and base_high in blocked_sec

    epics_sec = md_text.split('## Open Epics / Milestones', 1)[1]
    assert epic in epics_sec and '1/' in epics_sec and 'v1.0.0' in epics_sec


def test_auto_refresh_on_mutations_and_bare_repo_purity(repo, tmp_path):
    # 1. Bare repo without .gitignore: mutations never touch working tree
    ok('init')
    s1 = ok('create', '--title', 'Bare one', '--label', SLICE)
    ok('set', s1, '--milestone', 'v1.0.0')
    ok('claim', s1, '--by', 'feat/s1')
    ok('comment', s1, '--body', 'note')
    ok('close', s1)
    ok('reopen', s1)
    ok('label', 'area:api')
    assert git(repo, 'status', '--porcelain') == ''
    assert not (repo / '.memory' / 'BOARD.md').exists()
    assert not (repo / '.memory' / 'board.html').exists()

    # 2. Gitignored repo: mutating commands regenerate views without altering stdout
    (repo / '.gitignore').write_text('.memory/BOARD.md\n.memory/board.html\n', encoding='utf-8')
    git(repo, 'add', '.gitignore')
    git(repo, 'commit', '-qm', 'ignore board views')

    board_md = repo / '.memory' / 'BOARD.md'
    board_html = repo / '.memory' / 'board.html'

    created = ok('create', '--title', 'Tracked view', '--label', SLICE)
    assert created.startswith('BT-L-') and '\n' not in created
    assert board_md.is_file() and board_html.is_file()
    assert created in board_md.read_text(encoding='utf-8')

    # Pure read does not recreate deleted view
    board_md.unlink()
    ok('list')
    ok('summary')
    assert not board_md.exists()

    # Resume-note comment does not refresh store views
    ok('comment', created, '--body', '<!-- stratos:resume -->\nBranch: feat/x\nNext step: y\n')
    assert not board_md.exists()

    # Normal comment refreshes views
    assert ok('comment', created, '--body', 'real update') == created
    assert board_md.is_file()

    # apply-moves refreshes views without changing stdout
    board_md.unlink()
    moves_out = ok('apply-moves', body(tmp_path, f'{created} -> in progress\n', 'mv.txt'))
    assert moves_out == f'{created}: planned -> in progress\n[APPLY-MOVES] applied 1 move(s)'
    assert board_md.is_file() and created in board_md.read_text(encoding='utf-8').split('## In Progress', 1)[1].split('\n## ', 1)[0]


def test_auto_refresh_init_migrate_sync_merged_and_missing_template(repo, tmp_path, monkeypatch):
    # Fresh repo with .gitignore for init, migrate, sync, merged --close
    (repo / '.gitignore').write_text('.memory/BOARD.md\n.memory/board.html\n', encoding='utf-8')
    git(repo, 'add', '.gitignore')
    git(repo, 'commit', '-qm', 'gi')

    # migrate
    bm = repo / '.memory' / 'BACKLOG_MAP.md'
    bm.parent.mkdir(parents=True, exist_ok=True)
    bm.write_text(
        "| ID | Title | Status | Labels | Milestone | Parent | Blocked by | ICE | Ref |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "| BT-L-001-mig | Migrated item | planned | type:feature,tier:slice,mode:AFK,size:small | v1.0.0 | — | — | — | — |\n",
        encoding='utf-8',
    )
    mig_out = ok('migrate')
    assert mig_out.startswith('[MIGRATED]')
    assert (repo / '.memory' / 'BOARD.md').is_file()
    assert 'BT-L-001-mig' in (repo / '.memory' / 'BOARD.md').read_text(encoding='utf-8')

    # merged --close
    git(repo, 'checkout', '-qb', 'feat/mig')
    (repo / 'f.txt').write_text('hi\n', encoding='utf-8')
    git(repo, 'add', 'f.txt')
    git(repo, 'commit', '-qm', 'feat')
    tip = git(repo, 'rev-parse', 'HEAD').strip()
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '--no-ff', '-qm', 'merge feat', 'feat/mig')
    ok('set', 'BT-L-001-mig', '--status', 'in review')
    ok('comment', 'BT-L-001-mig', '--body', f'Shipped on feat/mig @ {tip}')
    (repo / '.memory' / 'BOARD.md').unlink()
    assert ok('merged', '--close') == '[MERGED BT-L-001-mig]'
    assert (repo / '.memory' / 'BOARD.md').is_file()

    # Missing board.html template must not abort a write during auto-refresh
    monkeypatch.setattr(issues, '_find_board_template', lambda: (_ for _ in ()).throw(issues.IssuesError('[ERROR] missing')))
    s2 = ok('create', '--title', 'No tpl', '--label', SLICE)
    assert s2 in (repo / '.memory' / 'BOARD.md').read_text(encoding='utf-8')


def test_auto_refresh_sync_fast_forward_and_init(tmp_path, monkeypatch):
    # Upstream bare remote + two clones for sync FF test + init test
    remote = tmp_path / 'remote.git'
    git(tmp_path, 'init', '--bare', '-b', 'main', '-q', str(remote))
    a_dir = tmp_path / 'a'
    b_dir = tmp_path / 'b'
    git(tmp_path, 'clone', '-q', str(remote), str(a_dir))
    git(a_dir, 'checkout', '-qb', 'main')
    git(a_dir, 'config', 'user.email', 't@example.com')
    git(a_dir, 'config', 'user.name', 'T')
    (a_dir / '.gitignore').write_text('.memory/BOARD.md\n.memory/board.html\n', encoding='utf-8')
    git(a_dir, 'add', '.gitignore')
    git(a_dir, 'commit', '-qm', 'init')
    git(a_dir, 'push', '-q', '-u', 'origin', 'main')

    git(tmp_path, 'clone', '-q', str(remote), str(b_dir))
    git(b_dir, 'config', 'user.email', 't@example.com')
    git(b_dir, 'config', 'user.name', 'T')

    monkeypatch.chdir(a_dir)
    assert ok('init') == '[INIT remote/issues]'
    assert (a_dir / '.memory' / 'BOARD.md').is_file()
    s1 = ok('create', '--title', 'Synced item', '--label', SLICE)
    git(a_dir, 'push', '-q', 'origin', 'remote/issues')

    monkeypatch.chdir(b_dir)
    assert ok('sync') == '[SYNC-FF]'
    assert (b_dir / '.memory' / 'BOARD.md').is_file()
    assert s1 in (b_dir / '.memory' / 'BOARD.md').read_text(encoding='utf-8')



