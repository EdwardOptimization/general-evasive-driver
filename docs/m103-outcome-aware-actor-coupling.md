# M103 Outcome-Aware Actor Coupling

M103 tests the next hypothesis after M101/M102:

```text
action-distance-only actor coupling is too broad;
actor coupling should be applied on snippets where normal history actually
beats an intervention in clearance or success.
```

M101 produced the first clear behavior-level reset/zero-response degradation,
but lost braking/lateral hidden-envelope retention. M102 recovered the
hidden-envelope signal, but behavior dependence disappeared. M103 therefore
builds outcome-sensitive normal-vs-ablation snippets and fits the actor/fusion
layers from the M102 checkpoint on those snippets.

## Implementation

Added:

```text
src/autodrift/history_ablation_snippets.py
tests/test_history_ablation_snippets.py
```

Updated:

```text
src/autodrift/outcome_intervention_optimize.py
tests/test_outcome_intervention_optimize.py
```

`history_ablation_snippets` rolls out a recurrent checkpoint from a decision
snapshot under:

```text
normal
reset
zero_response
```

It records accepted rows when normal history has better success or a clearance
margin gap over the intervention. The current NPZ export includes only `reset`
examples because `outcome_weighted_intervention_loss` is a preferred-hidden
versus rejected-hidden objective. `zero_response` rows are logged as diagnostics
but are not yet expressible by that loss because they change observation values,
not only recurrent hidden.

`outcome_intervention_optimize` now supports:

```text
--train-scope actor_coupling
```

That scope freezes the response encoder, online GRU, context encoder, critic,
and log standard deviation. It trains only:

```text
response_context_fusion
actor_mean
```

This keeps M102's response-hidden encoder fixed and tests whether the actor can
use the existing recurrent belief differently.

## Snippet Mining

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.history_ablation_snippets \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt \
  --episodes 30 \
  --seed 9600 \
  --device cpu \
  --target-obstacle-distances 8,10,12 \
  --min-probe-steps 10 \
  --max-probe-steps 180 \
  --allow-pre-friction-snapshot \
  --max-continuation-steps 0 \
  --min-margin-gap 0.01 \
  --min-normal-margin 0.0 \
  --outcome-export-min-margin-gap 0.0 \
  --outcome-export-boundary-margin-scale 0.20 \
  --top-k 100 \
  --run-dir runs/m103_history_ablation_snippets_m101_smoke_seed9600
```

Artifacts:

```text
runs/m103_history_ablation_snippets_m101_smoke_seed9600/history_ablation_candidates.csv
runs/m103_history_ablation_snippets_m101_smoke_seed9600/replays.csv
runs/m103_history_ablation_snippets_m101_smoke_seed9600/history_ablation_outcome_snippets.csv
runs/m103_history_ablation_snippets_m101_smoke_seed9600/outcome_intervention_snippets.csv
runs/m103_history_ablation_snippets_m101_smoke_seed9600/outcome_intervention_snippets.npz
runs/m103_history_ablation_snippets_m101_smoke_seed9600/summary.json
```

Result:

| metric | value |
| --- | ---: |
| candidates | 180 |
| accepted outcome-sensitive rows | 87 |
| reset accepted rows | 55 |
| zero-response accepted rows | 32 |
| exported outcome snippets | 57 |
| weight sum | 0.284162 |
| max margin gap | 0.155553 |

This is stronger than the early M78-style snippet corpus and captures the M101
reset-sensitive states.

## Fixed-Batch Evaluation

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m103_history_ablation_snippets_m101_smoke_seed9600/outcome_intervention_snippets.npz \
  --checkpoint-policy m98=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --checkpoint-policy m101=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m103=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt \
  --device cpu \
  --batch-size 128 \
  --batches 20 \
  --seed 0 \
  --logprob-margin 0.05 \
  --run-dir runs/m103_outcome_actor_coupling_eval_seed0
```

| policy | loss mean |
| --- | ---: |
| M98 | 0.111505 |
| M101 | 0.000366 |
| M102 | 0.045645 |
| M103 seed9610 | 0.000102 |

The M103 snippets distinguish M101 from M98/M102 and can be optimized from M102
to near-zero loss.

## Objective Optimization

