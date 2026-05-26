# M971 V4 Public Base Post-Promotion Guarded PPO Readiness Design

## Purpose

M971 designs the first guarded PPO readiness step after M969 promoted alpha
`1.0` as the current public-gate base.

Current public-gate base:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

M971 does not train, run PPO, use private holdout, change actor inputs, or make
a new driver capability claim.

## Why A Readiness Gate Is Required

M969 promotion proves alpha `1.0` is the best current public-gate base. It does
not prove that PPO continuation is safe.

Historical PPO failures in this project often looked like:

```text
aggregate behavior retained
but wrong-history proof rows washed out
or exact objectives regressed
or public proof gates passed only under narrow interpolation
```

So post-promotion PPO must be treated as a proposal generator, not as an
accepted update.

## PPO Proposal Scope

M972 should run exactly one smoke-scale guarded PPO proposal.

Config:

```text
configs/ppo_m972_post_promotion_guarded_smoke.json
```

Base/init checkpoint:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m972_post_promotion_guarded_smoke.json \
  --init-checkpoint runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt \
  --run-dir runs/ppo_m972_post_promotion_guarded_smoke_seed5972
```

PPO limits:

```text
total_steps: 1024
rollout_steps: 128
num_envs: 8
learning_rate: 5e-7
freeze_log_std: true
checkpoint_interval_steps: 1024
```

Anchors:

```text
baseline_action_anchor_checkpoint: alpha_1_0
snippet_action_anchor_checkpoint: alpha_1_0
trajectory_action_anchor_snapshot_npz: runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
outcome_intervention_snapshot_npz: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
rejected_history_preference_snapshot_npz: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
```

This keeps the proposal close to the promoted base while retaining the existing
response-history and rejected-history training signals.

## Acceptance Order

M972 must not promote. It should classify the raw PPO checkpoint through this
order:

1. Raw PPO completes and writes checkpoint.
2. Actor-input contract is unchanged.
3. Training logs are finite.
4. Built-in smoke eval does not collapse.
5. M966 proof replay stack passes versus alpha `1.0`.
6. M968 fresh generalization rows do not regress versus alpha `1.0`.
7. M968 behavior/ablation rows do not regress versus alpha `1.0`.

If the raw checkpoint fails proof or generalization gates but looks useful, the
route is exact repair/projection design, not promotion.

## Proof Retention Gates

M972 should rerun the M966 proof gate stack comparing:

```text
baseline: alpha_1_0
candidate: raw M972 PPO checkpoint
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
source-diverse protected diagnostics pass or are explicitly diagnostic-only
actor_inputs_changed == false
```

## Generalization And Behavior Gates

M972 should rerun the M968 public fresh eval and behavior comparison with the
same non-regression thresholds.

Fresh public eval:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
seeds: 96700, 96701
episodes: 256 per seed
```

Moderate OOD eval:

```text
config: configs/eval_m574_moderate_ood_l3.json
seed: 96720
episodes: 128
```

Behavior seeds:

```text
9505
9506
96730
96731
```

Candidate ablations:

```text
none
reset_recurrent_state
zero_all_response
```

Pass rule:

```text
candidate success_rate >= alpha_1_0 success_rate - 0.01
candidate termination_rate <= alpha_1_0 termination_rate + 0.01
candidate min_clearance_margin_mean >= alpha_1_0 margin_mean - 0.005
normal success >= reset success >= zero_all success
```

## Result Classes

M972 should classify into:

```text
post_promotion_guarded_ppo_raw_candidate
post_promotion_guarded_ppo_contract_artifact
post_promotion_guarded_ppo_training_instability
post_promotion_guarded_ppo_proof_washout
post_promotion_guarded_ppo_generalization_regression
post_promotion_guarded_ppo_behavior_regression
post_promotion_guarded_ppo_needs_exact_repair
```

Only `post_promotion_guarded_ppo_raw_candidate` may route to a separate
full-promotion gate. All other non-contract failures route to audit or exact
repair/projection design.

## Required M972 Artifacts

M972 should write:

```text
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/summary.json
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/ppo_run_dir.txt
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/proof_replay_summary.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/fresh_randomized_eval_summary.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/ood_eval_summary.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/behavior_summary.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/behavior_comparison.csv
runs/m972_v4_public_base_post_promotion_guarded_ppo_smoke/route_decision.csv
```

## Next Blocker

M971 routes to:

```text
m972-v4-public-base-post-promotion-guarded-ppo-smoke-implementation
```

M972 should run one smoke PPO proposal from alpha `1.0`, then gate it. It must
not promote and must not use private holdout.
