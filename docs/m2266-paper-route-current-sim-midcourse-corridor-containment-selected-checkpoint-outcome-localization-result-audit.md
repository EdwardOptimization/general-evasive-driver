# M2266 Paper-Route Current-Sim Midcourse Corridor-Containment Selected-Checkpoint Outcome Localization Result Audit

- status: completed
- decision: `current_sim_midcourse_corridor_containment_outcome_audit_route_to_no_rerun_slice_diagnosis_design`
- manifest: `experiments/manifests/m2266-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-result-audit.json`
- parent result: `runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/summary.json`

## Audit Result

M2265 is complete and guardrail clean:

```text
result_class: current_sim_selected_checkpoint_outcome_localization_pass
selected_checkpoint_count: 15
episode_row_count: 480
profile_seed_groups_complete: true
missing_input_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

Global outcome:

```text
M2244 base: success/offtrack/collision/max-step = 277/110/93/0
M2253 generic repair: success/offtrack/collision/max-step = 269/118/93/0
M2265 targeted containment: success/offtrack/collision/max-step = 278/110/92/0
```

M2265 is a real improvement over M2253:

```text
success_delta_vs_M2253: +9
offtrack_delta_vs_M2253: -8
collision_delta_vs_M2253: -1
```

But it does not satisfy the strict M2258 global offtrack target:

```text
global_offtrack_count < 110: false
actual global_offtrack_count: 110
```

Collision and max-step guardrails pass:

```text
collision_count <= 107: true
max_step_noncompletion_count == 0: true
```

## Missing Evidence

The M2258 repair was designed for:

```text
midcourse mild boundary-containment regression
```

M2265's localization runner reports global outcome and aggregate offtrack
statistics, but it does not compute the necessary slice deltas:

```text
mid_offtrack_delta
mild_overshoot_delta
safe_clearance_offtrack_delta
profile_seed local regressions
```

Therefore M2266 cannot claim targeted repair success. It can only say the
targeted repair recovered from the M2253 regression at the aggregate level
without beating the M2244 offtrack count.

## Route Decision

Route to:

```text
m2267-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-design
```

M2267 should design a no-rerun diagnosis comparing:

```text
baseline panel:
  runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv

targeted panel:
  runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv

reference panel:
  runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv
```

The main comparison should be M2244 vs M2265. M2253 should be included as a
reference to show whether targeted containment corrected the generic-repair
regression.

## Blocked Routes

Blocked for now:

```text
claiming repair success from aggregate 278/110/92
another reward/training run before slice diagnosis
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level result
level3 self-identification
private holdout
```

## Next

Pre-register:

```text
m2267-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-design
```
