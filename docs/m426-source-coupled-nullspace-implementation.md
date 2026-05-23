# M426 Source-Coupled Nullspace Implementation

M426 implements tooling for the M425 source-coupled recovery/nullspace design.
It does not run PPO, promote a checkpoint, lower thresholds, or change actor
inputs.

## Code Changes

`src/autodrift/exact_post_ppo_repair.py` now has:

- `trajectory_action_anchor_errors`, the per-row trajectory-anchor hinge error;
- `exact_trajectory_action_anchor_loss_by_source`, which reports trajectory
  guard loss separately for each `source_index`;
- `project_flat_gradient_against_hard_constraints`, a deterministic
  PCGrad-like projection helper;
- optional exact-repair config/CLI fields:
  - `project_recovery_gradient`;
  - `recovery_projection_epsilon`;
- an optional optimizer path that replaces the raw recovery gradient with its
  projection against exact and trajectory hard-guard gradients.

Default behavior is unchanged unless `--project-recovery-gradient` is set.

## Hard-Guard Anchor

M426 exports a source-coupled hard-guard anchor by filtering M422 `mixed_b`.
It keeps the rows that M424 identified as binding and excludes recovery/utility
sources:

```text
runs/m426_source_coupled_hard_guard_anchor/hard_guard_anchor.npz
runs/m426_source_coupled_hard_guard_anchor/hard_guard_anchor_sources.csv
```

Rows:

```text
197
```

Included sources:

| Source | Rows | Role |
| --- | ---: | --- |
| M267 row `6` | `40` | hard wrong-history guard |
| M267 row `15` | `34` | hard wrong-history guard |
| old-key `10023` | `41` | hard old-key guard |
| old-key `9951` | `40` | spillover guard |
| old-key `9939` | `42` | spillover guard |

Excluded sources:

```text
old-key 10004
old-key 9998
```

This prevents the hard guard from pinning the M398 recovery rows that the next
probe is supposed to improve.

## No-Update Smoke

Default-disabled no-update smoke:

```text
runs/m426_hard_guard_no_update_smoke
```

Result:

| Metric | Value |
| --- | ---: |
| exact lexicographic pass | `true` |
| exact M297 delta vs base | `0.0` |
| exact M270 delta vs base | `+0.0000000596` |
| old-key surrogate delta vs base | `0.0` |
| replay trajectory anchor loss | `0.0` |
| projected recovery enabled | `false` |

This confirms the new tooling does not disturb the existing exact-repair path
when disabled.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_exact_post_ppo_repair.py tests/test_intervention_objectives.py
```

Result:

```text
32 passed
```

The new tests cover:

- per-source trajectory loss matching weighted row losses;
- conflicting hard-gradient projection;
- non-conflicting gradient preservation;
- multiple simultaneous conflicting hard constraints;
- zero hard-gradient handling.

## Decision

Admit a no-PPO projection probe:

```text
m427-source-coupled-nullspace-projection-probe
```

M427 should use `--project-recovery-gradient` and the M426 hard-guard anchor.
It must run exact gates before replay gates and must not promote a checkpoint
directly.
