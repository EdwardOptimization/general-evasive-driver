# M1726 Paper-Route Controller-Family Task-Quality Repair Branch Synthesis

- status: completed
- workflow synthesis decision: `pivot`
- decision: `pivot_to_task_quality_scenario_taxonomy_design`
- synthesized range: M1718-M1725
- parent audit: `docs/m1725-paper-route-controller-family-off-track-repair-panel-result-audit.md`

## Evidence Summary

M1718-M1725 completed the off-track repair branch:

- M1718 localized remaining off-track dominance from M1715: `48` repair target
  slices under the `off_track>=0.80` and `collision<=0.10` rule.
- M1719 audited the target set as localized enough for a multi-source repair
  panel, while keeping controller-family profile rows as controls.
- M1720 designed a fixed-budget repair panel: `18` base specs, `4` variants,
  all `12` controller-family profiles, and `864` public diagnostic episodes.
- M1721 materialized the panel with zero contract violations, zero missing
  configs/checkpoints, and no rollout.
- M1722 audited the preflight as clean.
- M1723 pre-registered measured execution, required repair-variant aggregates,
  and collision/off-track repair thresholds.
- M1724 executed exactly `864` episodes with zero failures, finite selected
  metrics, guardrail `0`, and complete repair-variant/outcome/termination
  aggregates.
- M1725 audited the result as conditional repair retained, but not a composite
  or full-positive repair.

Key M1725 repair evidence:

| variant | off-track | collision | off-track improvement | collision delta |
| --- | ---: | ---: | ---: | ---: |
| `original_axis_baseline` | `0.9352` | `0.0324` | baseline | baseline |
| `best_off_track_variant` | `0.7361` | `0.1019` | `0.1991` | `0.0694` |
| `collision_control_wide_relaxed` | `0.7824` | `0.0648` | `0.1528` | `0.0324` |
| `wide_relaxed_extended` | `0.7315` | `0.0833` | `0.2037` | `0.0509` |

The composite variant improved off-track versus the prior-control best by only
`0.0046`, below the pre-registered `0.0300` composite margin, and its collision
delta was `0.0509`, just above the `0.05` guard.

## Supported Claims

- The public task-quality execution harness is working for design, preflight,
  execution, and audit loops.
- The repair axes can reduce off-track dominance under at least one
  collision-guarded variant.
- The branch found a real task-quality signal, not a runner artifact.
- The current task distribution is still too off-track dominated for
  controller-family comparison or paper-level claims.

## Falsified Claims

- `wide_relaxed_extended` is not a composite-positive repair under the M1723
  thresholds.
- A second narrow track-width/finish/max-step repair panel is unlikely to be the
  right next step on the same public target set.
- The fixed public repair panel is not ready to support controller-family
  ranking.
- Conditional task-quality repair is not enough to claim recurrent advantage,
  finite-window history necessity, or level3 self-identification.

## Failure Taxonomy Summary

Structural failure taxonomy:

```text
none
```

Research risks:

```text
task_quality_off_track_dominance: high
public_gate_overfit_risk: high
scenario_sampling_failure_risk: high
metric_artifact_risk: moderate
```

The branch did not fail mechanically. It produced clean execution and a
conditional repair signal. The active blocker is now scenario/task-quality
definition: the public task family is dominated by road-boundary failure, so
another local repair risks optimizing the fixed public panel instead of
building a paper-quality evasive-driving benchmark.

## Public-Gate Overfit Risk

Risk remains `high`.

Reasons:

- The repair panel was selected from public M1715/M1718 evidence.
- M1724/M1725 reuse the same public task-quality branch.
- The strongest improvements are still far above the full-positive off-track
  threshold.
- The controller-family profiles are controls, not ranking evidence.
- Continuing small axis repairs would tune against the same public off-track
  surface.

This means the next step should not be a third narrow repair on
`track_width/finish/max_steps`. The project needs a scenario taxonomy that
separates task feasibility, collision avoidance, road-boundary behavior, and
mitigation before controller-family comparison.

## Next Branch Decision

Decision:

```text
pivot_to_task_quality_scenario_taxonomy_design
```

Next branch:

```text
paper_route_task_quality_scenario_taxonomy
```

Next milestone:

```text
m1727-paper-route-task-quality-scenario-taxonomy-design
```

The next milestone should be design-only. It should specify a scenario taxonomy
and no-rollout materialization route for paper-quality task distributions:

```text
ordinary stable avoidance
AEB-infeasible stable AES
drift-required avoidance
unavoidable mitigation
off-track boundary stress
friction / actuator / vehicle-parameter stress
sensor-noise and delay stress
```

It should preserve the human-view/no-privileged actor contract and keep L1,
L2-current-tiled, L2 history-window, L3-online, and L3-reset controls, but it
must not compare controller families until the scenario distribution is less
dominated by a single outcome bucket.

## Claim Boundary

Allowed:

```text
task-quality repair branch synthesis;
conditional repair retained public diagnostic result;
route decision toward scenario taxonomy design.
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

M1726 passes as a synthesis milestone. Pivot from narrow off-track repair to a
scenario-taxonomy design branch before any new repair panel, controller-family
comparison, or paper-route claim.
