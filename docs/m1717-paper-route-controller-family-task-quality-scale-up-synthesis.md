# M1717 Paper-Route Controller-Family Task-Quality Scale-Up Synthesis

- status: completed
- workflow synthesis decision: `pivot`
- decision: `pivot_to_off_track_dominance_localization`
- synthesized range: M1711-M1716
- parent audit: `docs/m1716-paper-route-controller-family-calibrated-scale-up-result-audit.md`

## Evidence Summary

M1711-M1716 completed the source-expanded task-quality scale-up loop:

- M1711 designed a fixed-budget scale-up: `18` base specs, `4` calibrated
  variants, `12` controller-family controls, `864` public diagnostic episodes.
- M1712 materialized the scale-up subset with zero contract violations and no
  rollout.
- M1713 audited the subset as clean.
- M1714 pre-registered the execution protocol and collision/off-track tradeoff
  thresholds.
- M1715 executed exactly `864` episodes with zero failures, finite selected
  metrics, guardrail `0`, and complete scale-up variant/outcome/termination
  aggregates.
- M1716 audited the result as conditional positive: two calibrated variants
  improved off-track rate by at least `0.10` while keeping collision delta
  inside the `0.05` guard, but no variant crossed the full `0.70` off-track
  threshold.

Key M1716 variant evidence:

| variant | off-track | collision | off-track improvement | collision delta |
| --- | ---: | ---: | ---: | ---: |
| `original_axis_baseline` | `0.9306` | `0.0370` | baseline | baseline |
| `best_off_track_variant` | `0.8009` | `0.0370` | `0.1296` | `0.0000` |
| `collision_control_wide_relaxed` | `0.7593` | `0.0833` | `0.1713` | `0.0463` |
| `mid_calibration_variant` | `0.8472` | `0.0509` | `0.0833` | `0.0139` |

## Supported Claims

- The source-expanded execution harness is now working for task-quality
  diagnostics.
- The bounded-smoke calibration signal did not vanish under broader source
  coverage.
- The task axes can reduce off-track dominance without automatically violating
  the collision guard.
- The current task distribution is still too off-track dominated for
  controller-family comparison or paper-level claims.

## Falsified Claims

- The calibrated scale-up is not a full positive result under the `0.70`
  off-track threshold.
- The original-axis task setting is not adequate for paper-route comparison:
  baseline off-track rate is `0.9306`.
- The `mid_calibration_variant` alone is not enough: its off-track improvement
  is only `0.0833`, below the pre-registered `0.10` weak-signal threshold.
- A direct controller-family ranking after M1715 would be premature because the
  task distribution is still dominated by off-track noncompletion.

## Failure Taxonomy Summary

Structural failure taxonomy:

```text
none
```

Research risks:

```text
scenario_sampling_failure_risk: high
metric_artifact_risk: moderate
public_gate_overfit_risk: high
task_quality_off_track_dominance: high
```

The branch did not fail mechanically. It produced a useful conditional-positive
signal, but the active blocker moved from execution plumbing to task-quality
localization: which source families, variants, and profile controls are driving
the remaining off-track dominance?

## Public-Gate Overfit Risk

Risk remains `high`.

Reasons:

- All evidence is public diagnostic evidence.
- The scale-up subset is fixed and has already been used to choose the next
  route.
- Controller-family profile rows are controls, not ranking evidence.
- The task axes were tuned from bounded-smoke behavior and need localization
  before another repair.

This means the next step should not be a broader claim. It should be a
no-rollout localization audit that uses the existing M1715 episode rows to find
where off-track dominance concentrates.

## Next Branch Decision

Decision:

```text
pivot_to_off_track_dominance_localization
```

Next branch:

```text
paper_route_controller_family_task_quality_repair
```

Next milestone:

```text
m1718-paper-route-controller-family-off-track-dominance-localization
```

The next milestone should not train, rollout, tune profiles, compare controller
families, or add actor inputs. It should materialize no-rollout cross-aggregates
from M1715 episode rows:

```text
scale_up_variant_label + source_edge
scale_up_variant_label + task_family
scale_up_variant_label + profile_name
source_edge + task_family
profile_name + outcome_bucket
```

The output should identify repair targets where off-track remains dominant and
collision guard is not the limiting factor. Only after that localization should
the project design a repaired task-quality panel.

## Claim Boundary

Allowed:

```text
scale-up branch synthesis;
conditional-positive public task-quality signal;
route decision toward off-track dominance localization.
```

Forbidden:

```text
controller-family ranking;
finite-window history necessity;
recurrent advantage;
private-holdout evidence;
paper-level evidence;
level3 self-identification.
```

## Decision

M1717 passes as a synthesis milestone. Pivot from the scale-up calibration
branch to no-rollout off-track dominance localization before any task repair,
controller-family comparison, or paper-route claim.
