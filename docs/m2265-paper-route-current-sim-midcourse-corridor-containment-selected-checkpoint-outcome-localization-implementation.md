# M2265 Paper-Route Current-Sim Midcourse Corridor-Containment Selected-Checkpoint Outcome Localization Implementation

- status: completed
- decision: `current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2265-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-implementation.json`
- selected rows: `runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv`
- result artifact: `runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/summary.json`

## Execution Result

M2265 completed the selected-checkpoint outcome localization:

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

No blocked claim was made:

```text
training_started: false
ppo_started: false
replay_started: false
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Global Outcome

M2265 global selected-checkpoint outcome:

```text
success/offtrack/collision/max-step = 278/110/92/0
success_rate: 0.57917
offtrack_rate: 0.22917
collision_rate: 0.19167
mean_return: 58.81669
mean_min_clearance_margin: 1.13464
mean_max_off_track_overshoot: 0.02336
primary_repair_route: offtrack_recovery_reward_and_corridor_repair_design
```

Comparison:

| panel | success | offtrack | collision | max-step |
| --- | ---: | ---: | ---: | ---: |
| M2244 base | `277` | `110` | `93` | `0` |
| M2253 generic repair | `269` | `118` | `93` | `0` |
| M2265 targeted containment | `278` | `110` | `92` | `0` |

Delta vs M2244:

```text
success_delta: +1
offtrack_delta: 0
collision_delta: -1
max_step_delta: 0
```

Delta vs M2253:

```text
success_delta: +9
offtrack_delta: -8
collision_delta: -1
max_step_delta: 0
```

## Interpretation Boundary

M2265 is clearly better than the generic M2253 repair, but it does not satisfy
the strict M2258 global offtrack acceptance criterion:

```text
global_offtrack_count < 110
```

M2265 returns to the M2244 base offtrack count (`110`) rather than improving
below it. Collision and max-step guardrails pass:

```text
collision_count <= 107: true
max_step_noncompletion_count == 0: true
```

The existing localization runner does not compute the M2258 slice metrics:

```text
mid_offtrack_delta
mild_overshoot_delta
safe-clearance offtrack delta
```

Those require a no-rerun failure-slice diagnosis over M2244/M2253/M2265 episode
rows before deciding whether the targeted containment branch succeeded, failed,
or needs synthesis.

## Route Decision

Route to:

```text
m2266-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-result-audit
```

M2266 should audit M2265 and likely decide between:

```text
no-rerun M2244/M2265 failure-slice diagnosis
branch synthesis
task/reward redesign
```

It should not approve another training run based only on the aggregate
`278/110/92` result.

## Blocked Claims

Still blocked:

```text
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
claiming targeted repair success without slice metrics
another blind reward/training iteration
```

## Next

Pre-register:

```text
m2266-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-result-audit
```
