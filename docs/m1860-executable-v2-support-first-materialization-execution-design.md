# M1860 Executable V2 Support-First Materialization Execution Design

- status: completed
- decision: `support_first_materialization_execution_design_admit_run`
- branch: `paper_route_executable_v2_support_first_materialization`
- parent helper: `src/autodrift/executable_v2_support_first_materialization.py`
- project materialization execution run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Exact M1861 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_support_first_materialization \
  --support-rows runs/m1856_executable_v2_support_first_source_mining/support_first_materialization_admissibility_input.csv \
  --accepted-cells runs/m1856_executable_v2_support_first_source_mining/support_first_accepted_cells.csv \
  --template configs/executable_v2_support_first_candidate_templates_v0.json \
  --output-dir runs/m1861_executable_v2_support_first_materialization \
  --max-sources-per-role 24 \
  --max-sources-per-role-surface 12 \
  --max-cells-per-source 2 \
  --next-blocker m1862-executable-v2-support-first-materialization-result-audit
```

## Expected Bounds

```text
input_supported_source_count: 202
max_sources_per_role: 24
max_sources_per_role_surface: 12
max_cells_per_source: 2
selected_source_count <= 96
materialized_spec_count <= 192
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
duplicate_key_count: 0
guardrail_violation_count: 0
```

M1861 may produce fewer than 192 rows if selected sources have only one unique
accepted cell after boundary/representative deduplication. That is acceptable if
reported.

## Expected Outputs

```text
runs/m1861_executable_v2_support_first_materialization/summary.json
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_source_selection.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_cell_selection.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialized_executable_v2_panel_specs.json
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_matrix.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_blocked_sources.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_duplicate_keys.csv
runs/m1861_executable_v2_support_first_materialization/support_first_materialization_claim_boundary.csv
```

## Claim Boundary

M1861 may claim bounded materialization artifacts exist. It may not claim reset
feasibility, measured execution, controller ranking, paper-level evidence, or
self-identification.

## Guardrails

- project materialization execution run: `false`
- source mining rerun: `false`
- source repair payload generated: `false`
- environment reset started: `false`
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

## Next Route

M1861 should run the exact command above. M1862 must audit the materialized
artifacts before any reset-validation design.
