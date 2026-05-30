# M1738 Paper-Route Task-Quality Repaired Scenario Taxonomy Execution

- status: completed
- result class: `task_quality_scenario_taxonomy_execution_pass`
- summary: `runs/m1738_repaired_scenario_taxonomy_execution/summary.json`
- parent synthesis: `docs/m1737-paper-route-task-quality-scenario-taxonomy-branch-synthesis.md`
- repaired specs: `runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json`
- repaired matrix: `runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv`

## Execution Result

M1738 executed the fixed M1734 repaired scenario taxonomy matrix as a public
diagnostic rollout. It did not train, replay, run PPO, promote a checkpoint, use
private holdout data, change actor inputs, tune controller-family profiles, rank
profiles, or claim paper-level/level3 self-identification evidence.

| field | observed | required |
| --- | ---: | ---: |
| episodes | `864` | `864` |
| target episodes | `864` | `864` |
| profiles | `12` | `12` |
| scenario specs | `72` | `72` |
| scenario families | `6` | `6` |
| execution failures | `0` | `0` |
| selected metrics finite | `true` | `true` |
| guardrail violations | `0` | `0` |
| unsupported features | `5` | `5` |
| silent unsupported approximations | `0` | `0` |
| unsupported faults treated as covered | `false` | `false` |

The failed M1731 sampling path is repaired at execution time: M1738 completed
all `864` cells and preserved scenario metadata plus sampling repair provenance
for every episode row.

## Required Aggregates

M1738 wrote the required aggregate artifacts:

| aggregate | rows |
| --- | ---: |
| `profile_aggregate.csv` | `12` |
| `scenario_family_aggregate.csv` | `6` |
| `scenario_role_aggregate.csv` | `6` |
| `sampling_repair_variant_aggregate.csv` | `5` |
| `hidden_dynamics_bucket_aggregate.csv` | `9` |
| `road_boundary_bucket_aggregate.csv` | `4` |
| `obstacle_timing_bucket_aggregate.csv` | `5` |
| `obstacle_lateral_bucket_aggregate.csv` | `4` |
| `sampled_obstacle_label_aggregate.csv` | `4` |
| `outcome_aggregate.csv` | `3` |
| `termination_reason_aggregate.csv` | `3` |
| `profile_outcome_aggregate.csv` | `30` |
| `scenario_family_outcome_aggregate.csv` | `18` |
| `scenario_family_sampled_label_aggregate.csv` | `9` |

## Raw Outcome Snapshot

These are diagnostic outcome counts only. They are not controller-family
rankings and are not paper-level evidence until a follow-up audit interprets
the workload quality and claim scope.

```text
success_obstacle_pass: 81
collision_failure: 279
off_track_noncollision_noncompletion: 504
```

Sampled obstacle labels:

```text
aeb_feasible: 144
aes_feasible: 216
drift_required: 316
unavoidable: 188
```

The scenario-family aggregates show the repaired taxonomy is executable but
still dominated by off-track and collision outcomes in several families. This
must be audited before any scenario-quality, controller-family, or paper-route
claim is made.

## Claim Boundary

Supported:

- repaired scenario taxonomy execution plumbing passed;
- all planned cells completed with finite selected metrics;
- repair provenance and sampled-label aggregates are available;
- unsupported fault-like features remain explicitly not covered.

Unsupported:

- controller-family ranking;
- best-profile selection;
- scenario-family task-quality conclusion;
- paper-level benchmark evidence;
- recurrent advantage;
- level3 self-identification.

## Decision

Route to M1739 repaired scenario taxonomy result audit.

M1739 should audit the M1738 outcome distribution and decide whether the
scenario taxonomy branch should proceed to scenario-quality interpretation,
task-quality redesign, or branch synthesis before any controller-family
comparison.
