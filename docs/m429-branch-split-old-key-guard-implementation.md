# M429 Branch-Split Old-Key Guard Implementation

M429 implements the M428 branch-split old-key guard. It does not run PPO,
promote a checkpoint, lower thresholds, or change actor inputs.

## Code Changes

New module:

```text
src/autodrift/branch_split_old_key_guard.py
```

It adds:

- failed old-key row filtering from targeted replay `guard_results.csv`;
- branch classification:
  - normal-branch collision -> `normal`;
  - normal success with positive wrong-history margin -> `wrong_history`;
- reuse of `old_key_replay_failure_trajectory_anchor` to reconstruct branch
  trajectory anchors from the M400 base policy;
- combination of the M426 hard guard and branch-split old-key guard into one
  radius-aware trajectory anchor.

Tests:

```text
tests/test_branch_split_old_key_guard.py
```

## Export

Run directory:

```text
runs/m429_branch_split_old_key_guard
```

Primary anchor:

```text
runs/m429_branch_split_old_key_guard/branch_split_hard_guard_anchor.npz
```

Source metadata:

```text
runs/m429_branch_split_old_key_guard/branch_split_hard_guard_sources.csv
```

Rows:

| Source | Rows |
| --- | ---: |
| M426 base hard guard | `197` |
| branch-split old-key additions | `160` |
| total | `357` |

Branch additions:

| Source | Branch | Rows |
| --- | --- | ---: |
| `10004|perturbed|31|31|9.5|-1.0|0.8` | wrong-history | `37` |
| `10023|perturbed|12|12|11.0|-0.8|1.2` | wrong-history | `41` |
| `9872|perturbed|21|18|12.0|-1.2|1.2` | normal | `41` |
| `9872|perturbed|21|18|12.5|-0.8|1.3` | normal | `41` |

The `10004` normal branch is not added to the hard guard, so the M398 recovery
utility can still move it. Only its rejected-history branch is guarded.

## No-Update Smoke

Run directory:

```text
runs/m429_branch_split_guard_no_update_smoke
```

Result:

| Metric | Value |
| --- | ---: |
| exact lexicographic pass | `true` |
| exact M297 delta vs base | `0.0` |
| exact M270 delta vs base | `+0.0000000596` |
| old-key surrogate delta vs base | `0.0` |
| replay trajectory anchor loss | `0.0` |

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_branch_split_old_key_guard.py tests/test_old_key_replay_failure_trajectory_anchor.py tests/test_exact_post_ppo_repair.py
```

Result:

```text
25 passed
```

## Decision

Admit no-PPO projection probe:

```text
m430-branch-split-nullspace-projection-probe
```

M430 should use `--project-recovery-gradient` with the M429 branch-split hard
guard. It must run exact gates before replay gates and must not promote a
checkpoint directly.
