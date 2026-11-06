# StratosphereOS Development Experiments & Evaluations

This directory preserves experimental test harnesses, evaluations, and analysis scripts developed during the StratosphereOS v5 architecture evolution.

## Contents

- **`evals/bt217-0f-walk-me-through/`**:
  - Benchmark evaluation of the `0f-walk-me-through` lifecycle skill.
  - Contains rubric scoring (`grades.md`), question templates (`questions.md`), prompt briefs (`brief-V0.md` through `brief-V2.md`), and raw evaluation notes.
- **`evals/bt189-backlog-map-spike/`**:
  - Spike evaluation and analysis verifying BACKLOG_MAP removal vs. GitHub tracker parity.
  - Contains RAT classification (`s1-classification.md`), write site inventory (`s2-inventory.md`), cross-repo measurements (`s3-measurements.md`), generator prototype (`gen_map.py`), and drift analysis (`drift_by_ref.py`).
- **`evals/v5-hardening/`**:
  - Live AFK evaluation runs, synthesis reports, and validation findings from the StratOS v5.0.0 evolution.
  - Contains overall synthesis reports (`report.md`), finding classifications (`findings.md`), fix plans (`v5-fix-plan.md`), plan challenges (`plan-challenge.md`), and final resume state (`resume-2026-11-04.md`).
- **`simulations/pa6-merge-flow/`**:
  - Discrete-event simulation driver (`run_parta.py`) verifying branch isolation, commit granularity, and merge invariants for finished units.
  - Logs validated state transitions (`moves-ok.txt`) and prohibited illegal moves (`moves-refused.txt`).
- **`probes/v5-kanban-board/`**:
  - Headless DOM probes (`v5board/check_dom.py`, `key_probe.py`, `build_probe.py`), drag-and-drop state verification test fixtures (`v5dnd/`), and HTML5 DnD event handling analysis (`dnd.md`) for the dynamic Kanban board interface.
- **`scripts/`**:
  - Historical backlog matrix analysis and row verification scripts (`b1rows.py`, `b234rows.py`, `g2rows.py`, `g3rows.py`, `g3rrows.py`, `g4rows.py`).
