# M2299 Paper-Route Current-Sim Scenario Task-Family Offtrack-Primary Collision-Guardrail Result Audit

- status: completed
- decision: `accept_guarded_repair_design_route`
- manifest: `experiments/manifests/m2299-paper-route-current-sim-scenario-task-family-offtrack-primary-collision-guardrail-result-audit.json`
- parent summary: `runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/summary.json`
- repair gate spec: `runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json`
- reset/rollout/policy action in M2299: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2299 accepts M2298 as a valid target/guardrail materialization:

```text
result_class: current_sim_scenario_task_family_offtrack_collision_guardrail_materialization_pass
input_slice_count: 57
dominant_slice_count: 56
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
profile_diagnostic_slice_count: 20
profile_target_slice_count: 0
profile_guardrail_slice_count: 0
repair_gate_spec_exists: true
guardrail_violation_count: 0
```

The materialized route remains:

```text
offtrack_primary_collision_guardrail_failure_slice_result_audit
```

## Target And Guardrail Interpretation

The offtrack target set is broad enough to support a guarded repair design. It
covers role families, obstacle labels, timing buckets, lateral buckets, hidden
dynamics buckets, and the global-equivalent offtrack outcome/termination slices.

The collision guardrail set is also broad enough for repair constraints. It
includes the R4 unavoidable-mitigation role, collision outcome and termination
slices, plus high-collision obstacle/timing/lateral/hidden-dynamics slices.

Profile axes remain diagnostic-only:

```text
profile_target_slice_count: 0
profile_guardrail_slice_count: 0
```

That prevents M2299 from turning the measured panel into profile ranking or
profile-specific tuning.

## Repair Gate Spec Audit

`repair_gate_spec.json` is accepted for the next design step. It defines:

```text
offtrack target:
  reduce_global_offtrack_count: true
  reduce_or_hold_target_slice_offtrack_count: true
  target_slice_count: 20

collision guardrail:
  do_not_increase_global_collision_count: true
  do_not_increase_guardrail_slice_collision_count: true
  guardrail_slice_count: 11

completeness:
  target_episode_count: 1080
  metadata_missing_count: 0
  metric_completeness_failure_count: 0
  guardrail_violation_count: 0
```

M2299 does not evaluate a repaired checkpoint. It only admits a design milestone
that must use these gates as the acceptance boundary for any later repair.

## Blocked Shortcuts

M2299 blocks:

- direct broad PPO or reward repair without an explicit guarded design;
- using `profile_name` or `profile_seed` as target or guardrail axes;
- ranking the measured profile families;
- selecting a winner;
- changing actor inputs or scenario specs to improve the result;
- paper-level, finite-window vs GRU, or level3 self-ID claims.

## Next Route

M2299 accepts the guarded repair route, but the local-search guard blocks
starting another design-only milestone immediately. Pre-register synthesis
first:

```text
m2300-paper-route-current-sim-scenario-task-family-guarded-repair-branch-synthesis
```

M2300 should synthesize M2294-M2299 and decide whether to continue to guarded
repair design, pivot to fresh evidence, or stop for user review. It should not
execute training or rollout. If the synthesis continues, the follow-up design
must freeze:

- the M2298 offtrack targets as improvement objectives;
- the M2298 collision guardrails as non-regression constraints;
- the measured-execution denominator of `1080` episodes;
- target and guardrail pass/fail gates;
- allowed config/reward/curriculum changes for a later implementation;
- blocked ranking, winner, paper-level, finite-window vs GRU, and self-ID claims.

## Claim Boundary

M2299 may claim only that M2298 is accepted as a clean target/guardrail
materialization and that the next route is guarded repair design.

M2299 cannot claim:

- any repair improves behavior;
- controller-family ranking;
- winner selection;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- level3 self-identification.
