# M2366 Paper-Route Current-Sim Dual-Axis Measured Outcome Localization Result Audit

- status: completed
- decision: `measured_outcome_localization_result_accepted_route_to_actionable_target_consolidation_design`
- manifest: `experiments/manifests/m2366-paper-route-current-sim-dual-axis-measured-outcome-localization-result-audit.json`
- parent doc: `docs/m2365-paper-route-current-sim-dual-axis-measured-outcome-localization-implementation.md`
- audited summary: `runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json`
- reset/rollout/measured execution in M2366: `false`
- policy action executed in M2366: `false`
- training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID claims: `false`

## Audit Result

M2365 is accepted as a complete artifact-only localization pass:

```text
source_episode_count: 5400
slice_row_count: 313
offtrack_target_slice_count: 198
collision_guardrail_slice_count: 95
r4_mitigation_semantics_slice_count: 48
high_priority_offtrack_slice_count: 99
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Route class counts:

```text
offtrack_target: 118
offtrack_target_with_collision_guardrail: 80
collision_guardrail: 15
r4_mitigation_semantics: 48
diagnostic_only: 52
```

## Interpretation

The localization panel is useful, but not directly executable as repair input.
Many rows are overlapping views of the same 5400 episodes.

Diagnostic-only or guardrail-heavy axes:

```text
global
pack_id
profile_name
sampling_repair_class
```

These rows are useful for guardrails and sanity checks, but they must not be
used to rank controller families, support policies, packs, or profiles.

Actionable repair axes:

```text
role_family
scenario_family_id
sampled_obstacle_label
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
hidden_dynamics_bucket
role_family + hidden_dynamics_bucket
role_family + obstacle_longitudinal_timing_bucket
role_family + obstacle_lateral_offset_bucket
```

These axes can define bounded repair targets because they describe task,
geometry/timing, and hidden-dynamics stress, not policy-family ranking.

## Primary Findings

High-priority offtrack targets:

```text
obstacle_longitudinal_timing_bucket=early_far:
  episode_count 1800, offtrack_rate 0.8778, collision_rate 0.0478

role_family=R0_stable_avoidable:
  episode_count 900, offtrack_rate 0.9344, collision_rate 0.0011

scenario_family_id=R0:
  episode_count 900, offtrack_rate 0.9344, collision_rate 0.0011

hidden_dynamics_bucket=nominal_neighbor:
  episode_count 465, offtrack_rate 0.8559, collision_rate 0.1355
```

Offtrack targets requiring collision guardrails:

```text
role_family=R2_handling_limit_drift_capable_avoidance:
  episode_count 900, offtrack_rate 0.8289, collision_rate 0.1600

sampled_obstacle_label=drift_required:
  episode_count 2025, offtrack_rate 0.7867, collision_rate 0.2015

obstacle_lateral_offset_bucket=centerline:
  episode_count 2700, offtrack_rate 0.7581, collision_rate 0.1667

hidden_dynamics_bucket=tire_stiffness_shift:
  episode_count 450, offtrack_rate 0.8067, collision_rate 0.1800
```

Collision guardrail slices that should not become offtrack repair targets:

```text
obstacle_longitudinal_timing_bucket=late_close:
  episode_count 1800, offtrack_rate 0.6144, collision_rate 0.3156

obstacle_longitudinal_timing_bucket=mid:
  episode_count 1800, offtrack_rate 0.6867, collision_rate 0.2356

hidden_dynamics_bucket=low_mu:
  episode_count 945, offtrack_rate 0.6889, collision_rate 0.2952

hidden_dynamics_bucket=weak_brake:
  episode_count 780, offtrack_rate 0.5615, collision_rate 0.3038
```

R4 remains a separate mitigation-semantics route:

```text
role_family=R4_unavoidable_mitigation:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389

scenario_family_id=R4:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389

sampled_obstacle_label=unavoidable:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389
```

## Decision

M2366 accepts M2365 and routes to an actionable target consolidation design:

```text
m2367-paper-route-current-sim-dual-axis-actionable-target-consolidation-design
```

The next design should:

```text
1. keep global/pack/profile rows as diagnostic guardrails only;
2. extract canonical actionable target rows from role/timing/lateral/hidden axes;
3. split ordinary offtrack targets from collision guardrails;
4. preserve R4 mitigation semantics as a separate route;
5. produce a materializer route for consolidated target artifacts;
6. continue blocking ranking, winner selection, paper-level claims,
   finite-window-vs-GRU claims, level3 self-ID claims, scenario-redesign
   executed claims, and training-repair-success claims.
```

## Claim Boundary

M2366 may claim only:

```text
M2365 localization artifacts are complete and can be audited into a bounded
actionable target consolidation design route.
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
m2367-paper-route-current-sim-dual-axis-actionable-target-consolidation-design
```
