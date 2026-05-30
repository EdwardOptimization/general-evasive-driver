# M1700 Paper-Route Controller-Family Outcome-Semantics Branch Synthesis

- status: completed
- workflow synthesis decision: `pivot`
- decision: `pivot_to_controller_family_task_quality_calibration_branch`
- synthesized range: M1690-M1699

## Evidence Summary

M1690-M1699 converted the controller-family paper route from metadata to a
measured public rollout pipeline.

What the branch established:

- M1690 materialized `72` executable P0-compatible task specs and an `864`-cell
  workload with zero unmappable specs or contract violations.
- M1691 audited materialization as clean.
- M1692 designed resumable full-rollout execution.
- M1693 executed the full `72 x 12 = 864` public rollout with zero failures,
  finite metrics, and clean guardrails.
- M1694 found raw success uninterpretable because `794/864` rows were terminated
  non-collision non-completions without termination reason.
- M1695 designed logging-only outcome-semantics instrumentation.
- M1696 implemented `termination_reason`, `obstacle_passed_raw`,
  `completion_reason`, `outcome_bucket`, and outcome aggregates without changing
  actor inputs or policy behavior.
- M1697 designed a same-workload instrumented rerun.
- M1698 executed the instrumented rerun with zero failures and clean guardrails.
- M1699 audited the rerun and found the dominant outcome is
  `off_track_noncollision_noncompletion=794`.

## Supported Claims

- The public controller-family workload pipeline is executable end-to-end.
- The M1674 profile checkpoints can be evaluated across all `72` materialized
  specs under the P0/no-wheel/no-oracle actor contract.
- The runner is resumable and writes complete profile/spec/stratum/comparison
  artifacts.
- Outcome-semantics instrumentation works and is logging-only.
- The current workload's dominant blocker is road-boundary/off-track
  termination, not obstacle collision alone.

## Falsified Claims

- Falsified: M1693 raw `success == obstacle_completed && !collision` is
  sufficient for controller-family ranking.
- Falsified: the current M1690/M1693/M1698 workload is immediately suitable as a
  paper-level controller comparison.
- Falsified: recurrent advantage can be inferred from current profile aggregates.
- Falsified: additional rollout execution alone will solve the interpretation
  problem.

## Failure Taxonomy Summary

- `none`: execution and instrumentation gates passed.
- `scenario_sampling_failure` risk: high. The workload is dominated by off-track
  non-completion, so it is not yet isolating evasive obstacle handling.
- `metric_artifact` risk: high if raw success is used without outcome buckets.
- `objective_overfit` risk: moderate. The branch used public generated specs and
  public profile checkpoints repeatedly.

No checkpoint is promoted and no controller-family ranking is admitted.

## Public-Gate Overfit Risk

Risk is high.

Reasons:

- All evidence is public.
- The same profile family and generated task sources have been inspected through
  many process milestones.
- The current workload produces a strong off-track mode that can dominate any
  comparison if not explicitly controlled.
- The task family is still a diagnostic simulation workload, not a private
  paper-quality holdout.

The next branch must treat M1698 as task-quality evidence, not final controller
comparison evidence.

## Next Branch Decision

Pivot from:

```text
paper_route_controller_family_task_source_generation
```

to:

```text
paper_route_controller_family_task_quality_calibration
```

The next branch should answer:

```text
Can we build a calibrated public controller-family evaluation where off-track,
collision, obstacle pass, and max-step noncompletion are separated well enough
to compare history profiles without conflating road-boundary failure with
obstacle-avoidance behavior?
```

Immediate next step:

```text
M1701 paper-route controller-family task-quality calibration design
```

M1701 should design, not execute, a calibration plan that includes:

- outcome-conditional metrics;
- off-track and obstacle-collision separation;
- road-width/corridor or boundary-tolerance variants;
- finish/pass semantics checks;
- source-family/spec filters or stratification;
- unchanged actor input contract;
- no profile-specific tuning;
- no private holdout;
- no controller-family ranking until a later calibrated audit.

## Decision

M1700 pivots to task-quality calibration. The current branch produced useful
infrastructure and a negative/diagnostic result, but it should not continue with
more narrow rollout execution until outcome semantics and task quality are
calibrated.
