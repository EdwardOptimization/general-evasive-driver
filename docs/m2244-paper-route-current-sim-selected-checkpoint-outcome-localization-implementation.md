# M2244 Paper-Route Current-Sim Selected-Checkpoint Outcome Localization Implementation

- status: completed
- decision: `current_sim_selected_checkpoint_outcome_localization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2244-paper-route-current-sim-selected-checkpoint-outcome-localization-implementation.json`
- command: `PYTHONPATH=src python -m autodrift.paper_route_current_sim_selected_checkpoint_outcome_localization --output-dir runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization`
- summary: `runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/summary.json`

## Execution Result

M2244 completed the selected-checkpoint outcome localization:

```text
result_class: current_sim_selected_checkpoint_outcome_localization_pass
selected_checkpoint_count: 15
episode_row_count: 480
expected_episode_row_count: 480
profile_seed_group_count: 15
profile_seed_groups_complete: true
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The run evaluated exactly the M2241 selected checkpoints over the same public
seed policy:

```text
episodes_per_selected_checkpoint: 32
episode_seed: seed_id + 10000 + episode_index
```

## Global Outcome

Global outcome over `480` episodes:

| outcome | count | rate |
| --- | ---: | ---: |
| success | `277` | `0.57708` |
| offtrack | `110` | `0.22917` |
| collision | `93` | `0.19375` |
| max-step noncompletion | `0` | `0.0` |

Dominant failure mode:

```text
offtrack_dominated_failure
```

Primary repair route:

```text
offtrack_recovery_reward_and_corridor_repair_design
```

## Profile Outcome

Every profile is labeled `offtrack_dominated_failure` at profile level:

| profile | success rate | collision rate | offtrack rate |
| --- | ---: | ---: | ---: |
| L0_current_masked | `0.59375` | `0.17708` | `0.22917` |
| L1_one_step | `0.57292` | `0.19792` | `0.22917` |
| L2_window_25 | `0.59375` | `0.17708` | `0.22917` |
| L2_window_50 | `0.60417` | `0.18750` | `0.20833` |
| L3_online_gru | `0.52083` | `0.22917` | `0.25000` |

Profile-seed localization shows mixed local patterns:

- Several high-performing seeds are `success_supported`.
- Most weak seeds are `offtrack_dominated_failure`.
- `L1_one_step|222602` is `collision_dominated_failure`.

This supports a repair route that targets offtrack/recovery first while keeping
collision/clearance as a secondary guardrail.

## Interpretation

M2244 changes the next repair target:

```text
The blocker is no longer unknown aggregate readiness failure.
It is primarily offtrack/recovery/corridor failure on selected checkpoints,
with secondary collision risk.
```

The result does not rank profiles. It is diagnostic evidence for task/reward
repair, not a paper comparison.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
measured execution as comparison evidence
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
another checkpoint-selection-only run
another blind budget escalation
```

## Next

Pre-register result audit:

```text
m2245-paper-route-current-sim-selected-checkpoint-outcome-localization-result-audit
```

M2245 should audit the offtrack-dominated result and route to a concrete
offtrack/recovery/corridor repair design if the guardrails hold.
