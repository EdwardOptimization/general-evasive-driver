# M1043 V4 Public Base Combined Active-Set Guarded PPO Readiness Design

## Purpose

M1043 designs the first guarded PPO readiness step after M1041 promoted the
combined active-set checkpoint as the current public-gate base.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or make a new driver capability claim.

## Current Public-Gate Base

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

This base already passed:

```text
M997 exact temporal retention
M297/M270 exact no-regression
combined active-set checks
six public replay surfaces
source-diverse protected diagnostics
fresh public and moderate-OOD public checks
behavior/ablation seeds
```

## Why A New PPO Readiness Protocol Is Required

M1026 showed that smoke PPO can run and preserve broad behavior, but still
wash out a near-boundary wrong-history proof row:

```text
M267/M264 row15 wrong-history margin crossed from -0.000112 to +0.000311
```

M1031 showed that exact repair/projection can retain row15 while exposing a
second active set:

```text
M183/M170 row16 normal margin crossed below zero
```

M1036-M1041 solved both active sets for a no-PPO repaired public base. The
next PPO attempt must therefore guard both active sets from the start and must
not rely on sampled PPO auxiliary metrics as the promotion signal.

## M1044 PPO Proposal Scope

M1044 should implement and run exactly one smoke-scale guarded PPO proposal.

New config to create:

```text
configs/ppo_m1044_combined_active_set_guarded_smoke.json
```

Base/init checkpoint:

```text
runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
```

Run wrapper to implement:

```text
src/autodrift/combined_active_set_guarded_ppo_smoke.py
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt \
  --config configs/ppo_m1044_combined_active_set_guarded_smoke.json \
  --run-dir runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke \
  --ppo-run-dir runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044 \
  --device auto
```

PPO limits:

```text
total_steps: 1024
rollout_steps: 128
num_envs: 8
minibatch_size: 512
learning_rate: 5e-7
freeze_log_std: true
checkpoint_interval_steps: 1024
seed: 61044
```

The config should start from `configs/ppo_m1026_candidate_b_guarded_smoke.json`
with these changes:

```text
baseline_action_anchor_checkpoint:
  M1041 public-gate base

snippet_action_anchor_checkpoint:
  M1041 public-gate base

trajectory_action_anchor_snapshot_npz:
  runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz

training seed:
  61044
```

Existing full-corpus objectives remain:

```text
outcome_intervention_snapshot_npz:
  runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz

rejected_history_preference_snapshot_npz:
  runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz

temporal_sequence_corpus:
  runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
```

## Wrapper Design

The M1044 wrapper should compose existing harness pieces instead of inventing a
new gate:

```text
1. run_ppo_proposal(...)
2. load raw checkpoint from ppo_run_dir/checkpoint.pt
3. verify training metrics are finite
4. verify actor inputs are unchanged
5. run_combined_active_set_full_public_gate(
       base_checkpoint=M1041 public-gate base,
       candidate_checkpoint=raw PPO checkpoint,
       combined_anchor_npz=row16x4 combined anchor,
       fresh_seeds=(103900, 103901),
       ood_seeds=(103920,),
       behavior_seeds=(9505, 9506, 103930, 103931)
   )
6. classify by the first failing tier
```

This makes M1044 stricter than M1026: exact M997/M297/M270, combined active-set
loss, six public replays, source-diverse diagnostics, fresh/OOD checks, and
behavior seeds all gate the raw PPO proposal.

## Acceptance Order

M1044 must not promote. It should classify the raw PPO checkpoint through this
order:

1. Raw PPO completes and writes checkpoint.
2. Actor-input contract is unchanged.
3. Training logs are finite.
4. Exact M997, M297/M270, and combined active-set checks pass.
5. Six public proof replay surfaces pass.
6. Source-diverse protected diagnostics pass.
7. Fresh public and moderate-OOD rows do not regress.
8. Behavior/ablation rows do not regress.

If raw PPO fails exact or proof gates but has finite training and broad
behavior retention, the route is post-PPO exact repair/projection, not
promotion and not longer PPO.

## Hard Rollback Rows

M1044 should always inspect and report:

```text
M267/M264 row15:
  wrong-history branch must remain failing.

M183/M170 row16:
  normal-history branch must remain successful.
```

Expected minimum signal:

```text
M267/M264 success_drop_count remains 17 / 17
M183/M170 success_drop_count remains 17 / 17
actor_inputs_changed == false
```

## Generalization And Behavior Gates

Use the same public checks that promoted the new base:

Fresh public:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
seeds: 103900, 103901
episodes: 256 per seed
```

Moderate OOD:

```text
config: configs/eval_m574_moderate_ood_l3.json
seed: 103920
episodes: 128
```

Behavior seeds:

```text
9505
9506
103930
103931
```

Candidate ablations:

```text
none
reset_recurrent_state
zero_all_response
```

Pass rule:

```text
candidate success_rate >= base success_rate - 0.01
candidate termination_rate <= base termination_rate + 0.01
candidate min_clearance_margin_mean >= base margin_mean - 0.005
candidate collision_rate <= base collision_rate + 0.01
normal success >= reset success >= zero_all success
```

## Result Classes

M1044 should classify into:

```text
combined_active_set_guarded_ppo_raw_candidate
combined_active_set_guarded_ppo_contract_artifact
combined_active_set_guarded_ppo_training_instability
combined_active_set_guarded_ppo_exact_retention_regression
combined_active_set_guarded_ppo_public_replay_washout
combined_active_set_guarded_ppo_source_diagnostic_failed
combined_active_set_guarded_ppo_generalization_regression
combined_active_set_guarded_ppo_behavior_regression
combined_active_set_guarded_ppo_needs_exact_repair
```

Only `combined_active_set_guarded_ppo_raw_candidate` may route to a later
promotion audit. It still must not promote from M1044.

## Required M1044 Artifacts

M1044 should write:

```text
configs/ppo_m1044_combined_active_set_guarded_smoke.json
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/summary.json
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/ppo_run_dir.txt
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/ppo_stdout.log
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/exact_contract_summary.csv
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/proof_replay_summary.csv
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/generalization_comparison.csv
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/behavior_comparison.csv
runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/route_decision.csv
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/train_metrics.csv
docs/m1044-v4-public-base-combined-active-set-guarded-ppo-smoke.md
```

## Forbidden Shortcuts

M1044 must not:

```text
run medium or long PPO;
change actor inputs;
use private holdout;
promote a checkpoint;
skip exact M997/M297/M270/combined-active-set checks;
skip public proof replay gates;
accept aggregate eval if row15 or row16 proof washes out;
claim paper-level generalization.
```

## Decision

```text
combined_active_set_guarded_ppo_readiness_design_admit_m1044_smoke
```

Next:

```text
m1044-v4-public-base-combined-active-set-guarded-ppo-smoke
```
