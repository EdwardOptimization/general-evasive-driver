# M1025 V4 Public Base Candidate B Guarded PPO Readiness Design

## Purpose

M1025 designs the first guarded PPO readiness step after M1023 promoted
Candidate B as the current public-gate base.

Current public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

M1025 does not train, run PPO, use private holdout, change actor inputs, or
make a new driver capability claim.

## Why A Readiness Gate Is Required

M1023 promotion proves Candidate B is the best current public-gate base. It
does not prove that PPO continuation is safe.

Recent history makes the risk concrete:

```text
M972 raw PPO from M964 retained broad behavior but washed out M267/M264 rows 6
and 15.

M302 sampled PPO auxiliary metrics looked live but exact full-corpus M297/M270
regressed.
```

So post-promotion PPO must be treated as a proposal generator, not as an
accepted update.

## PPO Proposal Scope

M1026 should run exactly one smoke-scale guarded PPO proposal.

Config to create:

```text
configs/ppo_m1026_candidate_b_guarded_smoke.json
```

Base/init checkpoint:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.candidate_b_guarded_ppo_smoke \
  --base-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --config configs/ppo_m1026_candidate_b_guarded_smoke.json \
  --run-dir runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke \
  --ppo-run-dir runs/ppo_m1026_candidate_b_guarded_smoke_seed61026 \
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
seed: 61026
```

The config should start from `configs/ppo_m972_post_promotion_guarded_smoke.json`
but update these anchors to Candidate B:

```text
baseline_action_anchor_checkpoint:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt

snippet_action_anchor_checkpoint:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Existing auxiliary corpora can remain:

```text
outcome_intervention_snapshot_npz:
  runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz

rejected_history_preference_snapshot_npz:
  runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz

trajectory_action_anchor_snapshot_npz:
  runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
```

## Acceptance Order

M1026 must not promote. It should classify the raw PPO checkpoint through this
order:

1. Raw PPO completes and writes checkpoint.
2. Actor-input contract is unchanged.
3. Training logs are finite.
4. Built-in smoke eval does not collapse.
5. M997 exact temporal retention does not regress materially versus Candidate B.
6. Six public proof replay surfaces pass versus Candidate B.
7. Source-diverse protected diagnostics pass.
8. Fresh public and moderate-OOD rows do not regress versus Candidate B.
9. Behavior/ablation rows do not regress versus Candidate B.

If raw PPO fails proof or exact gates but looks useful, the route is exact
repair/projection design, not promotion and not longer PPO.

## Exact Temporal Retention Gate

M1026 should recompute M997 exact metrics for:

```text
baseline: Candidate B
candidate: raw M1026 PPO checkpoint
```

Pass rule:

```text
weighted_total_loss <= CandidateB weighted_total_loss + 0.001
weighted_normal_sequence_nll <= CandidateB normal NLL + 0.005
weighted_temporal_preference_loss <= CandidateB preference loss + 0.005
weighted_logp_gap_mean >= CandidateB gap mean - 0.050
temporal_logp_gap_p10 >= CandidateB gap p10 - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080
```

The exact gate is retention, not a claim that PPO improved the temporal
objective.

## Proof Retention Gates

M1026 should compare:

```text
baseline: Candidate B
candidate: raw M1026 PPO checkpoint
```

Required surfaces:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
source-diverse protected diagnostic bundle
old key 9944 diagnostic-only report
```

Pass rule:

```text
all six public replay gates pass
M267/M264 success_drop_count remains 17 / 17
source-diverse protected diagnostics pass
actor_inputs_changed == false
```

## Generalization And Behavior Gates

Use the same public fresh and behavior seeds as M1022 so the first PPO proposal
is compared against the promotion gate that admitted Candidate B:

Fresh public eval:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
seeds: 102100, 102101
episodes: 256 per seed
```

Moderate OOD eval:

```text
config: configs/eval_m574_moderate_ood_l3.json
seed: 102120
episodes: 128
```

Behavior seeds:

```text
9505
9506
102130
102131
```

Candidate ablations:

```text
none
reset_recurrent_state
zero_all_response
```

Pass rule:

```text
candidate success_rate >= CandidateB success_rate - 0.01
candidate termination_rate <= CandidateB termination_rate + 0.01
candidate min_clearance_margin_mean >= CandidateB margin_mean - 0.005
candidate collision_rate <= CandidateB collision_rate + 0.01
normal success >= reset success >= zero_all success
```

## Result Classes

M1026 should classify into:

```text
candidate_b_guarded_ppo_raw_candidate
candidate_b_guarded_ppo_contract_artifact
candidate_b_guarded_ppo_training_instability
candidate_b_guarded_ppo_exact_retention_regression
candidate_b_guarded_ppo_proof_washout
candidate_b_guarded_ppo_generalization_regression
candidate_b_guarded_ppo_behavior_regression
candidate_b_guarded_ppo_needs_exact_repair
```

Only `candidate_b_guarded_ppo_raw_candidate` may route to a later full
promotion gate. It still must not promote from M1026.

## Required M1026 Artifacts

M1026 should write:

```text
configs/ppo_m1026_candidate_b_guarded_smoke.json
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/summary.json
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/ppo_run_dir.txt
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/exact_retention_summary.csv
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/proof_replay_summary.csv
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/fresh_randomized_eval_summary.csv
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/ood_eval_summary.csv
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/behavior_summary.csv
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/behavior_comparison.csv
runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke/route_decision.csv
```

## Forbidden Shortcuts

M1026 must not:

```text
run medium or long PPO
change actor inputs
use private holdout
promote from the smoke checkpoint
skip exact temporal retention
skip public proof replay
accept aggregate eval if wrong-history proof washes out
```

## Decision

```text
candidate_b_guarded_ppo_readiness_design_admit_m1026_smoke
```

Next:

```text
m1026-v4-public-base-candidate-b-guarded-ppo-smoke
```
