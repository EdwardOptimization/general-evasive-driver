# M1710 Paper-Route Controller-Family Task-Quality Calibration Branch Synthesis

- status: completed
- workflow synthesis decision: `continue`
- decision: `continue_to_source_expanded_calibrated_scale_up_design`
- synthesized range: M1701-M1709

## Evidence Summary

M1701-M1709 converted the off-track-dominated controller-family workload into a
bounded task-quality calibration pipeline.

What the branch established:

- M1701 designed the task-quality calibration axes:
  `track_width_scale`, `finish_variant`, and `max_steps_scale`.
- M1702 materialized the full no-rollout calibration matrix:
  `72` base specs, `864` calibration specs, `12` profiles, and `10368` cells,
  with zero P0 contract violations.
- M1703 audited that matrix as clean metadata and blocked direct full execution.
- M1704 designed a bounded `864`-cell smoke:
  `6` selected base specs, all `12` calibration variants, and all `12` profiles.
- M1705 materialized the bounded subset with `3` T4 and `3` T5 base specs, zero
  contract violations, and no rollout.
- M1706 audited the bounded subset as clean.
- M1707 designed measured execution and pre-registered task-quality thresholds.
- M1708 executed `864` public diagnostic episodes with zero failures, finite
  metrics, and zero guardrail violations.
- M1709 audited the result as positive task-quality evidence:
  the best variant reduced off-track rate from `0.9028` to `0.6944`, a `0.2083`
  improvement, crossing the pre-registered `<= 0.70` interpretability threshold.

## Supported Claims

- The task-quality calibration infrastructure works end to end.
- The bounded public calibration smoke is executable and produces outcome,
  termination, profile, source, and calibration-variant aggregates.
- The strict original-axis workload is too off-track dominated for direct
  controller-family ranking.
- At least one calibrated public variant makes obstacle pass and collision
  outcomes more interpretable.
- A source-expanded calibrated scale-up is justified before returning to
  controller-family comparison.

## Falsified Claims

- Falsified: direct full-matrix execution was the right next step after M1702.
- Falsified: the original strict task axis is enough for paper-route
  controller-family comparison.
- Falsified: off-track rate alone is a sufficient optimization target. The best
  off-track variant also increased collision rate from `0.0556` to `0.0972`.
- Falsified: the branch can jump directly from bounded smoke to ranking
  recurrent profiles.

## Failure Taxonomy Summary

- `none`: M1702/M1705 preflights and M1708 execution passed structurally.
- `scenario_sampling_failure` risk: moderate. M1708 is still a six-base-spec
  public smoke, even though it includes T4/T5 and source-diverse rows.
- `metric_artifact` risk: moderate. Off-track improvement can hide collision
  tradeoffs if audited alone.
- `objective_overfit` risk: high. The same public profile family and generated
  task source pool have been inspected repeatedly.

No checkpoint is promoted and no controller-family ranking is admitted.

## Public-Gate Overfit Risk

Risk is high.

Reasons:

- All calibration evidence is public.
- The M1674 controller-family profiles are repeatedly reused.
- The positive variant was selected after a bounded public smoke and needs
  source-expanded confirmation.
- The task remains diagnostic simulation evidence rather than private
  paper-quality holdout evidence.

The next branch step must therefore preserve baseline and collision-control
variants, not just rerun the best off-track variant.

## Next Branch Decision

Continue the current branch:

```text
paper_route_controller_family_task_quality_calibration
```

Immediate next step:

```text
M1711 paper-route controller-family calibrated scale-up design
```

M1711 should design, not execute, a source-expanded fixed-budget scale-up:

```text
selected base specs: 18
task split: T4=9, T5=9
calibration variants per base spec: 4
profiles: 12
planned episodes: 18 * 4 * 12 = 864
```

The four calibration variants should include:

```text
original baseline: track_width=1.0, finish=original, max_steps=1.0
best off-track variant: track_width=2.0, finish=original, max_steps=1.5
collision-control wide variant: track_width=2.0, finish=relaxed, max_steps=1.0
mid calibration variant: track_width=1.5, finish=relaxed, max_steps=1.5
```

The scale-up should expand sources without increasing execution budget. It must
remain task-quality diagnostic evidence and keep controller-family ranking
blocked until a later audit confirms outcome modes are stable across broader
sources.

## Decision

M1710 continues the task-quality calibration branch and admits M1711 source-
expanded calibrated scale-up design. Keep rollout execution, training, replay,
PPO, promotion, private holdout, actor-input changes, profile tuning,
controller-family ranking, paper-level claims, and level3 self-ID claims blocked
until a later manifest explicitly admits them.
