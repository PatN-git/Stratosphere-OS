"""BT-143: deterministic spec-to-schema contract check shared by 2a/2b/2c.

Seam: the `contract_check.py` CLI (stdout + exit code). Fixtures write a small schema
in the CleanTechHub formats (`### \\`table\\`` + `- \\`col\\`:` bullets, `CREATE TABLE` /
`CREATE TYPE ... AS ENUM`) plus docs that reference it.
"""
import subprocess
import sys

import pytest

from conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "src" / "scripts" / "contract_check.py"

SCHEMA_MD = """\
# DATABASE SCHEMA

## Tables

### `companies` [LAW]
**Important columns:**
- `id`: UUID primary key.
- `name`, `website`: Profile metadata.
- `funding_stage` (Enum `funding_stage`; confirmed `'seed'`, `'series_a'`; **`'nonprofit'` is not a label**): Stage.

### `jobs` [LAW]
**Important columns:**
- `id`: UUID primary key.
- `company_id`: UUID foreign key to `companies.id`.
- `title`: Job title.
- `employment_type`: Enum `employment_type`, default `'full_time'`. Labels `'full_time'`, `'part_time'`, `'internship'`. **Not labels:** `'intern'`.
- `status`: Enum `publish_status`, default `'draft'`. Labels `'draft'` | `'live'`; `'expired'` is **not** a label.

**Relationships:**
- Belongs to: `companies(id)`

## Superseded
"""

TEMPLATE_MD = """\
## Tables

### `table_name`
**Important columns:**
- `id`:
- `created_at`:
"""

SCHEMA_SQL = """\
CREATE TYPE employment_type AS ENUM ('full_time', 'part_time', 'internship');
CREATE TABLE IF NOT EXISTS companies (
  id   uuid PRIMARY KEY,
  name text NOT NULL, -- display name, with a comma
  website text
);
CREATE TABLE IF NOT EXISTS jobs (
  id              uuid PRIMARY KEY,
  company_id      uuid NOT NULL REFERENCES companies(id),
  title           text NOT NULL,
  employment_type employment_type DEFAULT 'full_time',
  CONSTRAINT jobs_title_len CHECK (length(title) > 0)
);
"""


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "schema.md").write_text(SCHEMA_MD, encoding="utf-8")
    (tmp_path / "schema.sql").write_text(SCHEMA_SQL, encoding="utf-8")
    return tmp_path


def check(project, doc_text, *extra, schema="schema.md"):
    doc = project / "prd.md"
    doc.write_text(doc_text, encoding="utf-8")
    return run("--docs", doc, "--schema", project / schema, *extra)


def test_missing_column_is_flagged_with_line_number(project):
    r = check(project, "# PRD\n\nTrack misses in `jobs.consecutive_missing_scans`.\n")
    assert r.returncode != 0
    assert "[CONTRACT-MISSING] " in r.stdout
    assert "prd.md:3 jobs.consecutive_missing_scans (column, schema.md)" in r.stdout


def test_invalid_bound_enum_value_is_flagged(project):
    r = check(project, "Filter with `employment_type = 'intern'` only.\n")
    assert r.returncode != 0
    assert "prd.md:1 employment_type='intern' (enum-value, schema.md)" in r.stdout


def test_invalid_enum_value_via_table_qualified_column_and_colon(project):
    r = check(project, "- `jobs.status: 'expired'`\n- `funding_stage: 'nonprofit'`\n")
    assert r.returncode != 0
    assert "status='expired' (enum-value" in r.stdout
    assert "funding_stage='nonprofit' (enum-value" in r.stdout


def test_fk_to_missing_column_is_flagged(project):
    r = check(project, "`jobs.company_id` references `companies.legacy_id`.\n")
    assert r.returncode != 0
    assert "companies.legacy_id (column, schema.md)" in r.stdout
    assert "jobs.company_id" not in r.stdout


def test_valid_and_unclassifiable_references_are_not_flagged(project):
    doc = (
        "Reads `jobs.title` and `companies.name`, filters `employment_type = 'full_time'`,\n"
        "`status IN ('draft', 'live')`, the free-floating literal `'intern'`,\n"
        "the file `api/submit.js`, `jobs.json`, `src/jobs.js`, `foo.bar()`, `jobs.insert()`,\n"
        "and the bare word `widgets`. Prose jobs.bogus is outside backticks.\n"
    )
    r = check(project, doc)
    assert r.returncode == 0, r.stdout
    assert "CONTRACT-MISSING" not in r.stdout


