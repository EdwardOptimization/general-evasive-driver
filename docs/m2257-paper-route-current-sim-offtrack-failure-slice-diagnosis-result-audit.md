# M2257 Paper-Route Current-Sim Offtrack Failure-Slice Diagnosis Result Audit

- status: completed
- decision: `current_sim_offtrack_failure_slice_audit_route_to_midcourse_corridor_containment_repair_design`
- manifest: `experiments/manifests/m2257-paper-route-current-sim-offtrack-failure-slice-diagnosis-result-audit.json`
- parent result: `runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/summary.json`

## Audit Result

M2256 is a clean no-rerun diagnosis artifact:

```text
result_class: current_sim_offtrack_failure_slice_diagnosis_pass
baseline_episode_count: 480
repaired_episode_count: 480
support_complete: true
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

It only reads existing M2244/M2253 episode rows. No reset, rollout, measured
execution, training, replay, PPO, private holdout, ranking, or promotion was
run.

## Slice Interpretation

Global result:

```text
success_delta: -8
offtrack_delta: +8
collision_delta: 0
mean_return_delta: +14.37612
```

The offtrack regression is localized:

```text
mid_offtrack_delta: +14
late_offtrack_delta: -6
mild_overshoot_delta: +11
severe_overshoot_delta: 0
safe_clearance_offtrack_delta: +7
```

This is not primarily:

```text
collision growth
severe offtrack growth
one profile-seed singleton
negative-clearance obstacle conflict
```

The best interpretation is:

```text
midcourse_mild_boundary_containment_regression
```

The scalar reward repair made returns higher, but allowed more mild road-boundary
departures in the middle of the maneuver while obstacle clearance stayed safe.

## Route Decision

Route to:

```text
m2258-paper-route-current-sim-midcourse-corridor-containment-repair-design
```

This route should design a targeted repair around:

```text
midcourse road-boundary containment
mild overshoot prevention
recovery before offtrack termination
collision/clearance guardrail preservation
no profile-specific tuning
no actor input changes
```

It should not be another scalar return-oriented reward tweak. Any repair must
define how it will be judged by M2256-style slice metrics, not only by eval
return.

## Blocked Routes

Blocked for now:

```text
another blind training run
another generic offtrack penalty increase without slice metric guardrails
collision-only repair as the primary route
profile-seed-specific repair
controller-family ranking
paper-level comparison
finite-window-vs-GRU verdict
level3 self-identification claim
```

## Next

Pre-register:

```text
m2258-paper-route-current-sim-midcourse-corridor-containment-repair-design
```
