# M2377 Paper-Route Current-Sim Dual-Axis Offtrack Guardrail Repair Plan Application Design

- status: completed
- decision: `repair_plan_application_design_admit_artifact_only_config_patch_materializer`
- manifest: `experiments/manifests/m2377-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-application-design.json`
- parent audit: `docs/m2376-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization-result-audit.md`
- source summary: `runs/m2375_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_plan_materialization/summary.json`
- reset/rollout/measured execution in M2377: `false`
- policy action executed in M2377: `false`
- active config overwrite in M2377: `false`
- repair execution/training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Goal

M2377 designs a static overlay-only config-patch materializer from M2375
repair-plan artifacts. It does not apply patches to the active config and does
not execute repair. The next implementation should produce candidate patch
artifacts under a run directory only.

Source artifacts:

```text
repair_implementation_plan.json
reward_delta_rows.csv
curriculum_weight_rows.csv
guardrail_constraint_rows.csv
mixed_guarded_constraint_rows.csv
claim_boundary.csv
summary.json
```

## Patch Artifact Schema

M2378 should write these files:

```text
config_patch_manifest.json:
  overlay-only patch manifest with source artifacts, output files,
  target namespaces, blocked levers, guardrail counts, and claim boundary.

reward_config_patch_rows.csv:
  reward overlay rows derived from reward_delta_rows.csv.

curriculum_config_patch_rows.csv:
  curriculum overlay rows derived from curriculum_weight_rows.csv.

guardrail_config_patch_rows.csv:
  guardrail overlay rows derived from guardrail_constraint_rows.csv and
  mixed_guarded_constraint_rows.csv.

config_patch_preview.json:
  deterministic preview of patch families and count summaries, not an active
  environment config.

claim_boundary.csv:
  same blocked claim boundary as M2375/M2376, extended with active-config
  overwrite and current-sim verdict blocks.

summary.json:
  result class, count checks, guardrail flags, artifact paths, and next
  blocker.
```

## Patch Row Rules

Reward patch rows should be overlay records only:

```text
patch_family: reward_delta
target_namespace: candidate_reward_overlay
target_key:
  reward.offtrack_margin_weight_delta
  reward.recovery_window_weight_delta
  reward.boundary_overshoot_penalty_delta
delta_value: numeric value from M2375 reward_delta_rows.csv
source_repair_spec_id: original repair_spec_id
active_config_overwritten: false
```

Curriculum patch rows should be overlay records only:

```text
patch_family: curriculum_weight
target_namespace: candidate_curriculum_overlay
target_key: curriculum.source_slice_sampling_weight_multiplier
delta_value: numeric value from M2375 curriculum_weight_rows.csv
source_repair_spec_id: original repair_spec_id
profile_specific_tuning: false
active_config_overwritten: false
```

Guardrail patch rows should be constraint records only:

```text
patch_family: guardrail_constraint
target_namespace: candidate_guardrail_overlay
target_key:
  guardrail.collision_rate_not_worse
  guardrail.r4_mitigation_semantics_preserved
  guardrail.no_ranking_no_winner_claims
required: true
active_config_overwritten: false
```

## Pass Gates For M2378

M2378 should pass only if:

```text
source_reward_delta_row_count == 54
source_curriculum_weight_row_count == 54
source_guardrail_constraint_row_count == 284
source_mixed_guarded_constraint_row_count == 18
reward_config_patch_row_count == 162
curriculum_config_patch_row_count == 54
guardrail_config_patch_row_count == 284
active_config_overwritten == false
actor_input_change_count == 0
hidden_oracle_feature_injection_count == 0
profile_specific_tuning_count == 0
repair_execution_started == false
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
training_started == false
replay_started == false
ppo_used == false
ranking_admissible_count == 0
winner_selected_count == 0
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
training_repair_success_claim_made == false
current_sim_verdict_claim_made == false
guardrail_violation_count == 0
```

The expected reward patch count is:

```text
54 reward rows * 3 reward delta keys = 162 patch rows
```

## Guardrail Policy

The materializer must fail closed if any of these happen:

```text
active scenario config is overwritten;
patch target namespace is not an overlay namespace;
actor input contract is modified;
hidden/oracle features are introduced;
profile-specific tuning appears;
mixed guarded collision constraints are dropped;
R4 semantics become ordinary avoidance repair;
diagnostic rows become ranking-admissible;
any execution/training/replay/PPO flag is true.
```

## Decision

M2377 routes to:

```text
m2378-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-materialization
```

M2378 should implement the artifact-only static config-patch materializer. It
should not apply the patches, overwrite active configs, run reset/rollout,
execute repair, train, replay, use PPO, rank profiles or packs, select a
winner, claim current-sim verdict, or make paper/self-ID claims.

## Claim Boundary

M2377 may claim only:

```text
A bounded overlay-only config-patch application design has been defined from
audited repair-plan artifacts.
```

Still blocked:

```text
active config overwrite
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

Pre-register:

```text
m2378-paper-route-current-sim-dual-axis-offtrack-guardrail-config-patch-materialization
```
