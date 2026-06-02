# Current Status

This file is the compact official state for the project. Milestone documents
remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Current Research Blocker

Latest completed milestone:

```text
m2400-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-result-audit
```

Latest attempted milestone:

```text
m2400-paper-route-current-sim-dual-axis-effective-candidate-measured-outcome-localization-result-audit
result: completed
```

Current next task:

```text
m2401-paper-route-current-sim-dual-axis-effective-candidate-actionable-target-consolidation-implementation
```

Current route:

```text
M2391 materialized run-dir-only effective candidate pack artifacts by joining
M2385 overlay candidates to M2356 reset-valid repaired pack scenario specs.
M2394 implemented and ran the reset-only adapter for M2391 effective candidate
artifacts. All 2049 candidate-scenario references passed static validation, all
350 unique reset targets reset successfully, and all 54 effective candidates
passed candidate-level reset aggregation. No environment step or policy action
occurred. M2395 accepted this as reset-readiness evidence only and routed to a
bounded measured-validation design. M2396 froze the effective-candidate
measured-validation protocol: 2049 candidate-scenario references times 15
selected checkpoints, for 30735 closed-loop episodes. M2397 implemented and ran
that full panel with clean lineage and guardrails. M2398 accepted the artifact
as complete but classified the measured outcome as offtrack-dominated. The next
task is M2399 artifact-only outcome localization over M2397 rows, with no
rerun, repair, training, ranking, or paper/self-ID/current-sim verdict route.
M2399 materialized localization slices; M2400 must audit whether those slices
are actionable enough for consolidation or whether the branch should pivot,
synthesize, or stop. M2400 accepted localization as actionable but too broad for
direct repair, and routed to M2401 artifact-only actionable target
consolidation.
```

## Latest Evidence

M2362 produced the complete measured panel over the repaired five-pack family:

```text
episode_count: 5400
config_pack_count: 5
scenario_specs_per_pack_count: 72
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
global success_rate: 0.06518518518518518
global offtrack_rate: 0.7262962962962963
global collision_rate: 0.19962962962962963
dominant_failure_mode: offtrack_dominated_failure
```

M2390 schema repair design:

```text
decision: effective_candidate_pack_schema_repair_route_to_materialization
base env config lineage: M2356 repaired five-pack family
base reset validation: M2359 360/360 reset successes
base measured execution lineage: M2362 5400 episodes
candidate overlays: M2385 54 run-dir-only files
schema correction: overlay + base pack scenario selection, not one env_config per overlay
M2391 output target: effective_candidate_configs/*.json under run dir only
M2391 blocked: environment load/reset/step, policy action, repair execution,
  training/replay/PPO, ranking/winner, paper/FW-vs-GRU/level3 self-ID,
  scenario-redesign/training-repair/current-sim verdict claims
```

M2391 materialization result:

```text
result_class: current_sim_dual_axis_effective_config_schema_repair_materialization_pass
source_candidate_config_count: 54
static_validation_pass_count: 54
effective_candidate_config_written_count: 54
effective_candidate_config_outside_run_dir_count: 0
candidate_without_matching_scenarios_count: 0
candidate_without_env_config_count: 0
actor_contract_violation_count: 0
base_pack_count: 5
base_scenario_specs_per_pack_count: 72
selected_scenario_reference_count: 2049
min/max selected_scenario_count: 6/180
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_step_count: 0
guardrail_violation_count: 0
```

M2392 synthesis decision:

```text
synthesis window: M2387-M2391
synthesis_decision: continue
decision: continue_to_effective_candidate_reset_validation_adapter_design
actual capability changed: effective candidate pack artifact generation
still blocked: reset compatibility, rollout/measured execution, repair
  execution, training, ranking, paper/FW-vs-GRU/level3 self-ID/current-sim
  verdict claims
next task: M2393 reset-validation adapter design
```

M2393 adapter design:

```text
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
duplicate policy: deduplicate by pack_id + scenario_spec_id
future M2394 reset scope: reset-only, no environment step and no policy action
future pass target: 350/350 reset successes and 54/54 candidate reset passes
still blocked: rollout/measured execution, repair execution, training, ranking,
  paper/FW-vs-GRU/level3 self-ID/current-sim verdict claims
```

