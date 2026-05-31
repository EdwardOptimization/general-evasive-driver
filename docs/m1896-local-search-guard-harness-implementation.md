# M1896 Local Search Guard Harness Implementation

## Summary

M1896 implements the workflow improvement requested after the M1895 smoke
execution: prevent the research loop from rolling through many narrow
design/repair/audit/tooling milestones without changing the evidence state.

This milestone does not run reset, rollout, measured execution, replay, PPO,
private holdout, checkpoint promotion, controller ranking, paper-level claims,
or level3 self-identification claims.

## What Changed

- Added Process V6 schema constants in `src/autodrift/research_schema.py`.
- Added `local_search_guard` validation in
  `src/autodrift/research_validate.py`.
- Added focused tests in `tests/test_research_validate.py`.
- Documented Process V6 in `docs/research-process-enforcement.md`.
- Updated the local skill at
  `/home/quyaonan/.agents/skills/autodrift-research-harness/SKILL.md`.
- Reprioritized the queue:
  - M1896 is now the local-search guard implementation.
  - The M1895 result audit moved to M1897.

## Process V6 Rule

Every M1896+ manifest must include:

```text
local_search_guard.actual_progress_type
local_search_guard.process_overhead
local_search_guard.local_search_risk
local_search_guard.same_failure_repeat_count
local_search_guard.same_public_gate_repair_count
local_search_guard.evidence_expansion
local_search_guard.paper_verdict_delta
local_search_guard.must_synthesize_if
```

The validator now rejects:

- missing `local_search_guard` for M1896+ manifests;
- unknown progress type or risk labels;
- negative or non-integer repeat/repair counts;
- high local-search risk without workflow synthesis;
- same-failure repeat count `>= 3` without synthesis;
- same-public-gate repair count `>= 3` without synthesis;
- more than five consecutive non-evidence milestones on one
  `workflow_synthesis.branch`.

Evidence-producing progress types reset the non-evidence streak:

```text
new_closed_loop_data
new_dataset_or_panel
new_scenario_distribution
new_baseline_comparison
```

## Validation

Commands run:

```bash
python -m compileall -q src tests
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_research_validate.py
make research-validate
scripts/hooks/pre-commit
```

Result:

```text
compileall passed
30 passed
research validation passed (enforce_from_priority=870, enforced_tasks=1816, process_v2_from_priority=2220, process_v3_from_priority=6850, process_v4_from_priority=10820, process_v5_from_priority=10850, process_v6_from_priority=18910)
pre-commit lightweight harness tests: 19 passed
```

## Decision

M1896 passes as an infrastructure milestone if `make research-validate` passes
with M1897 as the next pending task. The next research step remains the M1895
result audit, now recorded as M1897.
