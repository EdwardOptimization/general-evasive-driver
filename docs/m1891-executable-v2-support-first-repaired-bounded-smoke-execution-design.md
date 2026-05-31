# M1891 Executable V2 Support-First Repaired Bounded-Smoke Execution Design

- status: completed
- decision: `support_first_repaired_bounded_smoke_execution_design_admit_wrapper_implementation`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent audit: `docs/m1890-executable-v2-support-first-repaired-runner-adapter-preflight-result-audit.md`
- repaired specs: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json`
- rollout workload: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv`
- import rows: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv`
- no rollout in M1891: true
- policy action executed: false
- training/replay/PPO: false

## Purpose

M1891 designs the repaired bounded-smoke execution route admitted by M1890.
The design is intentionally still pre-execution: it specifies the wrapper,
merge protocol, outputs, pass gates, and claim boundary before any environment
rollout.

## Parent Evidence

M1889/M1890 provide a clean no-rollout repaired smoke payload:

```text
selected source specs: 16
role surfaces: 8
controller profiles: 12
patched executable specs: 48
new rollout workload cells: 576
import/postprocess rows: 384
total repaired-smoke panel rows: 960
config failures: 0
missing import rows: 0
duplicate specs/workloads: 0 / 0
guardrail violations: 0
```

The payload deliberately separates two row classes:

```text
rollout_geometry_variant:
  finish_extended: 192
  road_relaxed: 192
  road_relaxed_finish_extended: 192

import_existing_episode:
  original: 192
  semantics_only: 192
```

Only the three geometry variants should run new environment rollouts. Original
and semantics-only rows must be imported from M1880 episode rows and then
included in the repaired panel for audit.

## Runner Compatibility Decision

The existing support-first measured runner cannot be used directly because it:

- expects JSON key `support_first_measured_executable_specs`;
- does not load `support_first_repaired_measured_executable_specs`;
- only writes one rollout-derived `episode_rows.csv`;
- does not merge imported original/semantics rows;
- does not preserve all repair metadata in aggregate outputs;
- does not distinguish rollout rows from imported rows in the final panel.

However, the one-cell execution helpers and metric/aggregate helpers from the
support-first measured runner are reusable. M1892 should implement a repaired
bounded-smoke wrapper that reuses those helpers where possible but owns the
repaired loaders, import merge, repaired aggregates, and pass gates.

## Required Wrapper

M1892 should implement:

```text
src/autodrift/executable_v2_support_first_repaired_bounded_smoke_execution.py
tests/test_executable_v2_support_first_repaired_bounded_smoke_execution.py
```

The wrapper should load:

```text
--support-first-repaired-measured-specs \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json
--support-first-repaired-workload \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv
--support-first-repaired-import-rows \
  runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv
--source-episode-rows \
  runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv
--m1674-run-dir \
  runs/m1674_controller_family_one_seed_public_pilot