M2394 reset-validation adapter result:

```text
result_class: current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass
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
guardrail_violation_count: 0
```

M2395 reset-validation adapter result audit:

```text
decision: effective_candidate_reset_validation_result_accepted_route_to_measured_validation_design
accepted evidence: M2394 reset-readiness only
observed failure types: none
reset rerun/rollout/policy action/repair/training/ranking: false
blocked claims: measured performance, repair success, paper verdict,
  finite-window-vs-GRU, level3 self-ID, scenario redesign executed,
  current-sim verdict
next task: M2396 measured-validation design
```

M2396 effective-candidate measured-validation design:

```text
decision: effective_candidate_measured_validation_design_admit_implementation
effective candidates: 54
candidate-scenario references: 2049
unique reset targets: 350
selected checkpoints: 15
target measured episodes: 30735
denominator: candidate_id + pack_id + scenario_spec_id + selected checkpoint
reset/rollout/policy action in M2396: false/false/false
blocked claims: ranking, paper verdict, finite-window-vs-GRU, level3 self-ID,
  scenario redesign executed, training repair success, current-sim verdict
next task: M2397 measured-validation implementation
```

M2397 effective-candidate measured-validation implementation:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_validation_pass
episode_count: 30735
target_episode_count: 30735
source_candidate_count: 54
candidate_scenario_reference_count: 2049
unique_pack_scenario_count: 350
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
global success_rate: 0.04054010086220921
global offtrack_rate: 0.8425898812428827
global collision_rate: 0.10157800553115341
dominant_failure_mode: offtrack_dominated_failure
ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: false
next task: M2398 measured-validation result audit
```

M2398 effective-candidate measured-validation result audit:

```text
decision: effective_candidate_measured_validation_complete_offtrack_dominated_route_to_outcome_localization
accepted artifact: M2397 complete 30735/30735 episodes
failure/validation/metadata/metric/contract/guardrail counts: 0/0/0/0/0/0
outcome_quality: offtrack_dominated_failure
global success_rate: 0.04054010086220921
global offtrack_rate: 0.8425898812428827
global collision_rate: 0.10157800553115341
metric_artifact/lineage_invalid/contract_violation: not observed
ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: false
next task: M2399 artifact-only measured outcome localization implementation
```

M2399 effective-candidate measured outcome localization:

```text
result_class: current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass
source_episode_count: 30735
source_candidate_count: 54
source_profile_count: 5
source_role_family_count: 6
slice_row_count: 1313
offtrack_target_slice_count: 1132
collision_guardrail_slice_count: 364
r4_mitigation_semantics_slice_count: 57
diagnostic_only_slice_count: 96
high_priority_offtrack_slice_count: 658
route_class_counts: offtrack_target 796, offtrack_target_with_collision_guardrail 336, collision_guardrail 28, r4_mitigation_semantics 57, diagnostic_only 96
ranking_admissible_count/winner_selected_count/guardrail_violation_count: 0/0/0
top localized blockers: centerline offtrack, drift_required offtrack+collision, early_far offtrack, guarded_offtrack_containment_repair offtrack+collision, R4 collision semantics
next task: M2400 localization result audit
```

M2400 effective-candidate measured outcome localization result audit:

```text
decision: effective_candidate_measured_outcome_localization_accepted_route_to_actionable_target_consolidation
accepted M2399 localization: source episodes 30735, slice rows 1313
offtrack/collision/R4/diagnostic/high-priority-offtrack counts: 1132/364/57/96/658
route_class_counts: offtrack_target 796, offtrack_target_with_collision_guardrail 336, collision_guardrail 28, r4_mitigation_semantics 57, diagnostic_only 96
classification: actionable enough to continue but too broad for direct repair
blocked: raw slice ranking, candidate/profile ranking, direct repair, paper/current-sim/self-ID verdict
next task: M2401 artifact-only actionable target consolidation implementation
```

M2363 audited M2362 and blocked raw ranking or paper interpretation:

```text
primary offtrack target roles: R0, R2, R3, R5
separate mitigation semantics role: R4_unavoidable_mitigation
profile aggregates: diagnostic only
pack aggregates: diagnostic only
winner selected: false
finite-window vs GRU conclusion: false
level3 self-ID claim: false
```

M2364 designed artifact-only localization. M2365 implemented and ran it:

```text
result_class: current_sim_dual_axis_measured_outcome_localization_pass
source_episode_count: 5400
slice_row_count: 313
offtrack_target_slice_count: 198
collision_guardrail_slice_count: 95
r4_mitigation_semantics_slice_count: 48
high_priority_offtrack_slice_count: 99
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

