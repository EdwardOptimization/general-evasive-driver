# M1847 Executable V2 Task-Source Metadata Redesign Implementation

- status: completed
- decision: `task_source_metadata_redesign_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_task_source_metadata_redesign`
- parent design: `docs/m1846-executable-v2-task-source-metadata-redesign-design.md`
- project artifact execution run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1847 implements the support-first task/source metadata helper designed in
M1846. The helper is metadata-only. It does not run scan/reset/rollout, does
not generate source repair payloads, and does not change actor inputs.

## Implementation

Added:

```text
src/autodrift/executable_v2_task_source_metadata_redesign.py
tests/test_executable_v2_task_source_metadata_redesign.py
```

The helper:

1. aggregates support profile summaries and optional label/reject counts by
   source;
2. evaluates each source against a role contract;
3. blocks stable AES materialization unless accepted `aes_feasible` support is
   present;
4. keeps drift-required evidence separate from stable AES;
5. derives source rows from a profile summary when an execution does not provide
   explicit source rows;
6. writes support contract, role contract, materialization admissibility,
   blocked-source, claim-boundary, and summary artifacts;
7. emits context-aware claim-boundary rows.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_task_source_metadata_redesign.py -q
```

Result:

```text
6 passed in 0.12s
```

Coverage:

- stable AES is blocked when support has zero accepted cells;
- drift-required evidence does not certify stable AES;
- supported stable AES admits materialization and preserves label/ranking
  controls;
- missing support evidence is `unknown` and blocks materialization;
- source rows can be derived from profile summaries;
- claim boundaries are context-aware.

## Full Test

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1756 passed, 4 warnings in 10.68s
```

## Output Contract

The helper writes:

```text
summary.json
task_source_support_contract.csv
task_source_role_contract.csv
task_source_materialization_admissibility.csv
task_source_blocked_sources.csv
task_source_claim_boundary.csv
```

## Decision

M1847 passes as infrastructure. Route to M1848 to pre-register the exact
project-artifact execution command over M1843 support evidence.

## Claim Boundary

Supported:

```text
support-first metadata helper implementation and focused tests
```

Unsupported:

```text
project artifact execution
source repair success
repaired reset feasibility
measured execution
controller-family ranking
paper-level result
level3 self-identification evidence
```
