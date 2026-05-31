# M1889 Executable V2 Support-First Repaired Runner Adapter Preflight

- status: completed
- decision: `support_first_repaired_adapter_preflight_pass_route_to_result_audit`
- summary: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/summary.json`
- reset/rollout in M1889: false
- measured execution: false
- training/replay/PPO: false

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_repaired_runner_adapter \
  --repair-matrix runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv \
  --measured-specs runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json \
  --episode-rows runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv \
  --output-dir runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight \
  --sources-per-role-surface 2 \
  --target-role-surface-count 8 \
  --target-controller-profile-count 12 \
  --target-selected-source-spec-count 16 \
  --target-executable-spec-count 48 \
  --target-rollout-workload-cell-count 576 \
  --target-import-row-count 384 \
  --target-total-panel-row-count 960 \
  --next-blocker m1890-executable-v2-support-first-repaired-runner-adapter-preflight-result-audit
```

## Summary

M1889 ran only the no-rollout repaired adapter preflight over real M1884/M1875/
M1880 artifacts. It did not run environment reset, environment rollout,
measured execution, training, replay, PPO, or ranking.

Result:

```text
result_class: support_first_repaired_runner_adapter_pass
selected_source_spec_count: 16 / 16
role_surface_count: 8 / 8
controller_profile_count: 12 / 12
executable_spec_count: 48 / 48
rollout_workload_cell_count: 576 / 576
import_row_count: 384 / 384
total_panel_row_count: 960 / 960
config_failure_count: 0
missing_import_row_count: 0
duplicate_spec_count: 0
duplicate_workload_count: 0
profile_alias_mismatch_count: 0
guardrail_violation_count: 0
```

Variant counts:

```text
rollout variants:
  finish_extended: 192
  road_relaxed: 192
  road_relaxed_finish_extended: 192

import variants:
  original: 192
  semantics_only: 192
```

Every selected role surface has `120` total repaired panel rows across import
and rollout variants. Every controller profile has `80` total repaired panel
rows.

## Artifacts

```text
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/summary.json
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_selection.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_claim_boundary.csv
```

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Claim Boundary

Supported:

- real-artifact no-rollout repaired adapter preflight passes;
- bounded smoke runner inputs exist for later execution design;
- import and rollout rows are separated and count-complete.

Unsupported:

- repaired measured execution result;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Route to M1890 result audit. Do not run repaired measured execution until the
preflight result is audited and an exact execution protocol is registered.