M2365 route classes:

```text
offtrack_target: 118
offtrack_target_with_collision_guardrail: 80
collision_guardrail: 15
r4_mitigation_semantics: 48
diagnostic_only: 52
```

M2366 audit decision:

```text
M2365 localization accepted: true
next route: actionable target consolidation design
diagnostic-only/guardrail-heavy axes: global, pack_id, profile_name, sampling_repair_class
actionable axes: role_family, scenario_family_id, sampled_obstacle_label,
  timing bucket, lateral bucket, hidden dynamics bucket, and role-conditioned
  timing/lateral/hidden axes
R4 mitigation semantics: separate route, not ordinary offtrack repair
```

M2367 design decision:

```text
diagnostic-only axes: global, pack_id, profile_name, sampling_repair_class,
  pack/profile composites
actionable axes: role_family, scenario_family_id, sampled_obstacle_label,
  hidden dynamics, timing, lateral, and role-conditioned hidden/timing/lateral
ordinary repair target excludes: diagnostic axes and R4 semantics rows
M2368 command: artifact-only consolidation, no reset/rollout/training/ranking
```

M2368 result:

```text
source_slice_row_count: 313
consolidated_row_count: 313
offtrack_repair_target_row_count: 54
collision_guardrail_row_count: 28
r4_mitigation_semantics_row_count: 48
diagnostic_guardrail_row_count: 190
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
guardrail_violation_count: 0
```

M2369 audit decision:

```text
M2368 consolidation accepted: true
next route: bounded offtrack guardrail repair design
ordinary offtrack repair targets: 54
collision guardrail rows: 28
R4 mitigation semantics rows: 48
diagnostic guardrail rows: 190
direct training/repair-success claim: blocked
```

M2370 design decision:

```text
repair families: priority offtrack, ordinary offtrack, guarded offtrack,
  collision guardrail, R4 mitigation semantics guardrail, diagnostic guardrail
allowed repair levers are names only; none are executed in M2370/M2371
blocked: actor input change, oracle features, profile-specific tuning,
  winner selection, R4 ordinary repair, collision-blind offtrack objective,
  scenario-redesign-executed claim, training-repair-success claim
```

M2371 result:

```text
repair_spec_row_count: 320
priority_offtrack_containment_repair: 26
offtrack_containment_repair: 10
guarded_offtrack_containment_repair: 18
collision_guardrail_constraint: 28
r4_mitigation_semantics_guardrail: 48
diagnostic_no_ranking_guardrail: 190
profile_or_pack_repair_spec_count: 0
r4_ordinary_repair_spec_count: 0
collision_blind_mixed_repair_spec_count: 0
guardrail_violation_count: 0
```

M2372 audit decision:

```text
M2371 repair specs accepted: true
next route: bounded offtrack guardrail repair implementation design
ordinary offtrack specs: 36
mixed guarded offtrack specs: 18
collision guardrail specs: 28
R4 mitigation semantics guardrail specs: 48
diagnostic no-ranking guardrail specs: 190
profile/pack ordinary repair specs: 0
R4 ordinary repair specs: 0
collision-blind mixed repair specs: 0
repair execution/training/replay/PPO: false
```

M2373 implementation design decision:

