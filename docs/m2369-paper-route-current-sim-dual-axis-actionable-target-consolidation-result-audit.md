# M2369 Paper-Route Current-Sim Dual-Axis Actionable Target Consolidation Result Audit

- status: completed
- decision: `actionable_target_consolidation_result_accepted_route_to_offtrack_guardrail_repair_design`
- manifest: `experiments/manifests/m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit.json`
- parent doc: `docs/m2368-paper-route-current-sim-dual-axis-actionable-target-consolidation-implementation.md`
- audited summary: `runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json`
- reset/rollout/measured execution in M2369: `false`
- policy action executed in M2369: `false`
- training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID claims: `false`

## Audit Result

M2368 is accepted as a complete artifact-only consolidation pass:

```text
source_slice_row_count: 313
consolidated_row_count: 313
offtrack_repair_target_row_count: 54
collision_guardrail_row_count: 28
r4_mitigation_semantics_row_count: 48
diagnostic_guardrail_row_count: 190
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Consolidated route counts:

```text
offtrack_repair_target: 36
offtrack_repair_target_with_collision_guardrail: 18
collision_guardrail: 10
r4_mitigation_semantics: 48
diagnostic_guardrail: 190
diagnostic_only: 11
```

## Interpretation

The consolidation fixes the main M2365 ambiguity:

```text
diagnostic/profile/pack/global rows are not repair targets;
R4 mitigation semantics rows are not ordinary repair targets;
collision guardrail rows are separate from ordinary offtrack targets;
mixed offtrack/collision rows retain collision_guardrail_required=true.
```

This is enough to route to repair design, but not enough to run training.
M2369 is still an audit of artifacts, not evidence that any repair works.

## Repair Targets

Representative ordinary offtrack targets:

```text
obstacle_longitudinal_timing_bucket=early_far:
  episode_count 1800, offtrack_rate 0.8778, collision_rate 0.0478

sampled_obstacle_label=aes_feasible:
  episode_count 1575, offtrack_rate 0.7956, collision_rate 0.0025

hidden_dynamics_bucket=slow_steer_actuator:
  episode_count 1335, offtrack_rate 0.8097, collision_rate 0.0959

role_family=R0_stable_avoidable:
  episode_count 900, offtrack_rate 0.9344, collision_rate 0.0011
```

Mixed offtrack targets requiring collision guardrails:

```text
obstacle_lateral_offset_bucket=centerline:
  episode_count 2700, offtrack_rate 0.7581, collision_rate 0.1667

sampled_obstacle_label=drift_required:
  episode_count 2025, offtrack_rate 0.7867, collision_rate 0.2015

obstacle_lateral_offset_bucket=left_offset:
  episode_count 1320, offtrack_rate 0.7439, collision_rate 0.1833

role_family=R2_handling_limit_drift_capable_avoidance:
  episode_count 900, offtrack_rate 0.8289, collision_rate 0.1600
```

Collision guardrails:

```text
obstacle_longitudinal_timing_bucket=late_close:
  episode_count 1800, offtrack_rate 0.6144, collision_rate 0.3156

obstacle_longitudinal_timing_bucket=mid:
  episode_count 1800, offtrack_rate 0.6867, collision_rate 0.2356

obstacle_lateral_offset_bucket=right_offset:
  episode_count 1380, offtrack_rate 0.6471, collision_rate 0.2797

hidden_dynamics_bucket=low_mu:
  episode_count 945, offtrack_rate 0.6889, collision_rate 0.2952

hidden_dynamics_bucket=weak_brake:
  episode_count 780, offtrack_rate 0.5615, collision_rate 0.3038
```

R4 remains separate:

```text
role_family=R4_unavoidable_mitigation:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389
```

## Decision

M2369 routes to:

```text
m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design
```

The design should define a bounded repair route that:

```text
1. targets ordinary offtrack repair rows first;
2. treats mixed target rows as offtrack targets with collision guardrails;
3. treats collision-only rows as guardrails, not offtrack objectives;
4. keeps R4 mitigation semantics separate;
5. preserves diagnostic profile/pack/global rows only as no-ranking guardrails;
6. does not run reset/rollout, train, replay, use PPO, rank profiles or packs,
   select a winner, claim scenario redesign executed, or claim repair success.
```

## Claim Boundary

M2369 may claim only:

```text
M2368 consolidation artifacts are complete and clean enough to admit a bounded
offtrack+guardrail repair design.
```

Still blocked:

```text
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Next

Pre-registered follow-up:

```text
m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design
```
