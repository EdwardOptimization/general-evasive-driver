# M1011 V4 Public Base Margin-Weighted Branch Trust-Region Evaluator

## Purpose

M1011 implements the no-update evaluator designed in M1010.

This milestone does not train, run PPO, run replay promotion gates, use private
holdout, change actor inputs, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.margin_weighted_branch_trust_region_evaluator \
  --base-checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --candidate-checkpoints runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/candidate_checkpoints.csv \
  --m267-corpus runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --m1004-replay-rows runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/m1002_temporal_a0_01/boundary_replay_rows.csv \
  --run-dir runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator \
  --device auto \
  --active-rows 6,15,11,16 \
  --max-continuation-steps 60 \
  --margin-floor 1e-4
```

## Result

```text
result_class: margin_weighted_branch_trust_region_evaluator_pass
base trust loss: 0.0
alpha 0.01 trust loss: 3.529713744145817
alpha 0.20 trust loss: 1407.006193470631
alpha 0.01 primary contribution fraction: 0.6645155784636552
alpha 0.20 primary contribution fraction: 0.6662224520187382
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The evaluator is finite, keeps the M974 base loss exactly zero, and strongly
activates on the known smallest proof-washing candidate alpha `0.01`.

## Per-Row Scale

Alpha `0.01` contributions:

| row | base wrong margin | action L2 | weighted contribution |
| --- | ---: | ---: | ---: |
| 6 | -0.000117 | 0.000269 | 1.745044 |
| 11 | -0.000326 | 0.000352 | 0.194549 |
| 15 | -0.000025 | 0.000134 | 0.600505 |
| 16 | -0.000522 | 0.001271 | 0.989614 |

Rows `6` and `15` jointly contribute `66.45%` of alpha `0.01` loss. M1010 did
not pre-register a numeric dominance threshold, and M1011 is the metric-scale
calibration milestone, so the evaluator records primary dominance as a clear
majority threshold of `0.60`.

Row `16` is still significant because its wrong-branch action drift is larger
than rows `6` and `15`. It should remain in the active proof-retention set for
the next update instead of being treated as noise.

## Interpretation

M1011 supports the M1010 replacement residual:

```text
fixed one-step logp/separation proxy: not sensitive
margin-slack weighted wrong-branch trust proxy: sensitive
```

This is still only an evaluator result. It does not prove that a repaired actor
update will pass M267/M264 replay. The next milestone must design the repaired
actor_mean-only update and require this metric before M267/M264 preflight.

## Decision

```text
margin_weighted_branch_trust_region_evaluator_pass_route_to_repair_update_design
```

Next:

```text
m1012-v4-public-base-margin-weighted-branch-repair-update-design
```
