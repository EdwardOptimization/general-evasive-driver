# M1383 Paper-Route History-Profile Artifact Inventory

## Purpose

M1383 inventories existing profile configs, checkpoints, runners, and lineage
compatibility before any new L0/L1/L2/L3 comparison.

This milestone does not train, run PPO, run new evaluation, promote a checkpoint,
use private holdout, export a corpus, change actor inputs, or claim an
architecture ranking.

## Inventory Summary

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Existing source-rich diagnostic artifacts:

```text
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json
docs/m1381-paper-route-promoted-base-source-rich-comparison-readiness-synthesis.md
```

Existing corrected profile branch artifacts:

```text
configs/paper_route_profiles/
configs/paper_route_corrected_profiles/
runs/m1212_corrected_profile_repeat/summary.json
runs/m1212_corrected_profile_repeat/profile_aggregate.csv
runs/m1212_corrected_profile_repeat/profile_runs/
```

The inventory is positive for infrastructure existence but negative for direct
fair architecture comparison against M1362.

## Config Inventory

Smoke profile configs exist:

```text
configs/paper_route_profiles/m1190_l0_current_masked_smoke.json
configs/paper_route_profiles/m1190_l1_one_step_smoke.json
configs/paper_route_profiles/m1190_l2_window_13_smoke.json
configs/paper_route_profiles/m1190_l2_window_25_smoke.json
configs/paper_route_profiles/m1190_l2_window_50_smoke.json
configs/paper_route_profiles/m1190_l2_window_100_smoke.json
configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
configs/paper_route_profiles/m1190_l3_reset_control_smoke.json
```

Corrected profile configs exist:

```text
configs/paper_route_corrected_profiles/m1207_l0_current_masked.json
configs/paper_route_corrected_profiles/m1207_l1_one_step.json
configs/paper_route_corrected_profiles/m1207_l2_window_13.json
configs/paper_route_corrected_profiles/m1207_l2_window_13_current_tiled.json
configs/paper_route_corrected_profiles/m1207_l2_window_25.json
configs/paper_route_corrected_profiles/m1207_l2_window_25_current_tiled.json
configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
configs/paper_route_corrected_profiles/m1207_l3_reset_control_corrected.json
```

Corrected controls are represented in config metadata:

```text
L0_current_masked:
  observation_mask: zero_previous_command_fields
  previous_command_mask_indices: [9, 10, 11]
  reset_hidden_policy: not_applicable

L2_window_25_current_tiled:
  actor_encoder: temporal_gru
  env_history_length: 25
  observation_dim: 1800
  history_transform: current_tiled
  current_tiled_history_control: true
  reset_hidden_policy: per_decision_window

L3_reset_control_corrected:
  actor_encoder: human_view_online_gru
  env_history_length: 1
  observation_dim: 72
  reset_hidden_policy: every_step_control
  corrected_reset_control: true
```

Forbidden-input flags are clean in the checked corrected configs:

```text
uses_hidden_oracle_actor_inputs: false
uses_wheel_or_slip_inputs: false
uses_reference_or_ttc_inputs: false
private_holdout_used: false
```

## Checkpoint Inventory

M1212 corrected profile repeat has 24 profile checkpoints:

```text
8 profiles x 3 seeds = 24 checkpoints
```

Profiles present:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

M1212 run status:

```text
result_class: corrected_profile_pilot_completed
total_seed_runs: 24
completed_seed_runs: 24
failed_seed_runs: 0
all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
```

M1212 checkpoint metadata is compatible with matched-history baseline tools.
For example:

```text
L3_online_gru checkpoint:
  config.history_baseline_level: L3_online_gru
  metadata.history_baseline.level: L3_online_gru
  input_contract: P0_human_view_no_wheel_no_oracle

L2_window_25 checkpoint:
  config.history_baseline_level: L2_finite_window
  metadata.history_baseline.level: L2_finite_window
  input_contract: P0_human_view_no_wheel_no_oracle
```

M1362 differs:

```text
config.actor_encoder: human_view_online_gru
config.actor_history_length: 1
config.history_baseline_level: unspecified
metadata keys: alpha, base_checkpoint, ppo_used, promoted, raw_checkpoint, run_type
metadata.history_baseline: absent
metadata.controller_profile: absent
```