def test_fenced_code_block_lines_are_checked(project):
    doc = "Intro\n```sql\nSELECT jobs.title,\n       jobs.ghost\nFROM jobs;\n```\n"
    r = check(project, doc)
    assert r.returncode != 0
    assert "prd.md:4 jobs.ghost (column, schema.md)" in r.stdout
    assert "jobs.title" not in r.stdout


def test_template_only_schema_skips_with_exit_zero(project):
    (project / "template.md").write_text(TEMPLATE_MD, encoding="utf-8")
    r = check(project, "`table_name.nothing` and `jobs.ghost`\n", schema="template.md")
    assert r.returncode == 0
    assert r.stdout.strip() == "[CONTRACT-SKIP] no schema declared"


def test_absent_schema_file_skips_with_exit_zero(project):
    r = check(project, "`jobs.ghost`\n", schema="nope.md")
    assert r.returncode == 0
    assert r.stdout.strip() == "[CONTRACT-SKIP] no schema declared"


def test_sql_source_must_agree_and_names_the_missing_source(project):
    # `website` is in the md and the sql; `funding_stage` is only in the md.
    r = check(project, "`companies.website` and `companies.funding_stage`\n", "--sql", project / "schema.sql")
    assert r.returncode != 0
    assert "companies.funding_stage (column, schema.sql)" in r.stdout
    assert "companies.website" not in r.stdout
    assert "(column, schema.md)" not in r.stdout


def test_sql_enum_values_are_checked_against_create_type(project):
    r = check(project, "`employment_type = 'intern'`\n", "--sql", project / "schema.sql")
    assert r.returncode != 0
    assert "employment_type='intern' (enum-value, schema.sql)" in r.stdout
    assert "(enum-value, schema.md)" in r.stdout


def test_template_md_with_sql_checks_the_sql_only(project):
    (project / "template.md").write_text(TEMPLATE_MD, encoding="utf-8")
    r = check(project, "`jobs.title` `jobs.ghost`\n", "--sql", project / "schema.sql", schema="template.md")
    assert r.returncode != 0
    assert "jobs.ghost (column, schema.sql)" in r.stdout
    assert "jobs.title" not in r.stdout


def test_alter_table_add_column_and_add_value_are_honoured(project):
    sql = project / "schema.sql"
    sql.write_text(
        SCHEMA_SQL
        + "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS consecutive_missing_scans int DEFAULT 0;\n"
        + "ALTER TYPE employment_type ADD VALUE IF NOT EXISTS 'intern';\n",
        encoding="utf-8",
    )
    r = check(project, "`jobs.consecutive_missing_scans` `employment_type = 'intern'`\n", "--sql", sql, schema="nope.md")
    assert r.returncode == 0, r.stdout


def test_clean_docs_report_ok_with_exit_zero(project):
    r = check(project, "`jobs.title` and `companies.name`\n")
    assert r.returncode == 0
    assert r.stdout.strip() == "[CONTRACT-OK] 2 reference(s) checked"


def test_multiple_docs_are_all_checked(project):
    (project / "a.md").write_text("`jobs.title`\n", encoding="utf-8")
    (project / "b.md").write_text("\n`jobs.ghost`\n", encoding="utf-8")
    r = run("--docs", project / "a.md", project / "b.md", "--schema", project / "schema.md")
    assert r.returncode != 0
    assert "b.md:2 jobs.ghost" in r.stdout
    assert "a.md:" not in r.stdout


def test_missing_doc_is_an_error_not_a_pass(project):
    r = run("--docs", project / "nope.md", "--schema", project / "schema.md")
    assert r.returncode == 2
    assert "file not found" in r.stderr


def test_bare_parenthesised_enum_list_is_parsed(project):
    # Older CleanTechHub format: no `Labels` keyword, the labels follow the type in parentheses.
    (project / "old.md").write_text(
        "### `jobs`\n- `employment_type`: Enum `employment_type` (`'full_time'`, `'part_time'`).\n",
        encoding="utf-8",
    )
    r = check(project, "`employment_type: 'intern'` `employment_type: 'part_time'`\n", schema="old.md")
    assert r.returncode != 0
    assert "employment_type='intern' (enum-value, old.md)" in r.stdout
    assert "part_time" not in r.stdout
