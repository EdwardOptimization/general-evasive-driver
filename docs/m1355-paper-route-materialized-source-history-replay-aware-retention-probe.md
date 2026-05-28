# M1355 Paper-Route Materialized Source-History Replay-Aware Retention Probe

## Summary

M1355 runs the no-PPO replay-aware retention probe designed in M1354.

Result:

```text
materialized_source_history_replay_aware_retention_m267_proof_washout
```

Failure taxonomy:

```text
proof_washout
```

This is a negative but useful result. The retained update strongly improves the
fixed source-history objective and preserves normal-history M267/M264 success,
but it fails the self-ID replay proof because five wrong-history branches become
successful.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_replay_aware_retention_probe \
  --run-dir runs/m1355_materialized_source_history_replay_aware_retention_probe \
  --device cpu
```

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_materialized_source_history_replay_aware_retention_probe.py
```

Result:

```text
3 passed
```

## Structural Checks

The retained update preserves the mutation and input contract:

```text
checkpoint_contract: canonical_72_human_view_online_recurrent
trainable_scope: response_context_fusion_plus_actor_mean
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
actor_input_contract_changed: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Changed parameters:

```text
actor_mean.bias
actor_mean.weight
response_context_fusion.0.bias
response_context_fusion.0.weight
```

Retention surface:

```text
fragile_rows: 29
trajectory_rows: 1409
required_row16_present: true
weight_min: 1.031501
weight_max: 7.491132
weight_mean: 2.670132
```

## Exact Metrics

The fixed objective improves strongly:

```text
combined_loss_delta: -4.6874377849
full_group_min_joint_margin_delta: +5.2968078983
eval_fold_group_min_joint_margin_delta: +4.8873970864
beat_alpha005_exact_lift: true
```

Against the M1352 diagnostic alpha:

```text
alpha0.005 combined delta: -0.0317072824
alpha0.005 group-min delta: +0.0322478571
alpha0.005 eval-fold delta: +0.0299366837
```

So the retained update solves the fixed metric side of the problem. The failure
is not weak source-history optimization.

## Replay Result

M267/M264 fails:

```text
gate_pass: false
normal_success_delta: 0.0
normal_margin_mean_delta: +0.0010805264
margin_gap_mean_delta: -0.0004139157
success_drop_count_delta: -5
baseline_success_drop_count: 17
candidate_success_drop_count: 12
candidate_wrong_history_success_rate: 0.2941176471
```

The normal branch is retained. The proof loss is specifically that wrong-history
rollouts become successful on five rows:

| row_id | base normal margin | candidate normal margin | base wrong margin | candidate wrong margin | base gap | candidate gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 0.011198 | 0.012583 | -0.001194 | 0.000912 | 0.012392 | 0.011671 |
| 10 | 0.005928 | 0.007634 | -0.002576 | 0.000580 | 0.008504 | 0.007055 |
| 13 | 0.005664 | 0.007567 | -0.001830 | 0.001706 | 0.007494 | 0.005861 |
| 15 | 0.006786 | 0.007025 | -0.000260 | 0.000211 | 0.007046 | 0.006813 |
| 16 | 0.005371 | 0.007307 | -0.001448 | 0.001909 | 0.006819 | 0.005398 |

M183/M170 is skipped by the pre-registered ordering because M267/M264 fails
first.

## Interpretation

Supported:

```text
Normal-branch replay retention alone is insufficient.
```

Supported:

```text
The source-history objective plus normal-trajectory retention can improve
normal safety while also making wrong-history behavior safe, which destroys the
success-drop proof.
```

Supported:

```text
The next objective must be branch-asymmetric: preserve or shape both the
correct-history success branch and the wrong-history rejected/failure branch.
```

Falsified:

```text
Adding normal replay retention is enough to make the M1346 direction replay-safe.
```

Unsupported:

```text
This checkpoint is promotable.
```

Unsupported:

```text
This is driver-performance evidence or strong self-identification evidence.
```

## Decision

Do not promote.

Do not run full replay.

Do not continue local tuning in this branch.

Route to the cadence-required synthesis:

```text
m1356-paper-route-materialized-source-history-pair-group-update-branch-synthesis
```

The synthesis should decide whether to pivot to a bidirectional active-set
objective that explicitly protects wrong-history failure/rejected behavior, or
whether to stop this source-history pair-group update branch.

## Artifacts

```text
runs/m1355_materialized_source_history_replay_aware_retention_probe/summary.json
runs/m1355_materialized_source_history_replay_aware_retention_probe/checkpoints/raw_replay_aware_retention_update.pt
runs/m1355_materialized_source_history_replay_aware_retention_probe/retention_surface/summary.json
runs/m1355_materialized_source_history_replay_aware_retention_probe/retention_surface/fragile_rows.csv
runs/m1355_materialized_source_history_replay_aware_retention_probe/replay/m267_m264/summary.json
```

## Guardrails

No PPO, promotion, private holdout, threshold relaxation, full replay,
actor-input expansion, high-fidelity claim, paper-level claim, or closed-loop
self-identification claim occurred.
