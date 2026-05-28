# M1352 Paper-Route Materialized Source-History Interpolation Preflight

## Summary

M1352 runs the exact plus two-surface replay preflight designed in M1351.

Result:

```text
materialized_source_history_interpolation_preflight_pass
```

Selected alpha:

```text
0.005
```

Selected checkpoint:

```text
runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/alpha_0_005.pt
```

This is not a promotion. It is a narrow trust-region preflight result showing
that the M1346 direction has a very small usable region.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_interpolation_preflight \
  --base-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --raw-checkpoint runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt \
  --corpus-run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --run-dir runs/m1352_materialized_source_history_interpolation_preflight \
  --device cpu \
  --alphas 0.005,0.01,0.02,0.05,0.1,0.2
```

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_materialized_source_history_interpolation_preflight.py
```

Result:

```text
3 passed
```

## Exact Tier

All six candidate alphas are exact-admitted:

```text
exact_candidate_count: 6 / 6
actor_inputs_changed: false for all
forbidden_parameter_mutation_detected: false for all
log_std_l2: 0.0 for all
```

Exact metrics:

| alpha | combined delta | group-min delta | eval-fold delta | both-dir groups | both-neg groups |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.005 | -0.031707 | +0.032248 | +0.029937 | 0 | 4 |
| 0.010 | -0.063395 | +0.064496 | +0.059871 | 0 | 4 |
| 0.020 | -0.126712 | +0.128975 | +0.119736 | 0 | 4 |
| 0.050 | -0.316172 | +0.322358 | +0.299286 | 0 | 4 |
| 0.100 | -0.630206 | +0.644513 | +0.598373 | 0 | 4 |
| 0.200 | -1.250839 | +1.277121 | +1.185753 | 0 | 4 |

The exact loss and group-min objective improve monotonically with alpha, but
small alphas do not yet create all-rows-both-directional groups.

## Replay Tier

M267/M264:

| alpha | gate | normal success delta | success-drop delta | normal margin delta | margin-gap delta |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0.005 | pass | 0.000000 | 0 | -0.000722 | -0.000106 |
| 0.010 | pass | 0.000000 | 0 | -0.001440 | -0.000209 |
| 0.020 | pass | 0.000000 | 0 | -0.002865 | -0.000412 |
| 0.050 | fail | -0.588235 | -10 | -0.007057 | -0.001480 |
| 0.100 | fail | -0.941176 | -16 | -0.013836 | -0.003693 |
| 0.200 | fail | -1.000000 | -17 | -0.013982 | -0.004007 |

M183/M170 was run only for alphas passing M267/M264:

| alpha | gate | normal success delta | success-drop delta | normal margin delta | margin-gap delta |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0.005 | pass | 0.000000 | 0 | -0.000844 | -0.000076 |
| 0.010 | fail | -0.294118 | -5 | -0.001684 | -0.000150 |
| 0.020 | fail | -0.823529 | -14 | -0.003354 | -0.000294 |

Therefore only `alpha=0.005` passes both replay preflight surfaces.

## Interpretation

Supported:

```text
The M1346 direction has a nonzero but very small trust-region-compatible alpha.
```

Supported:

```text
Closed-loop replay proof failure is amplitude-sensitive: M267/M264 tolerates up
to alpha 0.02, but M183/M170 only tolerates alpha 0.005.
```

Supported:

```text
Raw M1346 failed because it overshot the replay-safe trust region, not because
every infinitesimal move in the objective direction is invalid.
```

Not supported:

```text
The selected alpha is a promoted public base.
```

Not supported:

```text
The selected alpha is a strong policy improvement.
```

Not supported:

```text
The selected alpha proves closed-loop self-identification.
```

## Main Caveat

The selected `alpha=0.005` improves exact metrics only weakly:

```text
combined_loss_delta_vs_base: -0.0317072824
group_min_joint_margin_delta_vs_base: +0.0322478571
eval_fold_4_group_min_joint_margin_delta_vs_base: +0.0299366837
group_all_rows_both_directional_count: 0
```

This is enough to show a usable trust region exists, but not enough to claim
meaningful driver improvement. The next step must audit whether this tiny alpha
is worth carrying into limited repeat/full public replay or whether the objective
needs replay-aware retention terms before another update.

## Artifacts

```text
runs/m1352_materialized_source_history_interpolation_preflight/summary.json
runs/m1352_materialized_source_history_interpolation_preflight/alpha_summary.csv
runs/m1352_materialized_source_history_interpolation_preflight/candidate_checkpoints.csv
runs/m1352_materialized_source_history_interpolation_preflight/parameter_delta_rows.csv
runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/alpha_0_005.pt
```

## Decision

M1352 passes as a limited interpolation preflight and routes to result audit:

```text
m1353-paper-route-materialized-source-history-interpolation-replay-result-audit
```

Do not promote, run PPO, use private holdout, or claim driver performance from
this result.
