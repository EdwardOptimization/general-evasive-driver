# M1841 Executable V2 Reset-Time AES Feasibility Scan Implementation

- status: completed
- decision: `reset_time_aes_feasibility_scan_implementation_pass_route_to_execution_design`
- branch: `paper_route_executable_v2_reset_time_aes_feasibility_scan`
- parent design: `docs/m1840-executable-v2-reset-time-aes-feasibility-scan-design.md`
- project artifact scan run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1840 specified a conditional reset-time AES feasibility scan. M1841 implements
the no-reset helper and focused tests, but does not run the scan on project
artifacts and does not generate a source repair payload.

The helper answers, for a given target row and reset seed:

```text
Given reset-time speed_ref / initial_mu / friction-step timing,
does any deterministic obstacle distance / half-width grid cell satisfy the
same AES-only accept/reject semantics used by reset-time obstacle sampling?
```

## Implementation

Added:

```text
src/autodrift/executable_v2_reset_time_aes_feasibility_scan.py
tests/test_executable_v2_reset_time_aes_feasibility_scan.py
```

The helper:

1. loads repaired executable-v2 specs and reset-stress rows;
2. selects failed `aes_feasible` reset rows only;
3. reproduces reset-time `speed_ref`, `initial_mu`, and `friction_step_at`
   without calling `AutoDriftEnv.reset`;
4. scans a deterministic obstacle grid;
5. applies the same label, AEB-infeasible, threshold, and friction-timing
   filters as reset-time obstacle sampling;
6. writes profile/source summaries, accepted cells, label/reject count tables,
   boundary examples, claim boundary, and summary JSON.

The implementation caches built env/scenario config per profile while scanning
cells. It does not sample random obstacle ranges and does not write a repair
payload.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_reset_time_aes_feasibility_scan.py -q
```

Result:

```text
5 passed in 0.08s
```

Coverage:

- accepted AES cell is detected;
- AEB-only cell is rejected under `require_aeb_infeasible=true`;
- threshold filter can reject an otherwise AES-labeled cell;
- profile and source summaries aggregate mixed support correctly;
- claim boundary blocks repair payload, reset-repaired, and ranking claims.

## Full Test

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1750 passed, 4 warnings in 9.73s
```

## Claim Boundary

Supported:

```text
reset-time AES feasibility scan helper implementation and focused tests
```

Unsupported:

```text
project artifact scan result
source repair payload generated
reset feasibility repaired
measured execution
controller-family ranking
paper-level result
level3 self-identification evidence
```

## Decision

M1841 passes as infrastructure. Route to M1842 to pre-register the exact project
artifact scan command before running M1843.
