# B6 Part A, scripted (no model): merge-flow checks on bt221 HEAD 8c1a7ae

Code under test: `C:\Users\patri\Dev\Stratosphere-OS\.claude\worktrees\bt221\src\scripts\{issues,reconcile}.py` run in place (`python <wt>/src/scripts/issues.py --arch .memory/ARCHITECTURE.md ...`, cwd = project). No model, no `gh` (the run logs every argv[0]; assertion A5.6), no GitHub: the only remote is a local bare repo.
Sandbox `C:\t\pa6-1` (project + `pa6.git` bare origin, tracker branch `pa6/issues`, `HOME` and `GIT_CONFIG_GLOBAL` inside the sandbox, `TMP=TEMP=C:\t`). Driver `C:\t\pa6-driver\run_parta.py` (rerunnable: rebuilds the sandbox from scratch), raw outputs `C:\t\pa6-driver\out\`. Product files and shared rig files untouched.

Units (each: epic `in review` + one shipped slice closed at ship with a `Shipped on <branch> @ <full tip sha>` comment + a dependent standalone slice blocked by the shipped slice, as in the earlier live run; every slice had been `claim`ed on its unit branch before ship):
- U1 slugify: human merge commit. U2 word counter: human squash (`feature(<epic>): Word counter (#2)`). U3 title caser: never merged. U4 clamp: merged on the remote only (temp clone, merge commit), branch deleted on the remote, locally and its remote-tracking ref dropped, project not fetched until after the first `merged` runs.
- As in the earlier run, "two slices" = the shipped slice plus its dependent slice; the dependent is the thing that must clear or stay blocked.

## Assertions (PASS/FAIL)
