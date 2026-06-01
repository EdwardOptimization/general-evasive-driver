# M2267 Paper-Route Current-Sim Midcourse Corridor-Containment Failure-Slice Diagnosis Design

- status: completed
- decision: `current_sim_midcourse_corridor_containment_failure_slice_diagnosis_design_route_to_branch_synthesis_before_implementation`
- manifest: `experiments/manifests/m2267-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-design.json`
- parent audit: `docs/m2266-paper-route-current-sim-midcourse-corridor-containment-selected-checkpoint-outcome-localization-result-audit.md`

## Design Rationale

M2266 audits M2265 as aggregate-improved but not strict-repair-proven:

```text
M2244 base: success/offtrack/collision/max-step = 277/110/93/0
M2253 generic repair: success/offtrack/collision/max-step = 269/118/93/0
M2265 targeted containment: success/offtrack/collision/max-step = 278/110/92/0
```

M2265 corrects the M2253 aggregate regression, but it does not reduce global
offtrack below M2244. The missing evidence is whether the targeted repair fixed
the original M2256 failure slices:

```text
mid_offtrack_delta
mild_overshoot_delta
safe_clearance_offtrack_delta
profile_seed local regressions
```

The next step must be no-rerun analysis over existing episode rows, not another
training run.

## Input Artifacts

The next implementation should use exactly:

```text
baseline panel:
  runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv

targeted panel:
  runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv

generic-repair reference panel:
  runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv
```

Expected support:

```text
baseline episode rows: 480
targeted episode rows: 480
reference episode rows: 480
profile_seed groups per panel: 15
episodes per profile_seed group: 32
```

No environment reset, rollout, training, replay, PPO, or checkpoint loading is
allowed.

## Required Implementation Shape

The implementation should not reuse the old M2256 panel names blindly because that runner
labels the repaired panel as `repaired_m2253`. The M2268 implementation should
write explicit panel labels:

```text
baseline_m2244
targeted_m2265
generic_m2253
```

It may reuse the M2256 slicing logic, but the output labels must be accurate.

## Slice Axes

The implementation should compute:

```text
primary comparison: baseline_m2244 vs targeted_m2265
reference comparison: baseline_m2244 vs generic_m2253
repair-delta comparison: generic_m2253 vs targeted_m2265
```

For each comparison, include:

```text
global
profile_name
profile_name|seed_id
selected_readiness_floor_pass
outcome_bucket
termination_reason
obstacle_label
offtrack_timing_bucket
offtrack_severity_bucket
clearance_risk_bucket
sideslip_bucket
recovery_bucket
```

Offtrack timing buckets:

```text
no_offtrack
early_offtrack: time_to_first_off_track_s <= 1.20
mid_offtrack: 1.20 < time_to_first_off_track_s <= 1.70
late_offtrack: time_to_first_off_track_s > 1.70
unknown_offtrack_time
```

Offtrack severity buckets:

```text
no_offtrack_overshoot
trace_overshoot: 0 < overshoot <= 0.02
mild_overshoot: 0.02 < overshoot <= 0.05
severe_overshoot: overshoot > 0.05
unknown_overshoot
```

Clearance risk buckets:

```text
collision
negative_clearance_margin
low_clearance_margin: 0 <= margin < 0.25
medium_clearance_margin: 0.25 <= margin < 1.0
safe_clearance_margin: margin >= 1.0
unknown_clearance_margin
```

## Required Outputs

The implementation should write:

```text
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/summary.json
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/panel_summary.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/global_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/profile_seed_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/outcome_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/offtrack_timing_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/offtrack_severity_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/clearance_risk_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/reference_comparison_delta.csv
runs/m2268_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/failure_slice_routes.csv
```

Every output row must remain diagnostic:

```text
diagnostic_only: true
ranking_admissible: false
winner_selected: false
```

## Route Rules

The implementation should classify the route as:

```text
targeted_repair_supported
```

only if:

```text
mid_offtrack_delta vs M2244 <= 0
mild_overshoot_delta vs M2244 <= 0
global_offtrack_count <= 110
collision_count <= 107
max_step_noncompletion_count == 0
and targeted_m2265 improves materially over generic_m2253
```

Route to synthesis or redesign if:

```text
mid_offtrack or mild_overshoot remains worse than M2244
global offtrack remains >= 110 without slice improvement
collision or negative-clearance margin increases materially
no actionable slice explains the remaining gap
```

## Guardrails

M2267, the required branch synthesis, and the later implementation must not:

```text
run environment reset
run environment rollout
execute policy actions
run measured execution
train
run replay
run PPO
use private holdout
promote any checkpoint
rank profiles
select a winner
claim finite-window-vs-GRU
claim level3 self-identification
claim paper-level result
```

## Next

The workflow-synthesis cadence has been reached. Pre-register synthesis before
implementation:

```text
m2268-paper-route-current-sim-midcourse-corridor-containment-repair-branch-synthesis
```
