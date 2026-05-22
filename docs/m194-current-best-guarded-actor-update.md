# M194 Current-Best Guarded Actor Update

M193 admitted the refreshed M192 current-family boundary surface as
replay-aligned objective data. M194 tests one tiny actor-coupling update from
the current-best M189 checkpoint. This is not PPO.

## Setup

Initial checkpoint:

```text
runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt
```

Objective corpus:

```text
runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.npz
```

Train scope:

```text
actor_coupling only
```

The response encoder, context encoder, GRU, critic, and `log_std` remain
effectively fixed under this recipe. Actor inputs are unchanged.

## Actor Update

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt \
  --snippet-npz runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.npz \
  --device cpu \
  --steps 20 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 9850 \
  --grad-clip-norm 1.0 \
  --log-interval 5 \
  --eval-batch-size 64 \
  --eval-batches 30 \
  --eval-seed 0 \
  --train-scope actor_coupling \
  --action-anchor-checkpoint runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt \
  --action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --action-anchor-coef 100.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed 9850 \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --run-dir runs/m194_m189_actor_coupling_anchor100_s20_seed9850
```

Result:

| Metric | Value |
| --- | ---: |
| Before loss mean | 0.162431 |
| After loss mean | 0.160765 |
| Loss mean improvement | 0.001666 |
| After action-anchor MSE | 0.000014546 |
| Objective sanity | true |

Candidate:

```text
runs/m194_m189_actor_coupling_anchor100_s20_seed9850/optimized_checkpoint.pt
```

## Independent Fixed Eval

Artifact:

```text
runs/m194_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m189_5193 | 0.160647 |
| m194_s20 | 0.159008 |

Independent fixed-batch improvement:

```text
0.001639
```

## Replay Gates

| Corpus | Rows | Baseline drops | M194 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 | 16 | -0.003064 | -0.000074 | true |
| M183 M170 | 17 | 17 | 17 | -0.003059 | -0.000069 | true |
| M193 M189 | 14 | 14 | 14 | -0.002708 | -0.000110 | true |

Artifacts:

- `runs/m194_m183_m168_replay_gate_seed9510`
- `runs/m194_m183_m170_replay_gate_seed9510`
- `runs/m194_m193_m189_replay_gate_seed9630`

M194 preserves both old M183 replay surfaces and the refreshed M193 replay
surface. Margins move downward but stay inside the registered thresholds.

## Behavior Retention

Artifacts:

- `runs/m194_behavior_gate_seed9505`
- `runs/m194_behavior_gate_seed9506`

| Seed | Policy | Success | Collision | Mean margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m189_5193 | 0.8625 | 0.1375 | 1.838230 |
| 9505 | m194_s20 | 0.8625 | 0.1375 | 1.835998 |
| 9505 | m194_s20_reset | 0.8500 | 0.1250 | 1.834812 |
| 9505 | m194_s20_zero_all | 0.8000 | 0.1250 | 1.852303 |
| 9506 | m189_5193 | 0.8625 | 0.1375 | 1.855994 |
| 9506 | m194_s20 | 0.8625 | 0.1375 | 1.853627 |
| 9506 | m194_s20_reset | 0.8500 | 0.1250 | 1.851098 |
| 9506 | m194_s20_zero_all | 0.8000 | 0.1250 | 1.870296 |

Behavior success is retained on the M191 fresh seeds. Reset and zero-all
response ablations still degrade success.

## Protected Key

Artifact:

```text
runs/m194_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m189_5193 | 1 / 1 | true |
| m194_s20 | 1 / 1 | true |

Protected key `9944|perturbed|28|28` is retained.

## Decision

M194 is positive as a single-seed guarded actor update:

- M193 fixed objective improves on training and independent eval seeds;
- old M183 and new M193 replay gates pass;
- behavior success is retained on seeds `9505` and `9506`;
- protected key passes;
- response-history ablation degradation remains visible.

However, this is still one actor-update seed. It should not immediately admit
PPO.

Decision:

```text
admit_actor_update_repeat
```

Next step:

```text
m195-current-best-actor-update-repeat
```

M195 should repeat the same anchored actor-update recipe from M189 on fresh
seeds before any guarded PPO smoke.
