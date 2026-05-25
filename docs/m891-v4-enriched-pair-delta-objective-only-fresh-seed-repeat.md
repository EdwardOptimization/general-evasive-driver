# M891 V4 Enriched Pair-Delta Objective-Only Fresh-Seed Repeat

## Purpose

M891 repeats the M886 no-PPO objective-only probe with a fresh
optimizer/minibatch seed.

Changed:

```text
seed: 10886 -> 10887
```

Unchanged:

```text
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
steps: 32
learning_rate: 0.000001
batch_size: 32
action_anchor_coef: 0.1
parameter_anchor_coef: 0.0001
exact_holdout_regression_tolerance: 0.0001
train_scope: actor_coupling
```

No PPO, promotion, actor input change, or residual-head update is allowed.

## Run

```text
runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887
```

## Result

Summary:

```text
expected_rows: 247
tensor_rows_reconstructed: 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
raw_train_weighted_loss_delta: -0.0008406196871111327
exact_admissible_alpha_count: 7
best_exact_admissible_alpha: 0.1
best_exact_admissible_train_delta: -0.00008399784564971924
exact_losses_finite: true
training_nonfinite: false
actor_input_contract_changed: false
residual_head_changed: false
ppo_used: false
promoted: false
result_class: v4_enriched_pair_delta_objective_only_probe_exact_admissible
```

Interpolation:

```text
alpha    train_delta          max_holdout_regression   exact_admissible
0.001    -0.0000008493661880  -0.0000003576278687      true
0.0025   -0.0000021467285771  -0.0000007947285969      true
0.005    -0.0000041891490259  -0.0000016291936238      true
0.01     -0.0000084552072710  -0.0000034570693970      true
0.02     -0.0000167767847739  -0.0000068346659343      true
0.05     -0.0000420472314282  -0.0000173250834148      true
0.10     -0.0000839978456497  -0.0000346501668294      true
```

Action drift remains tiny:

```text
raw_candidate all action_l2_mean: 0.0012005468574069773
alpha_0_1 all action_l2_mean: 0.00012005468574069777
```

## Interpretation

M891 reproduces the M886 exact-admissible objective-only result under a fresh
optimizer/minibatch seed.

This supports:

```text
The small enriched pair-delta objective-only direction is not unique to the
M886 seed-10886 minibatch ordering.
```

It still does not prove:

```text
closed-loop replay retention for the fresh repeat
generalization
driver performance improvement
PPO safety
promotion readiness
```

## Decision

Decision:

```text
v4_enriched_pair_delta_objective_only_fresh_seed_repeat_exact_admissible
```

Next:

```text
m892-v4-enriched-pair-delta-objective-only-fresh-seed-repeat-audit
```

M892 should decide whether to run replay/proof gates for the M891 alpha `0.1`
candidate or require a second fresh-seed repeat first.
