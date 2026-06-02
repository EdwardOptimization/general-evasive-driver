# M2394 Paper-Route Current-Sim Dual-Axis Effective Candidate Reset Validation Adapter Implementation

- status: completed
- result class: `current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass`
- manifest: `experiments/manifests/m2394-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter.py`
- focused tests: `2 passed`
- summary: `runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json`
- source: `runs/m2391_paper_route_current_sim_dual_axis_effective_config_schema_repair_materialization`
- repair execution/training/replay/PPO: `false`
- environment rollout/policy action/environment step: `false/false/0`
- active config overwrite: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Result Summary

M2394 implemented and ran the reset-only adapter designed in M2393:

```text
source_candidate_config_count: 54
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
static_validation_pass_count: 2049
static_validation_failure_count: 0
environment_load_attempt_count: 350
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_reset_failure_count: 0
candidate_reset_pass_count: 54
candidate_reset_failure_count: 0
environment_step_count: 0
policy_action_executed: false
active_config_overwrite_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
failure_types_observed: []
```

Reset target counts by pack:

```text
baseline_reference_pack: 70
g_primary_pack: 70
h_primary_pack: 70
g_h_primary_pack: 70
gh_minimal_pack: 70
```

Output row counts:

```text
static_validation_rows.csv: 2049 data rows
reset_target_rows.csv: 350 data rows
reset_validation_rows.csv: 350 data rows
effective_candidate_reset_summary_rows.csv: 54 data rows
```

## Artifacts

M2394 wrote:

```text
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/summary.json
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/static_validation_rows.csv
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_target_rows.csv
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_validation_rows.csv
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/candidate_scenario_reset_rows.csv
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/effective_candidate_reset_summary_rows.csv
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/reset_failure_rows.csv
runs/m2394_paper_route_current_sim_dual_axis_effective_candidate_reset_validation_adapter/claim_boundary.csv
```

## Supported Claims

M2394 supports these bounded claims:

- M2391 effective candidate artifacts are reset-compatible under the M2393
  duplicate policy.
- All 2049 candidate-scenario references pass static validation.
- All 350 unique reset targets load and reset successfully.
- All 54 effective candidates pass candidate-level reset aggregation.
- The adapter preserved no environment step, no policy action, no active config
  overwrite, no repair execution, no training, and no ranking.

## Blocked Claims

M2394 still blocks:

```text
rollout or measured execution
repair execution
training repair success
support-policy or controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Decision

Decision:

```text
effective_candidate_reset_validation_adapter_pass_route_to_result_audit
```

Next milestone:

```text
m2395-paper-route-current-sim-dual-axis-effective-candidate-reset-validation-adapter-result-audit
```

M2395 should audit the reset adapter pass and choose the next bounded route. It
should not rerun reset validation, run rollout, execute repair, train, rank, or
make paper/self-ID/current-sim claims.
