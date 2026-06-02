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
m2366-paper-route-current-sim-dual-axis-measured-outcome-localization-result-audit
```

Current next task:

```text
m2367-paper-route-current-sim-dual-axis-actionable-target-consolidation-design
```

Current route:

```text
M2366 accepted the M2365 localization panel and routed to actionable target
consolidation. M2367 must separate actionable role/timing/lateral/hidden
targets from global/pack/profile diagnostic guardrails before any repair
materialization, scenario redesign, ranking, or paper-route interpretation.
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

M2367 should design consolidation over M2365 outputs:

```text
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/offtrack_target_slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/collision_guardrail_slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/r4_mitigation_semantics_rows.csv
```

The design should choose a bounded materialization route or stop the branch. It
must not run reset/rollout, train, replay, use PPO, rank profiles or packs,
select a winner, or make paper/self-ID claims.
