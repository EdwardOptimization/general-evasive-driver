# M1026 V4 Public Base Candidate B Guarded PPO Smoke

## Purpose

M1026 runs the first smoke-scale guarded PPO proposal after Candidate B became
the current public-gate base.

Base checkpoint:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Raw PPO checkpoint:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

M1026 is diagnostic only. It does not promote, use private holdout, change
actor inputs, or claim paper-level driver improvement.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.candidate_b_guarded_ppo_smoke \
  --base-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --config configs/ppo_m1026_candidate_b_guarded_smoke.json \
  --run-dir runs/m1026_v4_public_base_candidate_b_guarded_ppo_smoke \
  --ppo-run-dir runs/ppo_m1026_candidate_b_guarded_smoke_seed61026 \
  --device auto
```

PPO scope:

```text
total_steps: 1024
rollout_steps: 128
num_envs: 8
learning_rate: 5e-7
seed: 61026
device: cuda
```

## Result

```text
result_class: candidate_b_guarded_ppo_proof_washout
failure_types: proof_washout
ppo_returncode: 0
training_metrics_finite: true
exact_retention_pass: true
proof_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
actor_inputs_changed: false
promoted: false
private_holdout_used: false
```

The earlier local wrapper misclassified this run as training instability
because it looked for `metrics.csv` while the PPO trainer writes
`train_metrics.csv`. M1026 fixes that wrapper path and reruns the command. The
correct classification is proof washout, not training instability.

## Training Evidence

PPO completed and wrote:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/train_metrics.csv
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/eval_summary.json
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

Training metrics:

```text
rollout_return_mean: 83.46788363819792
reward_mean: 1.029706597328186
episode_count: 9
termination_rate: 0.0
response_prediction_loss_mean: 0.06008068968852361
outcome_intervention_loss_mean: 0.6771693030993143
rejected_history_preference_loss_mean: 0.9354193160931269
baseline_action_anchor_loss_mean: 1.1038426789659421e-06
snippet_action_anchor_loss_mean: 1.4172211032503768e-07
trajectory_action_anchor_loss_mean: 2.4589273228533177e-05
```

Built-in eval summary:

```text
return_mean: 84.6910098240963
steps_mean: 75.6
termination_rate: 0.0
lateral_rmse_mean: 0.9943085127811842
beta_abs_error_mean: 0.14212880515898513
```

## Exact Retention

M997 exact temporal retention passes:

```text
weighted_total_loss: -0.8869785161605426
candidate_action_l2_mean: 0.003195377804452141
candidate_action_l2_max: 0.013455355539917946
exact_gate_pass: true
actor_inputs_changed: false
```

Non-actor parameters changed, as expected for PPO:

```text
non_actor_parameter_changed: true
changed_parameter_count: 16
```

Therefore M1026 uses `exact_gate_pass` for PPO retention and does not treat
`exact_contract_gate_pass == false` as a contract violation. The deployable
actor-input contract is unchanged.

## Proof Replay

Five of six public proof replay surfaces pass:

```text
M183/M168: pass, 16/16 success drops retained
M183/M170: pass, 17/17 success drops retained
M193/M189: pass, 14/14 success drops retained
M212/M204: pass, 17/17 success drops retained
M223/M219: pass, 17/17 success drops retained
M267/M264: fail, 16/17 success drops retained
```

M267/M264 details:

```text
baseline_success_drop_count: 17
candidate_success_drop_count: 16
normal_success_delta: 0.0
normal_margin_mean_delta: +0.000386112488785186
margin_gap_mean_delta: +0.00012055396862334193
actor_inputs_changed: false
```

This is localized wrong-history proof washout, not normal-branch collision
regression. Candidate B's normal branch is not harmed on the aggregate surface;
one rejected-history branch became too safe.

## Generalization And Behavior

Fresh public and moderate-OOD checks all pass:

```text
fresh_public seed 102100: success unchanged 0.90234375, margin +0.00022690287699966838
fresh_public seed 102101: success unchanged 0.90234375, margin +0.000224858100944747
moderate_ood seed 102120: success unchanged 0.6640625, margin +0.00024997688947303587
```

Behavior/ablation seeds all pass:

```text
9505: candidate 0.8625, reset 0.85, zero_all 0.8
9506: candidate 0.8625, reset 0.85, zero_all 0.8
102130: candidate 0.9125, reset 0.875, zero_all 0.8625
102131: candidate 0.9125, reset 0.875, zero_all 0.8625
```

The normal >= reset >= zero-all ordering is retained for all behavior rows.

## Interpretation

M1026 confirms that a smoke-scale PPO proposal from Candidate B is trainable and
does not broadly damage fresh public, moderate-OOD, or behavior-ablation
metrics.

It also confirms that the guarded PPO recipe is still not promotion-safe:

```text
exact temporal retention can pass while a current-family wrong-history proof
row is washed out.
```

So the next step should not be longer PPO and should not be scalar auxiliary
coefficient tuning. The next step should audit the M267/M264 failed row and
decide whether an exact post-PPO repair/projection route can restore
wrong-history proof while retaining the useful broad PPO movement.

## Decision

```text
candidate_b_guarded_ppo_proof_washout_route_to_exact_repair_projection_audit
```

Next milestone:

```text
m1027-v4-public-base-candidate-b-guarded-ppo-proof-washout-audit
```
