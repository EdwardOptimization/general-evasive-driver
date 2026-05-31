# M1988 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Repair Branch Synthesis

- status: completed
- synthesis decision: `continue`
- completed branch segment: `paper_route_task_quality_calibrated_repaired_outcome_support_repair`
- decision: `task_quality_calibrated_outcome_support_repair_branch_synthesis_continue_to_reset_validation_command_design`
- reset/rollout/measured execution in M1988: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M1977-M1987 repaired the main task-quality blocker found after the repaired
calibrated measured execution: the previous 960-row public diagnostic panel was
complete, but not comparison-ready because success support was too sparse and
offtrack/collision outcomes dominated.

Branch progression:

```text
M1977: localized M1975 outcomes without rerun
M1978: audited localization as complete but not comparison-ready
M1979: designed a 192-row no-rollout outcome-support repair wave
M1980: implemented deterministic repair-template generation
M1981: audited repair templates as clean
M1982: designed no-rollout source mining over repaired templates
M1983: implemented source mining and found broad supported cells
M1984: audited source mining and excluded unsupported rows
M1985: designed bounded 80-source materialization from supported rows
M1986: implemented no-reset materialization preflight
M1987: audited materialization as clean and routed to synthesis
```

Starting blocker from M1977/M1978:

```text
episode_count: 960
success_obstacle_pass: 38
collision_failure: 150
off_track_noncollision_noncompletion: 772
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 1
L2_total_success_count: 0
guardrail_violation_count: 0
```

The branch therefore did not continue to controller-family ranking. It repaired
scenario/task support before another measured comparison.

Repair-template evidence:

```text
M1980 result_class: task_quality_calibrated_outcome_support_repair_templates_pass
candidate_count: 192
public_debug/public_gate split: 112/80
holdout_count: 0
labels_enter_actor_input_count: 0
profile_specific_tuning_count: 0
guardrail_violation_count: 0
```

Repair axes:

```text
offtrack_anchor_relief: 64
offtrack_boundary_relief_extension: 32
success_support_expansion: 48
collision_mitigation_relief: 32
mitigation_metric_isolation: 16
```

Source-mining evidence:

```text
M1983 result_class: task_quality_calibrated_outcome_support_source_mining_pass
input_template_count: 192
source_candidate_count: 192
resolution_failure_count: 0
accepted_cell_count_total: 8358
supported_source_count: 184
public_gate_supported_source_count: 73
unsupported_source_count: 8
guardrail_violation_count: 0
```

Supported source counts by repair axis:

```text
offtrack_anchor_relief: 64 / 64
offtrack_boundary_relief_extension: 32 / 32
success_support_expansion: 43 / 48
collision_mitigation_relief: 29 / 32
mitigation_metric_isolation: 16 / 16
```

M1984 classified the 8 unsupported rows and kept them out of materialization:

```text
success_support_expansion label-role mismatch: 5
collision_mitigation_relief label-role mismatch: 1
collision_mitigation_relief friction-timing-filter-only: 2
```

Materialization evidence:

```text
M1986 result_class: task_quality_calibrated_outcome_support_materialization_preflight_pass
selected_source_count: 80
executable_task_spec_count: 80
profile_count: 12
planned_workload_rows: 960
selected_unsupported_source_count: 0
materialization_failure_count: 0
duplicate_task_source_id_count: 0
duplicate_workload_key_count: 0
forbidden_key_violation_count: 0
contract_violation_count: 0
missing_profile_artifact_count: 0
guardrail_violation_count: 0
```

Selected repair-axis quotas:

```text
offtrack_anchor_relief: 24
offtrack_boundary_relief_extension: 16
success_support_expansion: 20
collision_mitigation_relief: 12
mitigation_metric_isolation: 8
```

## Supported Claims

Supported scenario/task-quality claims:

- M1977 reproduced the repaired calibrated measured outcomes exactly and
  localized the active blocker as low outcome support rather than a runner,
  metric-completeness, or actor-contract failure.
- M1979-M1980 produced a deterministic no-rollout outcome-support repair wave
  that targets offtrack-only, collision-dominated, success-support, and
  mitigation-metric blockers without changing actor inputs or controller
  profiles.