Common command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --snippet-npz runs/m103_history_ablation_snippets_m101_smoke_seed9600/outcome_intervention_snippets.npz \
  --device cpu \
  --steps 200 \
  --batch-size 256 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 9610 \
  --grad-clip-norm 1.0 \
  --log-interval 20 \
  --eval-batch-size 128 \
  --eval-batches 20 \
  --eval-seed 0 \
  --train-scope actor_coupling \
  --run-dir runs/m103_outcome_actor_coupling_m102_seed9610
```

Repeated seeds:

```text
9610
9611
9612
```

All three seeds produced the same model state. The checkpoint file hashes differ
only because checkpoint metadata records the seed.

| seed | before loss | after loss | improvement | objective pass |
| ---: | ---: | ---: | ---: | --- |
| 9610 | 0.045645 | 0.000102 | 0.045543 | yes |
| 9611 | 0.045645 | 0.000102 | 0.045543 | yes |
| 9612 | 0.045645 | 0.000102 | 0.045543 | yes |

The fixed-batch outcome objective itself is not the blocker.

## Behavior Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 80 \
  --seed 9500 \
  --policies heuristic \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m98_9480=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --checkpoint-policy m101_9530=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt \
  --checkpoint-policy m102_9550=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m103_9610=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt \
  --checkpoint-policy m103_9610_reset=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m103_9610_zero_current=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m103_9610_zero_all=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m103_9610_noact=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m103_outcome_actor_coupling_behavior_gate_seed9500
```

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.2250 | 0.7750 | 37.659345 | 0.099179 | -0.309701 |
| M62 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| M98 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| M101 | 0.8625 | 0.1375 | 65.908976 | 1.864457 | -0.111205 |
| M102 | 0.8625 | 0.1375 | 65.527537 | 1.854237 | -0.113690 |
| M103 | 0.8750 | 0.1250 | 66.955627 | 1.844280 | -0.118577 |
| M103 no-action-history | 0.8625 | 0.1375 | 65.900598 | 1.852600 | -0.120493 |
| M103 reset-hidden | 0.8750 | 0.1250 | 65.149515 | 1.812960 | -0.162618 |
| M103 zero-current-response | 0.8500 | 0.1500 | 64.279682 | 1.840047 | -0.150150 |
| M103 zero-all-response | 0.8500 | 0.1500 | 64.279682 | 1.840047 | -0.150150 |

Interpretation:

- normal behavior retention passes and success slightly improves over M62/M98;
- zero-response drops from `0.8750` to `0.8500`, so current response features
  matter somewhat again;
- reset hidden does not degrade success, so recurrent hidden dependence is not
  proven;
- no-action-history does not reduce success, so previous-command history is not
  behavior-critical on this gate.

## Hidden-Envelope Probe

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9510 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m103_outcome_actor_coupling_hidden_envelope_probe_seed9510
```

| target | response hidden R2 | reset hidden R2 | normal minus reset R2 |
| --- | ---: | ---: | ---: |
| braking | 0.611472 | 0.682268 | -0.070796 |
| lateral accel | 0.222348 | 0.332965 | -0.110616 |
| yaw | 0.427256 | 0.333901 | 0.093355 |

M103 keeps a small yaw hidden-history lift, but it fails the braking and lateral
hidden-envelope retention criteria. Because M103 trained only actor/fusion
layers, this failure is probably caused by changed closed-loop trajectory
distribution rather than response-encoder parameter drift.

## Decision

M103 is a mixed negative result.

What passed:

- outcome-sensitive snippet mining now works;
- the fixed-batch outcome objective can be optimized from M102 to near-zero;
- normal behavior retention passes and success slightly improves;
- zero-response ablation degrades success a little.

What failed:

- reset-hidden behavior does not degrade;
- no-action-history remains behavior-neutral;
- braking and lateral hidden-envelope retention fail;
- fitting M101 reset-sensitive snippets from an M102 start is not enough to
  produce a self-identifying recurrent driver.

Do not promote M103 to PPO continuation.

The next step should be M105: retention-constrained outcome coupling. The
objective should combine outcome-sensitive pressure with a broad behavior or
hidden-envelope retention guard, instead of fitting the reset snippets alone.
