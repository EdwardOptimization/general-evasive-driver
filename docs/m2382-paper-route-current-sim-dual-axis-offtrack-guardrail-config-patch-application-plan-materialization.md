# M2382 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Config Patch Application Plan Materialization

- status: completed
- result_class: `current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass`
- manifest: `experiments/manifests/m2382-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization.py`
- focused tests: `2 passed`
- summary: `runs/m2382_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization/summary.json`
- reset/rollout/measured execution in M2382: `false`
- policy action executed in M2382: `false`
- active config overwritten in M2382: `false`
- config patch applied in M2382: `false`
- candidate config file written in M2382: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Source Artifacts

M2382 reads only audited M2378 config-patch artifacts and the M2381 design:

```text
runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/summary.json
runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/config_patch_manifest.json
runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/reward_config_patch_rows.csv
runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/curriculum_config_patch_rows.csv
runs/m2378_paper_route_current_sim_dual_axis_offtrack_guardrail_config_patch_materialization/guardrail_config_patch_rows.csv
docs/m2381-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-design.md
```

## Output Artifacts

M2382 writes application-plan artifacts only:

```text
application_plan_manifest.json
candidate_application_specs.csv
reward_patch_application_refs.csv
curriculum_patch_application_refs.csv
guardrail_patch_application_refs.csv
mixed_guarded_candidate_requirements.csv
config_copy_preview.json
claim_boundary.csv
summary.json
```

No patches are applied and no candidate config files are written.

## Result Counts

```text
source_reward_config_patch_row_count: 162
source_curriculum_config_patch_row_count: 54
source_guardrail_config_patch_row_count: 284
candidate_application_spec_count: 54
reward_patch_reference_count: 162
curriculum_patch_reference_count: 54
guardrail_patch_reference_count: 284
mixed_guarded_candidate_requirement_count: 18
claim_boundary_row_count: 14
```

Candidate repair family counts:

```text
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
```

Guardrail target counts:

```text
guardrail.collision_rate_not_worse: 46
guardrail.r4_mitigation_semantics_preserved: 48
guardrail.no_ranking_no_winner_claims: 190
```

## Guardrail Checks

```text
candidate_without_reward_patch_count: 0
candidate_without_curriculum_patch_count: 0
candidate_without_guardrail_scope_count: 0
active_config_overwrite_count: 0
config_patch_applied_count: 0
candidate_config_file_written_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
profile_specific_tuning_count: 0
repair_execution_count: 0
training_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
non_required_guardrail_reference_count: 0
guardrail_violation_count: 0
```

## Decision

M2382 passes as artifact-only application-plan materialization.

Allowed claim:

```text
Audited overlay config-patch artifacts have been converted into application
plan artifacts that reference patches without applying them or writing
candidate config files.
```

Still blocked:

```text
active config overwrite
config patch application
candidate config file generation
environment reset or rollout
measured validation
repair execution
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
m2383-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-application-plan-materialization-result-audit
```

M2383 should audit these application-plan artifacts before any candidate
config generation, patch application, reset validation, repair execution, or
ranking route is designed.
