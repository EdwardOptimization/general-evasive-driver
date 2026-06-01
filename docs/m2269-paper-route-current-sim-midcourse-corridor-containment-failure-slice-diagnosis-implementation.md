# M2269 Paper-Route Current-Sim Midcourse Corridor-Containment Failure-Slice Diagnosis Implementation

- status: completed
- result: `current_sim_midcourse_corridor_containment_failure_slice_diagnosis_pass`
- manifest: `experiments/manifests/m2269-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-implementation.json`
- run: `runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/summary.json`

## Scope

M2269 implemented and ran the no-rerun slice diagnosis admitted by M2268. It
only reads existing public episode rows:

```text
baseline_m2244: runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv
targeted_m2265: runs/m2265_paper_route_current_sim_midcourse_corridor_containment_selected_checkpoint_outcome_localization/episode_rows.csv
generic_m2253:  runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv
```

No reset, rollout, policy action, training, replay, PPO, private holdout,
ranking, winner selection, paper-level claim, finite-window-vs-GRU conclusion,
or level3 self-identification claim was made.

## Result

The diagnostic support is complete:

```text
baseline_episode_count: 480
targeted_episode_count: 480
reference_episode_count: 480
panel_labels: baseline_m2244, targeted_m2265, generic_m2253
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

Global outcome:

```text
M2244 baseline: success/offtrack/collision = 277/110/93
M2253 generic:  success/offtrack/collision = 269/118/93
M2265 targeted: success/offtrack/collision = 278/110/92
```

Primary deltas:

```text
baseline_vs_targeted:
  success_delta: +1
  offtrack_delta: 0
  collision_delta: -1
  mean_return_delta: +8.979287

generic_vs_targeted:
  success_delta: +9
  offtrack_delta: -8
  collision_delta: -1
```

The M2256 failure slices are repaired relative to the M2244 baseline:

```text
mid_offtrack_delta_vs_base: -8
mild_overshoot_delta_vs_base: -2
safe_clearance_offtrack_delta_vs_base: 0
```

The route is:

```text
aggregate_neutral_slice_recovered_result_audit
```

## Interpretation

M2265 targeted containment is not a strict global offtrack repair versus M2244:
global offtrack remains `110`. It is, however, a meaningful correction of the
generic M2253 regression:

```text
M2253 worsened offtrack from 110 to 118.
M2265 brings offtrack back to 110.
M2253 worsened mid_offtrack by +14.
M2265 improves mid_offtrack by -8 versus M2244.
M2253 worsened mild_overshoot by +11.
M2265 improves mild_overshoot by -2 versus M2244.
```

This supports a result-audit route, not another immediate reward/training local
search. The evidence says targeted containment recovered the intended slice
regression but did not yet create a comparison-ready current-sim driver panel.

## Artifacts

```text
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/summary.json
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/panel_summary.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/global_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/profile_seed_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/outcome_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/offtrack_timing_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/offtrack_severity_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/clearance_risk_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/reference_comparison_delta.csv
runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/failure_slice_routes.csv
```

## Next

Pre-register and run:

```text
m2270-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-result-audit
```

The audit should decide whether this branch should stop/synthesize after slice
recovery, pivot to broader current-sim task quality, or admit a tightly scoped
next diagnostic. It must not turn this into another scalar reward tweak without
new evidence expansion.
