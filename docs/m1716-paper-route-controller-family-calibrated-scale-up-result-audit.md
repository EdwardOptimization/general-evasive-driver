# M1716 Paper-Route Controller-Family Calibrated Scale-Up Result Audit

- status: completed
- decision: `conditional_positive_scale_up_audit_route_to_branch_synthesis`
- audited artifact: `runs/m1715_controller_family_calibrated_scale_up_execution/summary.json`
- audited variant aggregate: `runs/m1715_controller_family_calibrated_scale_up_execution/scale_up_variant_aggregate.csv`

## Audit Result

M1715 is a clean measured source-expanded calibrated scale-up execution with a
conditional positive task-quality signal.

Execution plumbing:

- result class: `controller_family_calibrated_scale_up_execution_pass`
- episode count: `864` / `864`
- failure count: `0`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- scale-up variant aggregate rows: `4`
- outcome aggregate rows: `3`
- termination reason aggregate rows: `3`

This audit did not execute rollout, train, replay, run PPO, promote, use private
holdout, change actor inputs, tune profiles, rank controller families, or claim
paper-level evidence or level3 self-identification.

## Pre-Registered Variant Comparison

Baseline:

```text
variant: original_axis_baseline
off_track_noncollision_noncompletion_rate: 0.9306
collision_failure_rate: 0.0370
```

Calibrated variants:

| variant | off-track | collision | off-track improvement | collision delta | M1714 rule |
| --- | ---: | ---: | ---: | ---: | --- |
| `best_off_track_variant` | `0.8009` | `0.0370` | `0.1296` | `0.0000` | conditional positive |
| `collision_control_wide_relaxed` | `0.7593` | `0.0833` | `0.1713` | `0.0463` | conditional positive |
| `mid_calibration_variant` | `0.8472` | `0.0509` | `0.0833` | `0.0139` | below improvement threshold |

No calibrated variant crossed the full positive interpretability threshold:

```text
off_track_noncollision_noncompletion_rate <= 0.70
and collision_delta <= 0.05
```

Two calibrated variants did satisfy the weaker conditional-positive rule:

```text
offtrack_improvement >= 0.10
and collision_delta <= 0.05
```

The result is therefore not a full positive scale-up and not a repair failure.
It is a conditional positive task-quality signal with remaining off-track
dominance.

## Result Classification

```text
result_class: conditional_positive_scale_up
full_positive_scale_up: false
conditional_positive: true
tradeoff_only: false
repair_required_by_m1714_rules: false
runner_failure: false
```

Why not `positive_scale_up`:

```text
best off-track rate is 0.7593, above the 0.70 threshold.
```

Why not `tradeoff_only`:

```text
best_off_track_variant improves off-track by 0.1296 with zero collision delta;
collision_control_wide_relaxed improves off-track by 0.1713 with collision delta
0.0463, still inside the 0.05 guard.
```

Why not `repair`:

```text
at least one calibrated variant improves off-track by >= 0.10;
not all calibrated variants remain above the 0.80 off-track repair boundary.
```

## Interpretation Boundary

Supported:

- The scale-up execution path is clean.
- The M1708 bounded-smoke task-quality signal did not disappear under broader
  source coverage.
- The calibrated task axes still need improvement because off-track remains
  dominant.
- Branch synthesis is required before another narrow calibration milestone.

Unsupported:

- controller-family ranking
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1716 passes as a process audit. Route to M1717 branch synthesis before further
task-quality repair, broader scale-up, controller-family comparison, or paper
route claims.
