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
m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis
```

Current next task:

```text
m2387-paper-route-current-sim-dual-axis-candidate-config-safety-validation-design
```

Current route:

```text
M2386 synthesized the M2381-M2385 candidate config generation branch and
continued to bounded candidate config safety/reset-validation design. M2387 may
design validation only. It must not load configs, reset environments, run
rollouts, execute repair, rank, train, or make paper/self-ID/current-sim claims.
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

M2387 should design bounded candidate config safety/reset validation from:

```text
docs/m2386-paper-route-current-sim-dual-axis-candidate-config-generation-branch-synthesis.md
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/summary.json
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_config_rows.csv
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_patch_reference_matrix.csv
runs/m2385_paper_route_current_sim_dual_axis_offtrack_guardrail_candidate_config_generation/candidate_guardrail_scope_rows.csv
```

The design must specify inventory, schema/path safety checks, future reset-only
validation scope, blocked rollout/training/ranking routes, and failure taxonomy.
M2387 itself must not load candidate configs, run reset/rollout, execute
repair, train, replay, use PPO, rank profiles or packs, select a winner, claim
scenario redesign executed, claim repair success, current-sim verdict, or
paper/self-ID claims.
