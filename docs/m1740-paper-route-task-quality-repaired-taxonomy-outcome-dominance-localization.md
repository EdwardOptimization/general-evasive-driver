# M1740 Paper-Route Task-Quality Repaired Taxonomy Outcome Dominance Localization

- status: completed
- result class: `task_quality_outcome_dominance_localization_pass`
- summary: `runs/m1740_repaired_taxonomy_outcome_dominance_localization/summary.json`
- parent audit: `docs/m1739-paper-route-task-quality-repaired-scenario-taxonomy-result-audit.md`

## Summary

M1740 materializes a no-rollout localization of the M1738 repaired scenario
taxonomy outcomes. It only reads existing M1738 episode rows and does not run
environment rollout, train, replay, run PPO, promote a checkpoint, use private
holdout data, change actor inputs, tune profiles, rank controller families, or
make paper-level/level3 self-identification claims.

The result is a pass for localization plumbing, but it classifies the outcome
problem as diffuse:

```text
outcome_dominance_class: diffuse_outcome_dominance
dominant_slice_count: 143
dominant_family_count: 6
dominant_profile_count: 12
```

This means the M1738 non-success mass is not localized to one narrow scenario
family or one profile. The next step should audit this result before deciding
between task-quality redesign, a bounded evaluation panel, branch synthesis, or
stop.

## Pass/Fail

| field | observed | required |
| --- | ---: | ---: |
| episodes | `864` | `864` |
| selected metrics finite | `true` | `true` |
| dominant slices | `143` | `>0` |
| dominant families | `6` | diagnostic |
| dominant profiles | `12` | diagnostic |
| guardrail violations | `0` | `0` |

Aggregate row counts:

| artifact | rows |
| --- | ---: |
| `scenario_family_aggregate.csv` | `6` |
| `scenario_family_label_aggregate.csv` | `9` |
| `scenario_family_profile_aggregate.csv` | `72` |
| `scenario_family_road_bucket_aggregate.csv` | `13` |
| `scenario_family_hidden_bucket_aggregate.csv` | `18` |
| `scenario_family_timing_bucket_aggregate.csv` | `16` |
| `sampling_repair_variant_aggregate.csv` | `5` |
| `profile_aggregate.csv` | `12` |
| `profile_outcome_aggregate.csv` | `30` |
| `scenario_family_outcome_aggregate.csv` | `18` |

The top dominant slice is:

```text
slice_type: scenario_family_profile
slice_id: aeb_infeasible_stable_aes::L2_window_100_current_tiled
dominant_outcome: off_track_noncollision_noncompletion
dominant_outcome_rate: 1.0
non_success_rate: 1.0
episode_count: 12
```

This top row is diagnostic only. It is not a controller-family ranking claim.

## Interpretation Boundary

Supported:

- M1738 outcome dominance is now localized into durable aggregate and dominant
  slice artifacts.
- Dominance is diffuse across all `6` scenario families and all `12` profiles.
- The branch should not proceed directly to profile ranking or paper-level
  claims.

Unsupported:

- controller-family ranking;
- best-profile selection;
- paper-level benchmark evidence;
- level3 self-identification;
- conclusion that any one profile caused the task-quality issue.

## Decision

Route to M1741 outcome dominance result audit.

M1741 should audit whether diffuse dominance means the branch should pivot to
task-quality redesign, create a bounded paper-quality evaluation panel, perform
branch synthesis, or stop the scenario taxonomy route.
