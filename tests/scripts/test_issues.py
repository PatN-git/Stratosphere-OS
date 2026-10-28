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
    assert bt == 'BT-LOCAL-login-form-email-link'
    issue = json.loads(ok('get', bt))
    assert issue['status'] == 'planned' and issue['state'] == 'OPEN'
    assert issue['labels'] == SLICE.split(',') and issue['milestone'] == 'v1.0.0'
    assert '### Acceptance Criteria (Verifiable)\n- [ ] Logs in' in issue['body']
    text = git(repo, 'show', f'shop/issues:docs/issues/{bt}.md')
    assert text.startswith('---\ntype: issue\nid: BT-LOCAL-login-form-email-link\ntitle: "Login form: email link"\n')
    assert git(repo, 'status', '--porcelain') == ''


def test_create_takes_a_status_label_as_the_status_field_and_suffixes_a_clashing_slug(repo):
    ok('init')
    assert ok('create', '--title', 'Spike', '--label', 'type:research,status:needs_spec') == 'BT-LOCAL-spike'
    assert json.loads(ok('get', 'BT-LOCAL-spike'))['status'] == 'needs_spec'
    assert json.loads(ok('get', 'BT-LOCAL-spike'))['labels'] == ['type:research']
    assert ok('create', '--title', 'Spike!') == 'BT-LOCAL-spike-2'


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
    ok('create', '--title', 'Bare', '--label', 'type:feature,tier:slice')
    out = ok('ready')
    assert f'{db} | planned | DB | mode:AFK size:medium type:feature | — | ICE 0.8' in out
    assert f'[BLOCKED {ui} <- {db}]' in out
    assert '[MISSING-LABELS] BT-LOCAL-bare - Bare (mode:, size:)' in out
    assert f'{ui} |' not in out
    ok('close', db)
    assert f'{ui} | planned | UI' in ok('ready')


def test_check_reports_label_composition_unknown_labels_and_dangling_ids(repo):
    ok('init')
    ok('label', 'area:BE-api')
    good = ok('create', '--title', 'Good', '--label', SLICE + ',area:BE-api')
    assert ok('check') == '[CHECK-OK 1 issue(s)]'
    ok('create', '--title', 'Bad', '--label', 'type:feature,tier:slice,area:nope')
    ok('create', '--title', 'Epic', '--label', 'type:feature,tier:epic,mode:AFK')
    code, text = run('check')
    assert code == 1
    assert '[CHECK-FAIL BT-LOCAL-bad] unknown label area:nope' in text
    assert '[CHECK-FAIL BT-LOCAL-bad] a slice needs exactly one type:, mode: and size:' in text
    assert '[CHECK-FAIL BT-LOCAL-epic] an epic needs one type: and no mode: or size:' in text
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
    assert json.loads(ok('get', 'BT-LOCAL-b'))['title'] == 'B'
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
    ok('create', '--title', 'Login form', '--label', SLICE)
    git(repo, 'checkout', '-qb', 'feature/BT-LOCAL-login-form-x')
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
    ok('create', '--title', 'Auth v2', '--label', 'type:feature,tier:epic')
    db = ok('create', '--title', 'DB', '--label', SLICE, '--parent', epic)
    git(repo, 'checkout', '-qb', 'feature/BT-LOCAL-auth-v2-x')
    (repo / 'f.txt').write_text('f\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'f')
    git(repo, 'checkout', '-q', 'main')
    assert issues.make_merged_of(issues.Tracker().store())(db) == 'none'