- M1983 found broad source support for the repair wave: `184/192` source
  candidates supported and `8358` accepted cells.
- M1984 excluded all unsupported rows instead of forcing them into the panel.
- M1986 materialized a bounded `80 x 12 = 960` workload from supported rows
  with zero materialization, contract, duplicate, missing-profile, unsupported
  source, or guardrail failures.
- M1987 audited that materialization as clean enough to admit reset-validation
  command design.

Supported process claims:

- the branch respected the paper-route hierarchy: task-quality repair before
  controller ranking;
- all repair work before M1988 was public diagnostic and no-rollout except the
  earlier M1975 measured evidence being localized by M1977;
- no private holdout, controller-specific tuning, actor input change, training,
  replay, PPO, promotion, or paper-level claim was used;
- the synthesis cadence correctly stops another narrow repair milestone until
  branch evidence is summarized.

Paper-route axis advanced:

```text
engineering driver performance: no direct change
mechanism evidence for history dependence: no direct change
scenario/task-quality evidence: improved
high-fidelity validation readiness: no direct change
workflow or complexity reduction: improved by synthesis and claim boundary
```

## Falsified Or Unsupported Claims

Falsified by M1977/M1978:

```text
The repaired calibrated measured panel from M1975 is directly
comparison-ready.
```

Reason: only `38/960` rows succeeded, offtrack noncompletion dominated with
`772/960` rows, and the no-rerun localizer found `0` comparison-ready slices.

Falsified for M1980-M1983 repair templates:

```text
Every no-rollout repair template has executable source support.
```

Reason: M1983/M1984 found `8` unsupported rows. The repair remains valid only
because M1985/M1986 materialize from supported rows and exclude unsupported
rows.

Still unsupported:

- reset validity for the newly repaired M1986 executable specs;
- measured rollout success for the newly repaired M1986 workload;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification;
- high-fidelity validation readiness.

## Failure Taxonomy Summary

Observed or active blockers:

```text
outcome_support_low_offtrack_and_collision_dominated:
  found by M1977/M1978; repaired at no-rollout source/materialization level by
  M1979-M1986 but not yet reset-validated or measured.

scenario_sampling_failure / unsupported_source_rows:
  M1983 found 8 unsupported rows; M1984 classified and excluded them.
```

Resolved within this branch:

```text
no_rollout_source_support_gap:
  broad support found for 184/192 candidates with all repair-axis floors passed.

unsupported_row_materialization_risk:
  resolved by materializing only supported rows; selected_unsupported_source_count == 0.
```

Not observed in this branch:

```text
contract_violation
metric_artifact
private_holdout_contamination
training_instability
proof_washout
behavior_regression
controller ranking evidence
level3 self-ID evidence
```

## Public Gate Overfit Risk

Current risk: `medium_high`.

Risk reducers:

- the branch expands source support from the failed M1975/M1977 outcome support
  distribution rather than tuning controller profiles;
- source mining covers five repair axes and materialization selects all five;
- unsupported rows are explicitly excluded instead of coerced;
- the materialized panel keeps `80` sources and `12` fixed controller profiles;
- actor-input and no-oracle guardrails remain clean;
- no ranking or paper claim is made before reset and measured execution.

Remaining risks:

- all evidence remains public diagnostic evidence;
- the new M1986 workload has not yet been reset-validated;
- the new M1986 workload has not yet produced measured outcome rows;
- success/collision/offtrack support may still be inadequate after execution;
- mitigation-metric isolation rows are diagnostic-only and cannot support
  controller ranking by themselves;
- no private holdout or paper-level generalization set is involved.

## Next Branch Decision

Decision:

```text
continue
```

Immediate route:

```text
M1989 reset-validation command design
  -> M1990 reset-validation preflight
  -> result audit
  -> only then measured execution command design
```

Rationale:

- M1986 materialization is clean enough to test reset validity;
- M1988 has satisfied the synthesis cadence and separated supported from
  unsupported claims;
- direct rollout, ranking, paper-level interpretation, and self-ID claims remain
  blocked until reset validation and later measured execution produce evidence.

M1989 should freeze the exact reset-only validation command over:

```text
runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json
```

No reset should be run in M1989.
