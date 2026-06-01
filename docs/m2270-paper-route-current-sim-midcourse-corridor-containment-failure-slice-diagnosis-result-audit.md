# M2270 Paper-Route Current-Sim Midcourse Corridor-Containment Failure-Slice Diagnosis Result Audit

- status: completed
- decision: `current_sim_midcourse_corridor_containment_slice_audit_route_to_task_quality_synthesis`
- manifest: `experiments/manifests/m2270-paper-route-current-sim-midcourse-corridor-containment-failure-slice-diagnosis-result-audit.json`
- parent result: `runs/m2269_paper_route_current_sim_midcourse_corridor_containment_failure_slice_diagnosis/summary.json`

## Audit Result

M2269 is complete and guardrail clean:

```text
result_class: current_sim_midcourse_corridor_containment_failure_slice_diagnosis_pass
baseline_episode_count: 480
targeted_episode_count: 480
reference_episode_count: 480
support_complete: true
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

Panel labels are correct:

```text
baseline_m2244
targeted_m2265
generic_m2253
```

No reset, rollout, measured execution, training, replay, PPO, private holdout,
ranking, winner selection, paper-level result, finite-window-vs-GRU conclusion,
or level3 self-identification claim was made.

## Evidence

Global outcome:

```text
M2244 baseline: success/offtrack/collision = 277/110/93
M2253 generic:  success/offtrack/collision = 269/118/93
M2265 targeted: success/offtrack/collision = 278/110/92
```

M2265 targeted containment is better than M2253 generic repair:

```text
success_delta_vs_M2253: +9
offtrack_delta_vs_M2253: -8
collision_delta_vs_M2253: -1
```

M2265 targeted containment is aggregate-neutral versus M2244 on the main
offtrack count:

```text
success_delta_vs_M2244: +1
offtrack_delta_vs_M2244: 0
collision_delta_vs_M2244: -1
```

The intended M2256/M2257 slices are recovered versus M2244:

```text
mid_offtrack_delta_vs_M2244: -8
mild_overshoot_delta_vs_M2244: -2
safe_clearance_offtrack_delta_vs_M2244: 0
```

## Interpretation

The targeted containment branch did what it was designed to do at slice level:
it corrected the generic-repair midcourse/mild boundary regression without
increasing collision. However, it did not produce a strict global offtrack
improvement below the M2244 baseline, and all profile readiness floors remain
unproven from the broader current-sim route.

Therefore M2270 accepts this as:

```text
slice_recovery_supported
aggregate_strict_repair_not_proven
comparison_ready_current_sim_panel_not_proven
```

This should stop the local scalar reward-repair loop. A third immediate
road-margin/offtrack reward tweak would be local search without changing the
paper evidence axis.

## Route Decision

Route to:

```text
m2271-paper-route-current-sim-task-quality-branch-synthesis-design
```

M2271 should synthesize the current-sim task-quality branch and decide whether
the next useful move is broader scenario/task-quality repair, fresh task
distribution construction, or a controlled comparison redesign. It should not
start from another reward scalar tweak.

## Blocked Routes

Blocked for now:

```text
claiming targeted containment as a strict global repair
another reward/training local-search step before synthesis
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
m2271-paper-route-current-sim-task-quality-branch-synthesis-design
```
