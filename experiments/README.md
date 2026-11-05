# StratosphereOS Development Experiments & Evaluations

This directory preserves experimental test harnesses, evaluations, and analysis scripts developed during the StratosphereOS v5 architecture evolution.

## Contents

- **`evals/bt217-0f-walk-me-through/`**:
  - Benchmark evaluation of the `0f-walk-me-through` lifecycle skill.
  - Contains rubric scoring (`grades.md`), question templates (`questions.md`), prompt briefs (`brief-V0.md` through `brief-V2.md`), and raw evaluation notes.
- **`simulations/pa6-merge-flow/`**:
  - Discrete-event simulation driver (`run_parta.py`) verifying branch isolation, commit granularity, and merge invariants for finished units.
  - Logs validated state transitions (`moves-ok.txt`) and prohibited illegal moves (`moves-refused.txt`).
- **`probes/v5-kanban-board/`**:
  - Headless DOM probes (`v5board/check_dom.py`, `key_probe.py`, `build_probe.py`) and drag-and-drop state verification test fixtures (`v5dnd/`) for the dynamic Kanban board interface.
- **`scripts/`**:
  - Historical backlog matrix analysis and row verification scripts (`b1rows.py`, `b234rows.py`, `g2rows.py`, `g3rows.py`, `g3rrows.py`, `g4rows.py`).
