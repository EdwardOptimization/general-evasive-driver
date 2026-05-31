# M1877 Executable V2 Support-First Measured Runner Execution Design

- status: completed
- decision: `support_first_measured_runner_execution_design_admit_runner_implementation`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent audit: `docs/m1876-executable-v2-support-first-measured-runner-adapter-result-audit.md`
- measured specs: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json`
- workload matrix: `runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv`
- no rollout in M1877: true
- policy action executed: false
- training/replay/PPO: false

## Purpose

M1877 designs the measured execution route for the clean M1875 support-first
workload. It decides whether an existing runner can be used directly or whether
a support-first measured runner wrapper must be implemented first.

## Parent Evidence

M1875 produced a clean no-rollout workload:

```text
result_class: executable_v2_support_first_measured_runner_adapter_pass
support_first_spec_count: 180
controller_profile_count: 12
workload_cell_count: 2160
role_count: 4
role_surface_count: 8
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
missing_profile_artifact_count: 0
profile_alias_mismatch_count: 0
scenario_as_controller_profile_count: 0
missing_required_field_count: 0
duplicate_key_count: 0
guardrail_violation_count: 0
```

The known support-first imbalance is explicit:

```text
unavoidable_mitigation::post_friction_step: 12
most other role-surfaces: 24
```

## Runner Compatibility Decision

The shared `controller_family_full_rollout_execution.run_workload_cell()` helper
is reusable for one cell because it already:

- builds a P0 human-view/no-wheel/no-oracle env from `env_config`;
- loads controller profile config/checkpoint;
- applies profile observation masks and reset-hidden behavior;
- verifies model observation dimension;
- writes standard rollout metrics and guardrail flags.

However, the generic full-rollout runner must not be used directly because it:

- loads `executable_task_specs`, not `support_first_measured_executable_specs`;
- assumes older task-source fields and target counts;
- does not preserve support-first fields such as `scenario_profile_name`,
  `v2_role_surface_id`, `surface_variant`, and `sampled_obstacle_label`;
- does not write role-surface and scenario-profile aggregates required by this
  branch;
- would make it too easy to interpret a diagnostic run as controller-family
  ranking.

Therefore M1877 admits a support-first measured runner wrapper implementation
before measured rollout.

## Runner Contract To Implement

M1878 should implement:

```text
src/autodrift/executable_v2_support_first_measured_runner_execution.py
tests/test_executable_v2_support_first_measured_runner_execution.py
```

The wrapper should reuse shared helpers where appropriate:

```text
run_workload_cell
_load_profile_cache
append_csv_row
completed_workload_ids
read_csv_rows
write_run_state
selected_metrics_are_finite
aggregate_outcome_rows
profile_hidden_dynamics_worst_rows
```

but it must own support-first loaders, row passthrough, support-first
aggregates, target counts, and claim boundaries.

## Required Inputs

Runner CLI should accept:

```text
--support-first-measured-specs \
  runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json
--support-first-workload \
  runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_workload_matrix.csv
--m1674-run-dir \
  runs/m1674_controller_family_one_seed_public_pilot
--eval-seed-base 187900
--device cpu
--output-dir runs/m1879_executable_v2_support_first_measured_runner_execution
--no-resume
--next-blocker m1880-executable-v2-support-first-measured-runner-result-audit
```

The runner should load the JSON key:

```text
support_first_measured_executable_specs
```

and index specs by `task_source_id`.

## Required Episode Passthrough Fields

Every `episode_rows.csv` row must preserve at least:

```text
workload_id
support_first_workload_id
task_source_id
support_first_v2_panel_spec_id
support_first_materialized_v2_panel_spec_id
source_scenario_spec_id
controller_profile_name
profile_name
scenario_profile_name
scenario_profile_group
role_panel_id
v2_role_surface_id
surface_variant
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label
allowed_labels_metadata_only
strata
eval_seed
profile_config_path
checkpoint_path
```

It must keep:

```text
profile_name == controller_profile_name
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Required Output Artifacts

M1879 measured execution should write:

```text
summary.json
episode_rows.csv
failure_rows.csv
run_state.json
profile_aggregate.csv
controller_profile_aggregate.csv
role_panel_aggregate.csv
role_surface_aggregate.csv
surface_variant_aggregate.csv
scenario_profile_aggregate.csv
hidden_dynamics_bucket_aggregate.csv
road_boundary_bucket_aggregate.csv
obstacle_timing_bucket_aggregate.csv
obstacle_lateral_bucket_aggregate.csv
sampled_obstacle_label_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
controller_profile_role_panel_aggregate.csv
controller_profile_role_surface_aggregate.csv
profile_outcome_aggregate.csv
role_panel_outcome_aggregate.csv
role_surface_outcome_aggregate.csv
profile_hidden_dynamics_worst_bucket.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

## Required Pass Criteria For Later Execution

A later M1879 execution should pass only if:

```text
episode_count == 2160
failure_count == 0
controller_profile_count == 12
support_first_spec_count == 180
role_panel_count == 4
role_surface_count == 8
all_selected_metrics_finite == true
metric_completeness_passed == true
metric_completeness_failure_count == 0
guardrail_violation_count == 0
environment_rollout_started == true
training_started == false
replay_started == false
ppo_used == false
private_holdout_used == false
promoted == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

The execution pass only proves measured rollout plumbing and produces diagnostic
public data for audit. It does not itself rank controller families or establish
paper-level claims.

## Resumability

The measured runner must be resumable:

- append one row per completed `workload_id`;
- skip completed rows on resume;
- write failure rows instead of silently dropping exceptions;
- update `run_state.json` after each workload;
- support `--no-resume` by clearing old output files first.

If runtime is unexpectedly long, the runner can stop with partial artifacts and
later resume; the scope must not be silently reduced.

## Claim Boundary

Supported by M1877:

```text
support-first measured runner wrapper is required
runner contract, artifacts, pass criteria, and resumability are defined
implementation is admissible
```

Not supported by M1877:

```text
measured rollout result
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Guardrails

- environment reset started in M1877: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Decision

Admit M1878 support-first measured runner implementation with focused tests.
Do not run the 2160-episode measured rollout until implementation and execution
design pass.