Therefore M1362 can be used as the current public-base L3 diagnostic checkpoint,
but it is not a fixed-budget profile checkpoint and is not directly accepted by
matched-history baseline tools that require explicit `history_baseline`
metadata.

## Runner And Tooling Inventory

Available profile tooling:

```text
autodrift.controller_profiles
  canonical profile metadata and observation contract helpers.

autodrift.controller_profile_configs
  generates M1190 smoke configs.

autodrift.corrected_profile_configs
  generates corrected current-tiled and reset-control configs.

autodrift.controller_profile_runtime
  applies observation masks, current-tiled history transforms, and reset policy
  metadata.

autodrift.controller_profile_runtime_smoke
  no-training runtime smoke for profile configs.

autodrift.corrected_profile_pilot
  trains and evaluates corrected public profile pilots.

autodrift.evaluate / autodrift.benchmark
  can evaluate a checkpoint with ablations such as reset_recurrent_state,
  zero_action_history, zero_current_response, and zero_all_response.

autodrift.frozen_source_surface_eval
  can compare matched-history baselines on frozen source surfaces, but currently
  validates explicit history_baseline metadata.
```

Readiness classification:

```text
corrected profile config infrastructure: ready
current-tiled L2 controls: ready
corrected L3 reset semantics: ready
old M1212 profile checkpoints: public diagnostic only
M1362 public-base L3 checkpoint: diagnostic anchor only
M1362 matched-history metadata compatibility: missing
fair architecture ranking: requires fresh fixed-budget refresh
```

## Compatibility Decision

Do not compare M1212 profile checkpoints against M1362 as a fair architecture
ranking.

Reason:

```text
M1212 checkpoints were trained under the older corrected-profile public pilot.
M1362 is a later public-gate base produced by source-history/objective repair and
interpolation. Their training lineage, objectives, and evidence surfaces differ.
```

Do not mutate M1362 to add metadata in place.

Reason:

```text
M1362 is an official public-gate base. If a runner needs profile metadata for
diagnostics, use a sidecar/adaptor or route to a fresh fixed-budget profile
refresh. Do not rewrite the checkpoint artifact.
```

## Route Decision

Decision:

```text
history_profile_artifact_inventory_admit_fixed_budget_refresh_design
```

Next milestone:

```text
m1384-paper-route-history-profile-fixed-budget-refresh-design
```

M1384 should design a fresh fixed-budget profile refresh rather than run a
comparison immediately. It should specify:

```text
profile set:
  L0_current_masked
  L1_one_step
  L2_window_13
  L2_window_13_current_tiled
  L2_window_25
  L2_window_25_current_tiled
  L3_online_gru
  L3_reset_control_corrected

training policy:
  same seeds, same steps, same env/reward/randomization, same optimizer policy
  unless an exception is pre-registered.

evaluation policy:
  same public eval seeds for every checkpoint;
  source-rich temporal diagnostics as secondary public evidence;
  no private holdout until public protocol is stable.

anchor policy:
  M1362 remains current public-base L3 diagnostic anchor, not a fair
  architecture-ranking participant.
```

Only after that design should the project generate current fixed-budget configs
or run a bounded profile refresh.

## Supported Claims

M1383 supports:

```text
1. Existing profile infrastructure is usable and includes corrected controls.
2. M1212 provides old public corrected-profile checkpoints and summaries.
3. M1362 exists as the official public-base L3 diagnostic checkpoint.
4. Direct M1212-vs-M1362 architecture ranking is invalid.
5. Fresh fixed-budget profile refresh is the correct next route for paper-level
   architecture comparison evidence.
```

## Unsupported Claims

M1383 does not support:

```text
1. L0/L1/L2/L3 architecture ranking.
2. M1362 superiority over old profile checkpoints as a fair training-budget
   result.
3. profile promotion.
4. private-holdout evidence.
5. source-rich corpus export.
6. level3 self-identification.
```

## Guardrails

M1383 performs no training, PPO, new evaluation, replay, actor update, checkpoint
mutation, promotion, private holdout, threshold relaxation, actor-input
expansion, corpus export, high-fidelity claim, paper-level profile-ranking
claim, or level3 self-identification claim.
