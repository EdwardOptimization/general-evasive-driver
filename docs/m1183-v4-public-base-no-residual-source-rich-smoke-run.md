# M1183 No-Residual Source-Rich Smoke Run

## Summary

M1183 ran the current-base no-residual source-rich adapter as a bounded
metadata smoke. The run artifact is:

```text
runs/m1183_current_base_no_residual_source_rich_smoke/summary.json
```

Result:

```text
current_base_source_rich_adapter_metadata_ready
```

This is infrastructure evidence only. It is not source-rich mining, proof
conversion, actor training, PPO, promotion, private holdout, driver capability
evidence, recurrent-belief evidence, or paper-level evidence.

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.current_base_source_rich_adapter --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --scenario-config configs/cross_fault_hidden_condition_scenarios.json --run-dir runs/m1183_current_base_no_residual_source_rich_smoke --device cpu --seed-start 118300 --seed-count 1 --max-base-faults 2 --max-fault-specs 2 --max-source-groups 2 --max-snapshots-per-group 1 --max-candidates-per-snapshot 2 --max-steps 80 --min-step 20 --snapshot-stride 10 --warmup-steps 20 --max-continuation-steps 30
```

## Artifact Audit

Summary fields:

```text
result_class: current_base_source_rich_adapter_metadata_ready
residual_head_required: false
required_metadata_pass: true
missing_required_metadata_fields: []
source_groups: 2
source_group_rows: 2
warmup_probe_rows: 2
warmup_artifact_rows: 0
source_result_rows: 2
boundary_search_plan_rows: 4
actor_backbone_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Written files:

```text
summary.json
source_group_rows.csv
warmup_probe_rows.csv
source_result_rows.csv
boundary_search_plan_rows.csv
fault_proxy_limitations.md
progress.jsonl
```

CSV row counts:

```text
source_group_rows.csv: 2 rows
warmup_probe_rows.csv: 2 rows
source_result_rows.csv: 2 rows
boundary_search_plan_rows.csv: 4 rows
```

The `boundary_search_plan_rows.csv` header includes the required source-rich
fields:

```text
policy_label
residual_head_required
preferred_fault_fidelity_class
wrong_fault_fidelity_class
fault_onset_bucket
source_obstacle_body_x
source_obstacle_body_y
source_obstacle_half_width
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
boundary_axis
source_margin
```

## Interpretation

The smoke confirms that the adapter can generate source-rich metadata for the
current public-gate actor without loading a residual head. The output includes
fault fidelity/onset, warmup mode, source and target obstacle geometry, source
outcome fields, and placeholders for later current-frame matching,
action-divergence, and terminal-margin sensitivity stages.

The run remains intentionally small. It should not be interpreted as a
source-rich proof surface because it produced only metadata smoke rows and did
not run wrong-history interventions, proof gates, or paper-level evaluation.

## Decision

```text
current_base_no_residual_source_rich_smoke_pass_route_to_gate_utility_audit_design
```

Given the paper-route plan, the next highest-leverage milestone should be a
gate utility audit design. Source-rich tooling is now smoke-tested enough for
future data generation, but the project should first define how existing gates,
corpora, and row-specific repair logic will be classified before further broad
training or promotion attempts.
