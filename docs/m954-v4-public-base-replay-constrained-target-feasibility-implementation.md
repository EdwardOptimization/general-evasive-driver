# M954 V4 Public Base Replay-Constrained Target Feasibility Implementation

## Purpose

M954 implements the no-training feasibility audit designed in M953.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_replay_constrained_target_feasibility
```

## Artifacts

```text
runs/m954_v4_public_base_replay_constrained_target_feasibility/summary.json
runs/m954_v4_public_base_replay_constrained_target_feasibility/target_family_summary.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/offline_exact_target_metrics.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/m267_target_preflight.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/m267_target_preflight_rows.csv
runs/m954_v4_public_base_replay_constrained_target_feasibility/row_conflicts.csv
```

## Implementation

M954 adds:

```text
src/autodrift/public_base_replay_constrained_target_feasibility.py
tests/test_public_base_replay_constrained_target_feasibility.py
```

The audit evaluates:

1. existing M951 alpha directions;
2. low-tail projection targets with drift budgets up to `0.008`;
3. accepted-target blend directions;
4. M267/M264 active-row branch-separated first-action target overrides.

The target-space audit reuses the registered exact metrics:

```text
normal_retention_pass
tail_lift_pass
target_tolerance_pass
```

It accepts a joint family only if the same family also passes the active-row
M267/M264 target preflight.

## Result

```text
result_class: replay_constrained_target_feasibility_low_tail_exact_failure
offline_target_family_count: 56
m267_target_preflight_family_count: 56
m267_target_preflight_pass_count: 55
exact_target_candidate_count: 0
joint_feasible_target_count: 0
normal_safe_low_tail_trend_count: 27
row_conflict_count: 55
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
```

The important result is asymmetric:

```text
M267/M264 proof retention is not the current target-space bottleneck.
Low-tail exact feasibility is the bottleneck.
```

The best normal-retained family remains M951 alpha `0.0500`:

```text
normal_retention_pass: true
tail_lift_pass: false
target_tolerance_pass: true
m267_target_preflight_pass: true
gap_deficit_mean: 0.013409
low_tail_fraction: 0.330585
first_action_drift_from_base_mean: 0.002624
```

The smallest one-step projection family that tail-lifts is:

```text
family: projection_gap_scale_0_75_drift_0_0060
normal_retention_pass: false
tail_lift_pass: true
target_tolerance_pass: true
m267_target_preflight_pass: true
gap_deficit_mean: 0.014510
low_tail_fraction: 0.333059
first_action_drift_from_base_mean: 0.002463
```

It fails normal retention because the row-level MSE threshold is crossed even
though mean action drift is still small. This reproduces the same boundary seen
in M951 from a target-space perspective.

## Interpretation

M954 does not prove the project is stuck. It proves the current one-step target
families are underpowered for the registered exact low-tail gate.

Supported:

- branch-separated target overrides can preserve M267/M264 active proof rows;
- the rejected-history side is not the active blocker for target feasibility;
- normal-safe low-tail trend exists in 27 families.

Falsified:

- existing M951 directions contain a joint target candidate;
- first-action low-tail projection targets up to drift budget `0.008` produce
  a joint exact/preflight candidate;
- accepted-target blending alone creates a joint candidate.

## Next Blocker

M954 routes to:

```text
m955-v4-public-base-low-tail-sequence-target-audit-design
```

The next step should design a no-training short-horizon sequence target audit,
with a threshold audit as fallback. The reason is specific: first-action target
movement hits the normal-retention/low-tail boundary, while M267 proof retention
is already preserved.