```text
implementation route: artifact-only repair plan materialization
future outputs: repair plan, reward deltas, curriculum weights, guardrail constraints
ordinary offtrack direct repair specs: 36
mixed guarded specs requiring collision constraints: 18
guardrail-only specs: 28 collision, 48 R4, 190 diagnostic
active config overwrite: blocked
actor input change/oracle feature/profile-specific tuning: blocked
repair execution/training/replay/PPO: false
next route: outcome-localization branch synthesis
```

M2374 branch synthesis decision:

```text
synthesis decision: continue
next branch: paper_route_current_sim_dual_axis_repair_plan_materialization
next route: artifact-only repair-plan materialization
supported: task-quality artifacts are clean enough for repair-plan artifacts
blocked: repair success, scenario redesign executed, ranking, current-sim verdict,
  finite-window-vs-GRU, level3 self-ID
```

M2375 repair-plan materialization result:

```text
input_repair_spec_row_count: 320
ordinary/mixed/collision/R4/diagnostic source counts: 36/18/28/48/190
reward_delta_row_count: 54
curriculum_weight_row_count: 54
guardrail_constraint_row_count: 284
mixed_guarded_constraint_row_count: 18
profile_specific_tuning_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
collision_blind_mixed_repair_count: 0
r4_ordinary_repair_count: 0
guardrail_violation_count: 0
repair execution/training/replay/PPO: false
```

M2376 audit decision:

```text
M2375 repair-plan artifacts accepted: true
next route: bounded static config-patch application design
reward/curriculum rows: 54/54
guardrail/mixed guarded constraints: 284/18
exclusions and guardrail violations: 0
active config overwrite/repair execution/training: blocked
```

M2377 application design decision:

```text
design: overlay-only config-patch materializer
expected reward/curriculum/guardrail patch rows: 162/54/284
active config overwrite: blocked
actor input change/oracle feature/profile-specific tuning: blocked
repair execution/training/replay/PPO: false
next route: artifact-only config-patch materialization
```

M2378 config-patch materialization result:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_config_patch_materialization_pass
source reward/curriculum/guardrail/mixed rows: 54/54/284/18
reward_config_patch_row_count: 162
curriculum_config_patch_row_count: 54
guardrail_config_patch_row_count: 284
target namespaces: candidate_reward_overlay 162, candidate_curriculum_overlay 54,
  candidate_guardrail_overlay 284
guardrail targets: collision 46, R4 semantics 48, no-ranking 190
active_config_overwrite_count: 0
actor_input_change_count: 0
hidden_oracle_feature_injection_count: 0
profile_specific_tuning_count: 0
repair_execution_count/training_count/ranking_admissible_count/winner_selected_count: 0/0/0/0
guardrail_violation_count: 0
```

M2379 audit decision:

```text
M2378 config-patch artifacts accepted: true
next route: repair-plan materialization branch synthesis before application design
reward/curriculum/guardrail patch rows: 162/54/284
target namespaces: candidate overlay namespaces only
active config overwrite/repair execution/training/ranking: blocked
current-sim verdict/paper/self-ID claims: blocked
```

M2380 branch synthesis decision:

```text
synthesis window: M2375-M2379
synthesis decision: continue
next route: bounded candidate config-patch application design
actual capability changed: artifact capability only
driver behavior/training/validation changed: false
public gate overfit risk: moderate
local-search guard: triggered correctly and reset by synthesis
paper/self-ID/current-sim verdict claims: blocked
```

M2381 application design decision:

```text
design: artifact-only application-plan materializer
candidate_application_spec_count expected: 54
reward/curriculum/guardrail patch references expected: 162/54/284
mixed_guarded_candidate_requirement_count expected: 18
active config overwrite/config patch application/candidate config generation: blocked
reset/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
```

M2382 application-plan materialization result:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_config_patch_application_plan_materialization_pass
candidate_application_spec_count: 54
candidate repair families: priority 26, ordinary 10, guarded mixed 18
reward/curriculum/guardrail patch references: 162/54/284
mixed_guarded_candidate_requirement_count: 18
candidate_without_reward/curriculum/guardrail counts: 0/0/0
active_config_overwrite_count/config_patch_applied_count/candidate_config_file_written_count: 0/0/0
guardrail_violation_count: 0
```

