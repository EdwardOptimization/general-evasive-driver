# M568 Scaled BC Training

## Purpose

M568 trains the scaled L3 behavior-cloning seed family from the M567 non-public
train/validation corpora.

This milestone trains offline action-MSE checkpoints only. It does not run
route-screen, PPO, public diagnostics, or promotion.

## Commands

Each run used:

```text
train corpus = runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz
val corpus   = runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz
student env  = configs/ppo_m541_matched_l3_variance_4096.json
epochs       = 25
learning_rate = 0.001
hidden_size = 64
device = cpu
```

Run dirs:

```text
runs/m568_scaled_l3_bc_seed5660
runs/m568_scaled_l3_bc_seed5661
runs/m568_scaled_l3_bc_seed5662
```

## MSE Result

| Seed | Initial Train MSE | Final Train MSE | Train Delta | Initial Val MSE | Final Val MSE | Val Delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5660 | 0.027889 | 0.00003598 | -0.027853 | 0.027939 | 0.00003675 | -0.027902 |
| 5661 | 0.075615 | 0.00000808 | -0.075607 | 0.075560 | 0.00000855 | -0.075552 |
| 5662 | 0.044668 | 0.00001886 | -0.044649 | 0.044779 | 0.00001963 | -0.044759 |

All three seeds improve train and validation MSE.

## Metadata Check

All three checkpoints report:

```text
obs_dim = 72
actor_encoder = human_view_online_gru
actor_history_length = 1
is_online_recurrent = true
history_baseline.level = L3_online_gru
input_contract = P0_human_view_no_wheel_no_oracle
ppo_used = false
promoted = false
```

## Interpretation

The scaled corpus does not expose an optimizer-seed fragility at the action-MSE
layer. The three seeds all converge to very low teacher-action MSE on both
train and validation corpora.

This does not prove closed-loop performance. M569 must run route-screen v2 on
fresh seed `18560` before any public diagnostic repeat or PPO continuation.

## Decision

```text
scaled_bc_training_pass_admit_m569_route_screen_selection
```

M568 passes because all three scaled BC seeds improve train/validation MSE and
preserve P0 L3 online-GRU checkpoint metadata without route-screen, PPO, public
diagnostics, or promotion.

## Next

```text
M569: route-screen v2 selection on fresh seed 18560.
```
