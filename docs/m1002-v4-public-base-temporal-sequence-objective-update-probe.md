# M1002 V4 Public Base Temporal Sequence Objective Update Probe

## Purpose

M1002 implements the exact-gated actor_mean-only temporal sequence objective
update designed in M1001.

It runs an objective-only update over the M997 corpus, evaluates interpolated
checkpoints by exact gates, and does not run PPO, public replay, or promotion.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_temporal_sequence_update_probe \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --metadata runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv \
  --base-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --epochs 200 \
  --seed 1002 \
  --lr 1e-4 \
  --grad-clip-norm 1.0 \
  --alphas 0.005,0.010,0.020,0.050,0.100,0.200,0.500,1.000 \
  --run-dir runs/m1002_v4_public_base_temporal_sequence_objective_update_probe \
  --device auto
```

## Result

```text
result_class: temporal_sequence_update_exact_candidate
row_count: 277
positive_row_count: 277
epochs: 200
seed: 1002
lr: 0.0001
raw_changed_parameter_names:
  actor_mean.bias
  actor_mean.weight
raw_actor_mean_changed: true
raw_non_actor_changed: false
exact_candidate_count: 5
training_started: true
ppo_used: false
promoted: false
```

The update obeys the trainable-surface contract:

```text
only actor_mean changed
encoders / GRU / fusion / critic / log_std unchanged
```

## Exact Candidates

Passing alphas:

```text
0.010
0.020
0.050
0.100
0.200
```

Rejected alphas:

```text
0.005: total-loss improvement below threshold
0.500: action drift and normal-retention gates fail
1.000: action drift and normal-retention gates fail
```

Saved candidate checkpoints:

```text
runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt
runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_02.pt
runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_05.pt
runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_1.pt
runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
```

## Best Exact Candidate

Best exact candidate by weighted total loss among gate-passing alphas:

```text
alpha: 0.200
checkpoint:
  runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt

weighted_total_loss: -0.907863
weighted_normal_sequence_nll: -1.371144
weighted_temporal_preference_loss: 0.463279
weighted_base_logp_anchor: 0.000008
weighted_logp_gap_mean: 0.758060
temporal_logp_gap_p10: 0.065254
temporal_logp_gap_p50: 0.507577
temporal_logp_gap_p90: 2.034285
candidate_action_l2_mean: 0.008939
candidate_action_l2_max: 0.036729
total_loss_improvement: 0.026450
normal_nll_regression: 0.001870
pref_loss_regression: -0.028322
gap_regression: -0.117954
gap_p10_regression: -0.011273
```

All exact gates pass for alpha `0.200`:

```text
total_loss_pass: true
normal_nll_pass: true
pref_loss_pass: true
gap_pass: true
gap_p10_pass: true
action_mean_pass: true
action_max_pass: true
exact_gate_pass: true
```

The negative gap regressions mean the candidate improves the temporal gap
relative to the base rather than shrinking it.

## Interpretation

M1002 shows that the M997 temporal sequence objective is trainable inside a
small actor_mean-only trust region:

```text
exact objective improves;
temporal preference loss improves;
temporal logp gap improves;
action drift remains small at alpha <= 0.2;
non-actor parameters remain unchanged.
```

This is still only an exact objective candidate. It is not yet evidence that
closed-loop public replay/proof gates survive.

## Blocked Claims

Do not claim:

```text
the checkpoint is promoted;
PPO is ready;
public replay gates passed;
cross-fault wrong-history self-ID is proven;
diagnostic cross-fault rows became positive targets.
```

## Decision

```text
temporal_sequence_update_exact_candidate_route_to_public_replay_gate_design
```

Next:

```text
m1003-v4-public-base-temporal-sequence-update-public-replay-gate-design
```

M1003 should design the no-training public replay gate for the M1002 exact
candidates before any candidate can be used for PPO or promotion.
