# M2236 Paper-Route Current-Sim Matched-Budget Training Branch Synthesis

- status: completed
- synthesis_decision: `pivot`
- decision: `current_sim_matched_budget_training_synthesis_pivot_to_task_curriculum_readiness_diagnosis`
- manifest: `experiments/manifests/m2236-paper-route-current-sim-matched-budget-training-branch-synthesis.json`

## Evidence Summary

This branch tested whether the weak L3/recurrent evidence was mainly a
checkpoint-quality artifact and whether fair matched-budget training would make
the current profile panel comparison-ready.

Completed branch evidence:

- M2226 froze the matched-budget profile training design.
- M2227 materialized short-v0 configs and matrix: `15` configs, `15` rows,
  one budget signature, contract `0`.
- M2230 executed short-v0: `15/15` runs completed, failed `0`, finite metrics
  `true`, contract `0`, quality_floor_profile_pass_count `0`.
- M2231 audited short-v0 as complete but below floor.
- M2232 froze medium-v1: same five profiles, same seeds, same floor,
  `32768` steps per seed.
- M2233 materialized medium-v1: `15` configs, `15` rows, `32768` total steps
  in every row, contract `0`.
- M2234 executed medium-v1: `15/15` runs completed, failed `0`, finite metrics
  `true`, contract `0`, quality_floor_profile_pass_count `0`.
- M2235 audited medium-v1 as repeated below-floor evidence and blocked another
  blind budget escalation.

Route-level comparison:

| item | short-v0 | medium-v1 |
| --- | ---: | ---: |
| total steps per seed | `8192` | `32768` |
| completed runs | `15/15` | `15/15` |
| failed runs | `0` | `0` |
| finite metrics | `true` | `true` |
| contract violations | `0` | `0` |
| quality_floor_profile_pass_count | `0` | `0` |

Medium-v1 improved some aggregate means, but not enough to satisfy the
pre-registered `2/3` seed readiness floor for any profile.

## Supported Claims

Supported:

- The config/training infrastructure can execute fair five-profile,
  three-seed matched-budget panels.
- The current actor input contract stayed clean: no wheel/slip/oracle/hidden
  actor inputs were introduced.
- Short-v0 and medium-v1 both produced complete finite public training artifacts.
- The current panel is not ready for measured execution or controller-family
  comparison under the registered readiness floor.
- Budget increase from `8192` to `32768` steps per seed did not solve the
  route-level readiness blocker.

## Falsified Or Unsupported Claims

Not supported:

- `8192` steps per seed is enough for this panel.
- `32768` steps per seed is enough for this panel.
- M2230 or M2234 can support controller-family ranking.
- M2230 or M2234 can support finite-window-vs-GRU conclusions.
- M2230 or M2234 can support level3 self-identification claims.
- The earlier L3 zero-success issue was only a smoke-checkpoint artifact.

Falsified at the current evidence level:

- Blind budget escalation alone is a sufficient next research strategy.

## Failure Taxonomy Summary

Primary classification:

```text
training_readiness_floor_failure
```

Contributing failure modes:

- `seed_fragility`: every profile has too few seeds passing the floor.
- `training_instability`: longer training did not stabilize enough seeds.
- `metric_artifact` risk: the readiness floor may be diagnosing task/curriculum
  mismatch rather than pure actor architecture weakness.

Not the primary failure:

- implementation failure;
- missing artifacts;
- actor input contract violation;
- non-finite metric failure;
- profile-specific tuning leak.

## Public Gate Overfit Risk

The immediate overfit risk is not that a profile overfit a public gate. The risk
is that the workflow keeps responding to below-floor evidence with more budget
escalation. That would generate local-search churn without changing the
scientific evidence axis.

The safer next move is to diagnose the task/curriculum/readiness floor itself:

- Are failures concentrated by seed/task geometry?
- Are termination rates dominated by offtrack, collision, or non-progress?
- Are eval floors too strict for the current public task mix?
- Is the task distribution still offtrack-dominated in a way that prevents
  meaningful controller-family comparison?
- Do train metrics plateau early, suggesting reward/curriculum rather than
  undertraining?

## Next Branch Decision

Decision:

```text
pivot
```

New branch:

```text
paper_route_current_sim_task_curriculum_readiness_diagnosis
```

Next milestone:

```text
m2237-paper-route-current-sim-task-curriculum-readiness-diagnosis-design
```

M2237 should design an artifact-only diagnosis over M2230/M2234 training
outputs before any new training or measured execution. It should not rank
profiles. It should determine whether the repeated below-floor result is driven
by task/curriculum difficulty, evaluation floor calibration, reward/termination
behavior, or seed/task heterogeneity.

## Blocked

Still blocked:

```text
controller-family ranking
winner selection
measured execution from M2230/M2234 checkpoints
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another blind budget escalation
```