--eval-seed-base 189300
--device cpu
--output-dir runs/m1893_executable_v2_support_first_repaired_bounded_smoke_execution
--no-resume
--next-blocker m1894-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit
```

The implementation milestone must not run this command. A later execution
command-design milestone should register it before rollout.

## Execution Protocol

The wrapper should run only the geometry workload rows:

```text
execution_row_kind == rollout_geometry_variant
target rollout episode count == 576
```

For each rollout row it should:

- index executable specs by repaired `task_source_id`;
- keep `profile_name == controller_profile_name`;
- use the controller config/checkpoint named in the workload row;
- append a row to `rollout_episode_rows.csv`;
- preserve all support-first and repair metadata;
- set `environment_rollout_started`, `measured_rollout_started`, and
  `policy_action_executed` to true for rollout-derived rows;
- keep training/replay/PPO/promoted/private-holdout/profile-tuning/ranking
  guardrails false.

The wrapper should import the original and semantics-only rows after rollout:

```text
execution_row_kind == import_existing_episode
target import episode count == 384
```

For each import row it should:

- join `import_source_episode_workload_id` against M1880 `episode_rows.csv`;
- copy rollout metrics from the matched source episode;
- overwrite metadata with the repaired import-row metadata;
- preserve `base_workload_id`, `import_source_episode_workload_id`,
  `repair_variant_id`, `repair_variant_kind`, `geometry_variant_id`,
  `success_semantics_variant_id`, and `role_semantics_id`;
- set `environment_rollout_started` and `policy_action_executed` false for
  imported rows, or preserve separate row-level source flags so audit can
  distinguish imported data from new rollouts;
- set `semantic_recompute_required` true only for `semantics_only`.

For `semantics_only`, M1892 may initially copy the source metrics and add
diagnostic flags from existing metrics, but it must not create a new rollout.
If role-aware binary outcome recomputation is implemented, it must be a pure
postprocess over existing episode metrics such as collision, margin,
off-track, obstacle-pass time, recovery success, and mitigation proxies.

## Required Episode Metadata

Every output row in the combined repaired panel must preserve at least:

```text
workload_id
repaired_workload_id or repaired_import_row_id
support_first_workload_id
base_workload_id
base_support_first_workload_id
task_source_id
base_task_source_id
support_first_v2_panel_spec_id
base_support_first_v2_panel_spec_id
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
repair_row_id
repair_source_key
repair_variant_id
repair_variant_kind
geometry_variant_id
success_semantics_variant_id
role_semantics_id
config_delta_json or repair_config_delta_json
execution_row_kind
semantic_recompute_required
profile_config_path
checkpoint_path
eval_seed
```

The row must also keep:

```text
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
actor_input_contract_changed == false
profile_specific_tuning == false
```

## Required Output Artifacts

M1893 execution should write:

```text
summary.json
episode_rows.csv
rollout_episode_rows.csv
import_episode_rows.csv
failure_rows.csv
import_failure_rows.csv
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
repair_variant_aggregate.csv
repair_variant_kind_aggregate.csv
geometry_variant_aggregate.csv
success_semantics_variant_aggregate.csv
execution_row_kind_aggregate.csv
controller_profile_repair_variant_aggregate.csv
controller_profile_role_surface_repair_variant_aggregate.csv
role_surface_repair_variant_aggregate.csv
repair_variant_outcome_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
import_rollout_alignment.csv
profile_hidden_dynamics_worst_bucket.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

`episode_rows.csv` is the combined `960`-row repaired panel. The separate
rollout/import episode files keep provenance auditable.

## Required Pass Criteria For Later Execution

A later repaired bounded-smoke execution should pass only if:

```text
rollout_episode_count == 576
import_episode_count == 384
total_panel_row_count == 960
failure_count == 0
import_failure_count == 0
controller_profile_count == 12
selected_source_spec_count == 16
repaired_executable_spec_count == 48
role_panel_count == 4
role_surface_count == 8
repair_variant_count == 5
rollout_variant_count == 3
import_variant_count == 2
profile_alias_mismatch_count == 0
source_episode_join_missing_count == 0
duplicate_panel_row_count == 0
all_selected_metrics_finite == true
metric_completeness_passed == true
metric_completeness_failure_count == 0
guardrail_violation_count == 0
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

The execution pass should prove only that repaired bounded-smoke measurement
plumbing works and produces diagnostic public data for audit. It must not rank
controller families or make paper-level performance claims.

## Resumability

The wrapper must be resumable for the `576` rollout rows:

- append one rollout row per completed repaired `workload_id`;
- skip completed rollout rows on resume;
- persist row-level rollout exceptions in `failure_rows.csv`;
- import rows after each finalization from M1880 source rows;
- write `run_state.json` after every rollout cell;
- support `--no-resume` by clearing rollout, import, combined, failure,
  summary, and aggregate outputs.

Import rows should be deterministic and rebuildable from the import metadata
and source episode rows. They do not need to be appended incrementally during
the rollout loop.

## Post-Execution Audit Scope

The next audit after execution must check:

- exact count targets and all guardrails;
- import-vs-rollout provenance;
- source episode join completeness;
- metric completeness over the combined panel;
- repair-variant and role-surface aggregates;
- whether repaired geometry changes task quality enough to make a later
  controller-family comparison design admissible.

The audit must still keep controller ranking blocked unless the result is both
complete and not dominated by a diffuse task-quality failure.

## Claim Boundary

Supported by M1891:

```text
repaired bounded-smoke execution wrapper/protocol is specified
576 rollout rows and 384 import rows have an explicit merge plan
required outputs and pass gates are defined
wrapper implementation is admissible
```

Not supported by M1891:

```text
repaired measured rollout result
controller-family ranking
policy improvement claim
paper-level benchmark evidence
current-response / finite-window / GRU verdict
level3 self-identification evidence
```

## Decision

M1891 admits wrapper implementation, but workflow cadence requires a branch
synthesis milestone before the implementation milestone. The next step is M1892
branch synthesis; if it continues the branch, the following milestone should
implement the repaired bounded-smoke execution wrapper and focused tests without
running the real `576`-rollout workload.
