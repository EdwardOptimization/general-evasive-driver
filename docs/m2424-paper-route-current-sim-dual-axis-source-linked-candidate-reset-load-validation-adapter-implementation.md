# M2424 Paper-Route Current-Sim Dual-Axis Source-Linked Candidate Reset/Load Validation Adapter Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter_pass`
- manifest: `experiments/manifests/m2424-paper-route-current-sim-dual-axis-source-linked-candidate-reset-load-validation-adapter-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter.py`
- output: `runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter/summary.json`
- measured rollout/environment reset/environment step: `false`
- repair execution/training/replay/PPO: `false`
- active config overwrite: `false`
- source-linked family/profile/candidate/controller ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m autodrift.paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter \
  --source-dir runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization \
  --output-dir runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter \
  --next-blocker m2425-paper-route-current-sim-dual-axis-source-linked-repair-plan-materialization-branch-synthesis
```

## Result

Summary:

```text
result_class: current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter_pass
candidate_count: 4
target_candidate_count: 4
overlay_load_pass_count: 4
overlay_schema_failure_count: 0
table_payload_mismatch_count: 0
source_row_key_count_mismatch_count: 0
candidate_overlay_outside_run_dir_count: 0
guardrail_metadata_row_count: 24
guardrail_metadata_failure_count: 0
diagnostic_family_metadata_failure_count: 0
claim_boundary_failure_count: 0
missing_collision_guardrail_count: 0
missing_r4_guardrail_count: 0
missing_max_step_guardrail_count: 0
missing_speed_too_low_guardrail_count: 0
missing_diagnostic_guardrail_count: 0
missing_family_diagnostic_guardrail_count: 0
active_config_overwrite_count: 0
repair_execution_allowed_count: 0
training_allowed_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
actor_input_contract_change_count: 0
hidden_oracle_feature_injection_count: 0
guardrail_violation_count: 0
```

Candidate families:

```text
source_linked_geometry_timing_containment: 1
source_linked_hidden_dynamics_response_containment: 1
source_linked_role_conditioned_containment: 1
source_linked_outcome_failure_surface_containment: 1
```

Guardrail types:

```text
collision_non_regression: 4
r4_mitigation_semantics: 4
max_step_noncompletion: 4
speed_too_low: 4
diagnostic_monitoring: 4
source_linked_family_membership_diagnostic: 4
```

## Artifacts

```text
runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter/summary.json
runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter/candidate_validation_rows.csv
runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter/guardrail_validation_rows.csv
runs/m2424_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter/claim_boundary_validation_rows.csv
```

## Interpretation

M2424 validates that the M2422 source-linked candidate overlays are
structurally loadable and bounded:

```text
all 4 overlay JSON files load;
all table/payload candidate ids, families, and source row counts match;
all source row key counts match source plan row counts;
all overlay paths remain under the M2422 run directory;
collision, R4, max-step, speed-too-low, diagnostic, and family guardrail refs exist;
diagnostic and family guardrails are monitoring-only;
claim boundary forbids active overwrite, repair execution, family/profile/candidate
ranking, training repair success, and current-sim verdict.
```

This is adapter-readiness evidence only. It does not mean the candidates improve
the driver, because no environment reset, environment step, policy action,
repair execution, replay, PPO, or measured validation ran.

## Claim Boundary

Supported:

```text
M2424 read-only validated all M2422 source-linked candidate overlays and
guardrail metadata.
```

Blocked:

```text
environment reset success
measured rollout
repair execution
scenario redesign executed
training repair success
candidate ranking
source-linked family ranking
controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Validation

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_source_linked_candidate_reset_load_validation_adapter.py

5 passed
```

## Next

Next milestone:

```text
m2425-paper-route-current-sim-dual-axis-source-linked-repair-plan-materialization-branch-synthesis
```

M2425 should synthesize the source-linked repair-plan/candidate/adapter branch
before any further ordinary artifact step. It must decide whether to continue
to a new evidence-producing route, pivot, stop, or promote to a new branch
without running measured rollout, executing repair, training, ranking,
overwriting active configs, or making current-sim/paper/self-ID verdict claims.