M2383 audit decision:

```text
M2382 application-plan artifacts accepted: true
next route: bounded candidate config generation design
candidate_application_spec_count: 54
reward/curriculum/guardrail patch references: 162/54/284
active config overwrite/config patch application/candidate config generation: blocked
reset/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
```

M2384 candidate config generation design:

```text
design: run-dir-only candidate config generation materializer
candidate_config_file_written_count expected in M2385: 54
candidate_config_files_outside_run_dir_count expected: 0
source reward/curriculum/guardrail references expected: 162/54/284
mixed_guarded_candidate_requirement_count expected: 18
active config overwrite/reset/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
next after M2385: branch synthesis, not another narrow audit
```

M2385 candidate config generation result:

```text
result_class: current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass
source_candidate_application_spec_count: 54
candidate_config_file_written_count: 54
candidate_config_files_outside_run_dir_count: 0
source reward/curriculum/guardrail references: 162/54/284
mixed_guarded_candidate_requirement_count: 18
candidate_without_reward/curriculum/guardrail counts: 0/0/0
candidate repair families: priority 26, ordinary 10, guarded mixed 18
active_config_overwrite_count: 0
active_config_patch_application_count: 0
loaded_into_environment_count: 0
environment_reset_count: 0
guardrail_violation_count: 0
repair/training/replay/PPO/ranking/winner claims: false
paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim claims: false
next: M2386 branch synthesis
```

M2386 branch synthesis decision:

```text
synthesis window: M2381-M2385
synthesis decision: continue
next route: bounded candidate config safety/reset-validation design
actual capability changed: artifact capability only
driver behavior/training/validation changed: false
public gate overfit risk: moderate
local-search guard: triggered correctly and reset by synthesis
paper/self-ID/current-sim verdict claims: blocked
```

M2387 safety validation design:

```text
design: static safety checks plus future reset-only validation
source candidate configs: 54
target static_validation_pass_count in M2388: 54
target effective_config_written_count in M2388: 54 if schema permits
target environment_reset_attempt_count in M2388: 54 if static checks pass
environment_step_count target: 0
active_config_overwrite target: 0
policy action/rollout/repair/training/ranking: blocked
paper/self-ID/current-sim verdict claims: blocked
```

M2388 reset validation implementation result:

```text
result_class: current_sim_dual_axis_candidate_config_reset_validation_fail
source_candidate_config_count: 54
static_validation_pass_count: 54
static_validation_failure_count: 0
schema_incomplete_candidate_count: 54
effective_config_written_count: 0
effective_config_outside_run_dir_count: 0
environment_load_attempt_count: 0
environment_reset_attempt_count: 0
environment_reset_success_count: 0
environment_step_count: 0
active_config_overwrite_count: 0
guardrail_violation_count: 0
failure_types_observed: effective_config_materialization_failure
```

M2389 result audit decision:

```text
decision: schema_incomplete_reset_validation_failure_route_to_effective_config_schema_repair_design
schema incompleteness vs sampler incompatibility: schema incompleteness
reset compatibility demonstrated: false
unsafe execution observed: false
next route: bounded effective-config schema repair design
```

## Current Interpretation Boundary

Allowed claim:

```text
Run-dir-only candidate config artifacts have been generated from audited
application-plan artifacts without active config overwrite or execution.
```

Blocked claims:

```text
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Immediate Next Step

M2390 should design effective-config schema repair from:

```text
docs/m2389-paper-route-current-sim-dual-axis-candidate-config-reset-validation-result-audit.md
runs/m2388_paper_route_current_sim_dual_axis_candidate_config_reset_validation/summary.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_config_rows.csv
```

The design must identify legitimate base env config lineage, define candidate
overlay merge semantics, and specify run-dir-only effective config artifacts.
It must fail closed if no base lineage is defensible. It must not materialize
effective configs, reset, execute repair, train, replay, use PPO, rank profiles
or packs, select a winner, claim scenario redesign executed, claim repair
success, current-sim verdict, or paper/self-ID claims.
