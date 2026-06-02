# M2378 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Config Patch Materialization

- status: completed
- result_class: `current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass`
- manifest: `experiments/manifests/m2378-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization.py`
- focused tests: `2 passed`
- summary: `runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/summary.json`
- reset/rollout/measured execution in M2378: `false`
- policy action executed in M2378: `false`
- active config overwritten in M2378: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Source Artifacts

M2378 reads only audited M2375 repair-plan artifacts:

```text
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/repair_implementation_plan.json
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/reward_delta_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/curriculum_weight_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/guardrail_constraint_rows.csv
runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/mixed_guarded_constraint_rows.csv
```

## Output Artifacts

M2378 writes candidate overlay artifacts only:

```text
config_patch_manifest.json
reward_config_patch_rows.csv
curriculum_config_patch_rows.csv
guardrail_config_patch_rows.csv
config_patch_preview.json
claim_boundary.csv
summary.json
```

No active scenario config is overwritten.

## Result Counts

```text
source_reward_delta_row_count: 54
source_curriculum_weight_row_count: 54
source_guardrail_constraint_row_count: 284
source_mixed_guarded_constraint_row_count: 18
reward_config_patch_row_count: 162
curriculum_config_patch_row_count: 54
guardrail_config_patch_row_count: 284
claim_boundary_row_count: 12
```

Target namespace counts:

```text
candidate_reward_overlay: 162
candidate_curriculum_overlay: 54
candidate_guardrail_overlay: 284
```

Guardrail target counts:

```text
guardrail.collision_rate_not_worse: 46
guardrail.r4_mitigation_semantics_preserved: 48
guardrail.no_ranking_no_winner_claims: 190
```

## Guardrail Checks

```text
active_config_overwrite_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
profile_specific_tuning_count: 0
repair_execution_count: 0
training_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
namespace_violation_count: 0
mixed_guarded_missing_count: 0
non_required_guardrail_count: 0
guardrail_violation_count: 0
```

The mixed guarded rows remain represented in the guardrail overlay:

```text
source_mixed_guarded_constraint_row_count: 18
mixed_guarded_missing_count: 0
```

## Decision

M2378 passes as artifact-only overlay config-patch materialization.

Allowed claim:

```text
Audited repair-plan artifacts have been converted into candidate overlay
config-patch artifacts with active config overwrite, repair execution,
training, ranking, and paper/self-ID/current-sim verdict claims blocked.
```

Still blocked:

```text
active config overwrite
repair execution
environment reset or rollout
measured validation
training repair success
scenario redesign executed
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Next

Route to:

```text
m2379-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-materialization-result-audit
```

M2379 should audit these artifacts before any application, reset validation,
repair execution, or ranking route is designed.
