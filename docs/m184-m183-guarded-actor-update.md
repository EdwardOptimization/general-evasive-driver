# M184 M183 Guarded Actor Update

M183 admitted the M182 source-diverse boundary proof surface as replay-aligned
fixed objective data. M184 tests the smallest safe actor-coupling step from the
strict M168 branch before any PPO continuation.

This milestone is a guarded actor update, not PPO.

## Setup

Initial checkpoint:

```text
runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt
```

M183 corpus:

```text
runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
```

Actor update scope:

```text
train_scope = actor_coupling
trainable   = response_context_fusion + actor_mean
frozen      = response encoder, context encoder, GRU, critic, log_std
```

Actor inputs are unchanged. M183 outcome labels and geometry are training-time
artifacts only.

## Candidate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --snippet-npz runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz \
  --device cpu \
  --steps 20 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 9840 \
  --grad-clip-norm 1.0 \
  --log-interval 5 \
  --eval-batch-size 64 \
  --eval-batches 30 \
  --eval-seed 0 \
  --train-scope actor_coupling \
  --action-anchor-checkpoint runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --action-anchor-coef 100.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed 9840 \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --run-dir runs/m184_m168_actor_coupling_anchor100_s20_seed9840
```

Result:

| Metric | Value |
| --- | ---: |
| before loss mean | 0.176441 |
| after loss mean | 0.175359 |
| loss mean improvement | 0.001083 |
| after action-anchor MSE | 0.000005879 |
| objective sanity | true |

Candidate:

```text
runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt
```

## Independent Fixed-Batch Eval

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --device cpu \
  --batch-size 64 \
  --batches 50 \
  --seed 37 \
  --logprob-margin 0.05 \
  --run-dir runs/m184_fixed_batch_outcome_eval_s20_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m168_strict | 0.172549 |
| m184_s20 | 0.171518 |

Independent improvement:

```text
0.001031
```

## Boundary Replay

M184 must preserve the M183 fixed replay surfaces before any PPO.

M168 corpus command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --corpus-csv runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m168_strict \
  --candidate-policy m184_s20 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m184_m168_boundary_replay_gate_seed9510
```

M170 corpus command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --corpus-csv runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m170_split \
  --candidate-policy m184_s20 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m184_m170_boundary_replay_gate_seed9510
```

| Corpus | Rows | Baseline drops | M184 drops | Normal success delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M168 strict | 16 | 16 | 16 | 0.000000 | -0.000057 | true |
| M170 split | 17 | 17 | 17 | 0.000000 | -0.000172 | true |

M184 preserves both M183 replay surfaces.

## Behavior Retention

Commands use `configs/m121_human_view_zero_obstacle_relvel.json`, 80 episodes,
and compare M168, M184, and M184 response-history ablations.

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m168_strict | 0.8625 | 0.1375 | 1.846380 |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m184_s20_reset | 0.8500 | 0.1250 | 1.842272 |
| m184_s20_zero_all | 0.8000 | 0.1250 | 1.856674 |
| m184_s20_noact | 0.8625 | 0.1375 | 1.847464 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m168_strict | 0.8625 | 0.1375 | 1.853938 |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m184_s20_reset | 0.8500 | 0.1250 | 1.850425 |
| m184_s20_zero_all | 0.8000 | 0.1250 | 1.868669 |
| m184_s20_noact | 0.8625 | 0.1375 | 1.856373 |

Behavior retention passes and response ablation degradation is preserved.

## Protected Key

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv \
  --case-key '9944|perturbed|28|28' \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --reference-policy m168_strict \
  --device cpu \
  --run-dir runs/m184_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m168_strict | 1 / 1 | true |
| m184_s20 | 1 / 1 | true |

As usual, `guard_validated=false` only means no non-reference policy failed in
this run. The relevant evidence is `m184_s20 policy_pass=true`.

## Decision

M184 is positive as a guarded actor-update milestone.

What passed:

- fixed M183 objective improves on the training eval and an independent eval
  seed;
- action-anchor drift is very small;
- M168 and M170 M183 boundary replay surfaces retain all success drops;
- behavior success matches M168 on seeds `9503` and `9504`;
- reset and zero-all ablations still degrade success;
- protected key `9944|perturbed|28|28` passes.

Decision:

```text
admit_guarded_ppo_smoke
```

Next step: run only a tiny guarded PPO smoke from M184. The PPO smoke must be
rejected if it weakens M183 boundary replay, behavior retention, or the
protected key.
