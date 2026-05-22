# M169 Boundary Row67 Stage-Sensitivity Guard

M168 showed a branch-sensitive PPO continuation: the same stage recipe failed
from M166 but passed from M167_5168. The failed branch lost exactly one M164
boundary replay success-drop row: row `67`. M169 makes this kind of fragile row
explicitly testable before any further PPO stage.

This is a positive harness result. It adds a reusable row-level guard and
validates it on the M168 failed and admitted branches.

## Added Guard

Added:

```text
src/autodrift/boundary_fragile_row_guard.py
tests/test_boundary_fragile_row_guard.py
```

The guard reads an existing `boundary_replay_rows.csv` and compares baseline and
candidate policy outcomes by `row_id`.

It rejects a candidate when:

- any baseline success-drop row is lost, unless explicitly allowed;
- any required fragile row, such as row `67`, is missing or no longer a
  success-drop row.

This is stricter than the aggregate M164 count gate because it can detect row
swaps where the total success-drop count stays unchanged but a protected row is
replaced by a different one.

## Focused Test

Run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_boundary_fragile_row_guard.py tests/test_boundary_outcome_replay_gate.py
```

Result:

```text
8 passed
```

The focused tests cover:

- required replay columns;
- rejection when row `67` loses success-drop status;
- acceptance when row `67` is retained;
- rejection of row swaps even when aggregate success-drop count is unchanged.

## Real M168 Branch Checks

Failed M166 branch:

```text
runs/m169_m168_from_m166_fragile_row_guard_seed9510
```

| Metric | Value |
| --- | --- |
| candidate | m168_from_m166 |
| required rows | `[67]` |
| baseline success-drop count | 16 |
| candidate success-drop count | 15 |
| lost success-drop rows | `[67]` |
| changed success-drop rows | `[67]` |
| gate pass | false |

Admitted M167_5168 branch:

```text
runs/m169_m168_from_m167_5168_fragile_row_guard_seed9510
```

| Metric | Value |
| --- | --- |
| candidate | m168_from_m167_5168 |
| required rows | `[67]` |
| baseline success-drop count | 16 |
| candidate success-drop count | 16 |
| lost success-drop rows | `[]` |
| changed success-drop rows | `[]` |
| gate pass | true |

The guard reproduces the M168 branch decision and makes row `67` an explicit
protected condition for future stages.

## Decision

M169 is positive.

What changed:

- row-level fragile boundary replay guard added;
- guard catches the M168 failed branch;
- guard passes the M168 admitted branch;
- row `67` is now an explicit required row for stage-2 continuation.

What remains weak:

- the guard operates on already-replayed M164 rows; it does not replace the full
  M164 replay gate;
- row `67` is only one known fragile row, and more may appear in later stages;
- no-action history remains behavior-neutral;
- this still does not prove self-identification.

Decision: allow M170 stage-2 PPO only if it runs both the row-level fragile
guard and the full M164 boundary replay gate after the stage. The row-level
guard is a precondition, not a substitute for full replay.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m pytest -q tests/test_boundary_fragile_row_guard.py tests/test_boundary_outcome_replay_gate.py
PYTHONPATH=src python -m autodrift.boundary_fragile_row_guard ... m168_from_m166 --required-row-id 67
PYTHONPATH=src python -m autodrift.boundary_fragile_row_guard ... m168_from_m167_5168 --required-row-id 67
```
