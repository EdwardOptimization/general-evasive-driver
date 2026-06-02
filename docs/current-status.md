# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Current Research Blocker

Latest completed milestone:

```text
m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design
```

Current next task:

```text
m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis
```

Current route:

```text
M2373 designed a bounded artifact-only repair implementation route, but routed
to outcome-localization branch synthesis before another narrow materializer.
M2374 must synthesize M2364-M2373 and choose the next bounded route before any
repair execution, scenario redesign, ranking, training, or paper-route
interpretation.
```

## Latest Evidence

M2362 produced the complete measured panel over the repaired five-pack family:

```text
episode_count: 5400
config_pack_count: 5
scenario_specs_per_pack_count: 72
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
global success_rate: 0.06518518518518518
global offtrack_rate: 0.7262962962962963
global collision_rate: 0.19962962962962963
dominant_failure_mode: offtrack_dominated_failure
```

M2363 audited M2362 and blocked raw ranking or paper interpretation:

```text
primary offtrack target roles: R0, R2, R3, R5
separate mitigation semantics role: R4_unavoidable_mitigation
profile aggregates: diagnostic only
pack aggregates: diagnostic only
winner selected: false
finite-window vs GRU conclusion: false
level3 self-ID claim: false
```

M2364 designed artifact-only localization. M2365 implemented and ran it:

```text
result_class: current_sim_dual_axis_measured_outcome_localization_pass
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

M2365 route classes:

```text
offtrack_target: 118
offtrack_target_with_collision_guardrail: 80
collision_guardrail: 15
r4_mitigation_semantics: 48
diagnostic_only: 52
```

M2366 audit decision:

```text
M2365 localization accepted: true
next route: actionable target consolidation design
diagnostic-only/guardrail-heavy axes: global, pack_id, profile_name, sampling_repair_class
actionable axes: role_family, scenario_family_id, sampled_obstacle_label,
  timing bucket, lateral bucket, hidden dynamics bucket, and role-conditioned
  timing/lateral/hidden axes
R4 mitigation semantics: separate route, not ordinary offtrack repair
```

M2367 design decision:

```text
diagnostic-only axes: global, pack_id, profile_name, sampling_repair_class,
  pack/profile composites
actionable axes: role_family, scenario_family_id, sampled_obstacle_label,
  hidden dynamics, timing, lateral, and role-conditioned hidden/timing/lateral
ordinary repair target excludes: diagnostic axes and R4 semantics rows
M2368 command: artifact-only consolidation, no reset/rollout/training/ranking
```

M2368 result:

```text
source_slice_row_count: 313
consolidated_row_count: 313
offtrack_repair_target_row_count: 54
collision_guardrail_row_count: 28
r4_mitigation_semantics_row_count: 48
diagnostic_guardrail_row_count: 190
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
guardrail_violation_count: 0
```

M2369 audit decision:

```text
M2368 consolidation accepted: true
next route: bounded offtrack guardrail repair design
ordinary offtrack repair targets: 54
collision guardrail rows: 28
R4 mitigation semantics rows: 48
diagnostic guardrail rows: 190
direct training/repair-success claim: blocked
```

M2370 design decision:

```text
repair families: priority offtrack, ordinary offtrack, guarded offtrack,
  collision guardrail, R4 mitigation semantics guardrail, diagnostic guardrail
allowed repair levers are names only; none are executed in M2370/M2371
blocked: actor input change, oracle features, profile-specific tuning,
  winner selection, R4 ordinary repair, collision-blind offtrack objective,
  scenario-redesign-executed claim, training-repair-success claim
```

M2371 result:

```text
repair_spec_row_count: 320
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
collision_guardrail_constraint: 28
r4_mitigation_semantics_guardrail: 48
diagnostic_no_ranking_guardrail: 190
profile_or_pack_repair_spec_count: 0
r4_ordinary_repair_spec_count: 0
collision_blind_mixed_repair_spec_count: 0
guardrail_violation_count: 0
```

M2372 audit decision:

```text
M2371 repair specs accepted: true
next route: bounded offtrack guardrail repair implementation design
ordinary offtrack specs: 36
mixed guarded offtrack specs: 18
collision guardrail specs: 28
R4 mitigation semantics guardrail specs: 48
diagnostic no-ranking guardrail specs: 190
profile/pack ordinary repair specs: 0
R4 ordinary repair specs: 0
collision-blind mixed repair specs: 0
repair execution/training/replay/PPO: false
```

M2373 implementation design decision:

```text
implementation route: artifact-only repair plan materialization
future outputs: repair plan, reward deltas, curriculum weights, guardrail constraints
ordinary offtrack direct repair specs: 36
mixed guarded specs requiring collision constraints: 18
guardrail-only specs: 28 collision, 48 R4, 190 diagnostic
active config overwrite: blocked
actor input change/oracle feature/profile-specific tuning: blocked
repair execution/training/replay/PPO: false
next route: outcome-localization branch synthesis
```

## Current Interpretation Boundary

Allowed claim:

```text
M2362 measured outcomes have been localized into diagnostic target and
guardrail slices.
```

Blocked claims:

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

## Immediate Next Step

M2374 should synthesize the M2364-M2373 outcome-localization repair route:

```text
docs/m2364-paper-route-current-sim-dual-axis-measured-outcome-localization-design.md
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json
runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json
runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json
docs/m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design.md
```

The synthesis should decide whether to continue to repair-plan materialization,
pivot, stop, or promote to a new branch. It must not run reset/rollout, execute
repair, train, replay, use PPO, rank profiles or packs, select a winner, claim
scenario redesign executed, claim repair success, or make paper/self-ID claims.
