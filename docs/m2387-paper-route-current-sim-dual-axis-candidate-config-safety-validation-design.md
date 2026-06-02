# M2387 Paper-Route Current-Sim Dual-Axis Candidate Config Safety Validation Design

- status: completed
- decision: `candidate_config_safety_validation_design_admit_reset_only_validator`
- manifest: `experiments/manifests/m2387-paper-route-current-sim-dual-axis-candidate-config-safety-validation-design.json`
- parent synthesis: `docs/m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis.md`
- source summary: `runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json`
- reset/rollout/measured execution in M2387: `false`
- candidate config loading in M2387: `false`
- active config overwrite in M2387: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2387 designs a bounded safety/reset-validation protocol for the M2385
generated candidate config artifacts. It does not load candidate configs and it
does not run reset validation in M2387.

The next implementation may perform:

```text
static candidate config safety checks
run-dir temporary effective config materialization
reset-only environment validation
```

It must not perform:

```text
policy action execution
rollout or measured execution
repair execution
training/replay/PPO
support-policy or controller-family ranking
winner selection
paper/self-ID/current-sim verdict claims
active config overwrite
```

## Source Inventory

M2388 should read:

```text
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_config_generation_manifest.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_config_rows.csv
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_patch_reference_matrix.csv
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_guardrail_scope_rows.csv
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/active_config_safety_report.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/claim_boundary.csv
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_configs/*.json
```

Expected source counts:

```text
candidate_config_count: 54
candidate_config_rows_count: 54
candidate_patch_reference_matrix_row_count: 54
candidate_guardrail_scope_row_count: 54
reward_patch_count_per_candidate: 3
curriculum_patch_count_per_candidate: 1
guardrail_patch_count_per_candidate: 284
mixed_guarded_candidate_count: 18
candidate_config_files_outside_run_dir_count: 0
```

## Static Safety Checks

Before any environment construction, M2388 must verify:

```text
every candidate_config_path exists;
every candidate_config_path resolves under the M2385 run directory;
every candidate row has inside_run_dir true;
candidate_id matches between row, patch matrix, guardrail row, and JSON;
source_repair_spec_id and repair_family are non-empty;
reward_overlay length is 3 for every candidate;
curriculum_overlay length is 1 for every candidate;
guardrail_overlay.scope_id is global_guardrail_scope;
guardrail_overlay.guardrail_patch_count is 284;
mixed_guarded_requirements.collision_guardrail_required matches the source row;
claim_boundary forbids active config overwrite, environment loading, reset,
repair execution, training, ranking, and winner selection;
active_config_safety_report.active_config_overwritten is false;
claim_boundary.csv still blocks reset/rollout, repair, training, ranking,
paper, finite-window-vs-GRU, level3 self-ID, and current-sim verdict claims.
```

If any static check fails, M2388 must stop before environment loading and write
a failure summary with `environment_reset_attempt_count: 0`.

## Future Reset-Only Scope

M2388 may attempt reset validation only after all static checks pass.

Reset validation must use run-dir temporary effective configs, not the active
scenario config:

```text
effective_config_dir:
  runs/m2388_paper_route_current_sim_dual_axis_candidate_config_reset_validation/effective_configs

candidate_config_source:
  M2385 generated candidate JSON

active_config_overwrite:
  forbidden
```

The reset attempt budget is:

```text
candidate_config_count: 54
reset_attempts_per_candidate: 1
target_reset_attempt_count: 54
```

Reset validation is allowed to instantiate the environment only far enough to
test config load and reset compatibility. It must terminate immediately after
reset and must not step the environment.

Allowed future M2388 output fields:

```text
static_validation_pass_count
static_validation_failure_count
effective_config_written_count
effective_config_outside_run_dir_count
environment_load_attempt_count
environment_reset_attempt_count
environment_reset_success_count
environment_reset_failure_count
sampler_incompatible_candidate_count
schema_incomplete_candidate_count
active_config_overwrite_count
policy_action_executed
environment_step_count
rollout_started
repair_execution_started
training_started
ranking_admissible_count
winner_selected_count
guardrail_violation_count
```

## Failure Taxonomy

M2388 should classify failures as:

```text
static_schema_failure:
  missing required keys, wrong overlay counts, mismatched candidate ids, or
  missing guardrail references.

path_safety_failure:
  candidate or effective config path escapes the run directory.

claim_boundary_failure:
  any candidate artifact claims active overwrite, reset, repair, training,
  ranking, paper result, self-ID, or current-sim verdict.

effective_config_materialization_failure:
  candidate overlay cannot be converted into a temporary effective config
  without active config overwrite.

sampler_incompatible_candidate:
  environment construction or reset rejects the candidate configuration.

forbidden_execution_failure:
  any environment step, policy action, rollout, repair execution, training,
  replay, PPO, ranking, or winner selection occurs.
```

## Pass Gate For Future M2388

M2388 should pass only if:

```text
source candidate_config_count is 54;
static_validation_pass_count is 54;
effective_config_written_count is 54;
effective_config_outside_run_dir_count is 0;
environment_reset_attempt_count is 54;
environment_reset_success_count is 54;
environment_step_count is 0;
active_config_overwrite_count is 0;
policy_action_executed is false;
rollout_started is false;
repair_execution_started is false;
training_started is false;
ranking_admissible_count is 0;
winner_selected_count is 0;
guardrail_violation_count is 0.
```

If the generated candidate config schema is insufficient to materialize
effective configs, M2388 must fail closed and route to schema repair rather
than silently relaxing validation.

## Claim Boundary

M2387 may claim only:

```text
A bounded candidate config safety/reset-validation protocol has been designed.
```

Still blocked:

```text
candidate config loading in M2387
environment reset or rollout in M2387
measured execution
repair execution
training/replay/PPO
support-policy or controller-family ranking
winner selection
scenario redesign executed claim
training repair success claim
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Decision

M2387 routes to:

```text
m2388-paper-route-current-sim-dual-axis-candidate-config-reset-validation-implementation
```

M2388 may implement the static safety and reset-only validation protocol above.
It must fail closed on schema gaps, sampler incompatibility, path safety
violations, active config overwrite, environment steps, policy action
execution, repair execution, training, ranking, or paper/self-ID/current-sim
claims.
