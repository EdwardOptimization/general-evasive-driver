# M1709 Paper-Route Controller-Family Bounded Calibration Smoke Result Audit

- status: completed
- decision: `bounded_calibration_smoke_audit_positive_route_to_branch_synthesis`
- audited artifact: `runs/m1708_controller_family_bounded_calibration_smoke_execution/summary.json`
- audited calibration variants: `runs/m1708_controller_family_bounded_calibration_smoke_execution/calibration_variant_aggregate.csv`

## Execution Gate

M1708 passes the execution gate:

| check | value | pass |
| --- | ---: | --- |
| episode count | `864` | yes |
| failure count | `0` | yes |
| all selected metrics finite | `true` | yes |
| guardrail violation count | `0` | yes |
| outcome aggregate rows | `3` | yes |
| termination aggregate rows | `3` | yes |

This is public diagnostic execution evidence only. It is not a controller-family
ranking or self-identification result.

## Task-Quality Thresholds

M1707 pre-registered:

```text
interpretable calibration variant:
  variant episode_count == 72
  off_track_noncollision_noncompletion_rate <= 0.70

weak but useful calibration signal:
  best variant off_track_noncollision_noncompletion_rate <= 0.80
  or best variant improves off-track rate by at least 0.10
     against the original track_width=1.0 finish=original max_steps=1.0 baseline
```

M1708 result:

| item | off-track rate | success rate | collision rate |
| --- | ---: | ---: | ---: |
| original-axis baseline `1.0/original/1.0` | `0.9028` | `0.0417` | `0.0556` |
| best raw variant `2.0/original/1.5` | `0.6944` | `0.2083` | `0.0972` |

Threshold evaluation:

- interpretable variant: pass, because `0.6944 <= 0.70`
- weak signal: pass, because best variant is below `0.80`
- baseline improvement: pass, because `0.9028 - 0.6944 = 0.2083`, above `0.10`

The collision rate increases on the best off-track variant. That tradeoff must
be carried into any scale-up. The branch should not optimize only off-track rate.

## Outcome Interpretation

Overall outcome remains off-track heavy:

```text
success_obstacle_pass: 91 / 864 = 0.1053
collision_failure: 57 / 864 = 0.0660
off_track_noncollision_noncompletion: 716 / 864 = 0.8287
```

But calibration changed the task-quality surface enough to create at least one
interpretable variant. Wider track and longer max steps made obstacle pass and
collision rates less buried by off-track termination.

This means M1701-M1709 did not merely produce more public rows; it found a
calibration route that can reduce the off-track dominance diagnosed in
M1698/M1699.

## Failure Taxonomy

- `none`: M1708 execution and guardrails passed.
- `scenario_sampling_failure` risk: still moderate. Overall outcomes are still
  off-track dominated, and the positive variant comes from a small six-base-spec
  smoke.
- `metric_artifact` risk: moderate. Off-track improvement alone would be
  misleading because collision rate also changes.
- `objective_overfit` risk: high. This is still public evidence over repeatedly
  inspected profile families and generated tasks.

## Required Next Route

The branch is now at the synthesis boundary. M1701-M1709 formed the task-quality
calibration branch after M1700, and the branch has produced a positive smoke plus
clear remaining risks.

The next milestone should be M1710 branch synthesis, not immediate scale-up.
M1710 should decide whether to:

```text
continue with calibrated scale-up;
pivot to collision/off-track tradeoff repair;
stop the branch if the public overfit risk is too high;
or promote to a new paper-route evaluation branch.
```

## Supported Claims

- The bounded calibration smoke executed cleanly.
- The pre-registered task-quality threshold found an interpretable calibration
  variant.
- The best variant improved off-track rate by `0.2083` against the original-axis
  baseline.
- Branch synthesis is required before scale-up.

## Unsupported Claims

- controller-family ranking
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification
- promotion of any checkpoint or controller family

## Decision

M1709 passes as a task-quality result audit. Route to M1710 branch synthesis and
keep training, replay, PPO, promotion, private holdout, actor-input changes,
profile-specific tuning, and controller-family ranking blocked.
