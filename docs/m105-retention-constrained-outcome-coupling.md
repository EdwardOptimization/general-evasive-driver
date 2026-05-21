# M105 Retention-Constrained Outcome Coupling

M105 tests the next hypothesis after M103:

```text
outcome-sensitive actor coupling is useful, but it needs a broad behavior
retention anchor so that fitting reset-sensitive snippets does not erase the
hidden-envelope belief learned by M98/M102.
```

M103 proved that the M103 outcome snippets are optimizable from M102, but the
result was mixed negative: reset-hidden behavior did not degrade and
braking/lateral hidden-envelope retention regressed. M105 keeps the same
deployable human-view actor contract and adds a training-time action-retention
anchor on a broader M102 rollout batch.

## Implementation

Updated:

```text
src/autodrift/outcome_intervention_optimize.py
tests/test_outcome_intervention_optimize.py
```

`outcome_intervention_optimize` now supports:

```text
--action-anchor-checkpoint
--action-anchor-env-config
--action-anchor-coef
--action-anchor-episodes
--action-anchor-seed
--action-anchor-horizon-steps
--action-anchor-sample-stride
--action-anchor-max-samples
--action-anchor-batch-size
```

When `--action-anchor-coef > 0`, the optimizer:

1. loads a frozen reference checkpoint;
2. collects a rollout batch using the same hidden-envelope sampling harness;
3. records reference deterministic action means at sampled positions;
4. trains with:

```text
loss = outcome_intervention_loss
     + action_anchor_coef * action_anchor_mse
```

The current M105 run trains only:

```text
response_context_fusion
actor_mean
```

It does not change actor inputs, does not add hidden physics labels, and does
not train the response encoder or online GRU.

## Objective Optimization

Common command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.outcome_intervention_optimize \
  --init-checkpoint runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --snippet-npz runs/m103_history_ablation_snippets_m101_smoke_seed9600/outcome_intervention_snippets.npz \
  --device cpu \
  --steps 120 \
  --batch-size 256 \
  --learning-rate 0.0001 \
  --logprob-margin 0.05 \
  --seed 9710 \
  --grad-clip-norm 1.0 \
  --log-interval 20 \
  --eval-batch-size 128 \
  --eval-batches 20 \
  --eval-seed 0 \
  --train-scope actor_coupling \
  --action-anchor-checkpoint runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --action-anchor-env-config configs/ppo_m24_human_view_gru_driver.json \
  --action-anchor-coef 10.0 \
  --action-anchor-episodes 30 \
  --action-anchor-seed 9710 \
  --action-anchor-horizon-steps 15 \
  --action-anchor-sample-stride 3 \
  --action-anchor-max-samples 800 \
  --action-anchor-batch-size 256 \
  --run-dir runs/m105_anchor10_outcome_coupling_smoke_seed9710
```

Repeated seeds:

```text
9710
9711
9712
```

| seed | before outcome loss | after outcome loss | improvement | after anchor MSE | objective pass |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9710 | 0.045645 | 0.002708 | 0.042937 | 0.000281 | yes |
| 9711 | 0.045645 | 0.002663 | 0.042981 | 0.000276 | yes |
| 9712 | 0.045645 | 0.002758 | 0.042886 | 0.000264 | yes |

The anchor prevents the optimizer from collapsing into a broad action rewrite
while still reducing the M103 outcome-intervention loss by about `0.043`.

Artifacts:

```text
runs/m105_anchor10_outcome_coupling_smoke_seed9710/summary.json
runs/m105_anchor10_outcome_coupling_smoke_seed9711/summary.json
runs/m105_anchor10_outcome_coupling_smoke_seed9712/summary.json
```

## Behavior Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 80 \
  --seed 9500 \
  --policies heuristic \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102_9550=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m103_9610=runs/m103_outcome_actor_coupling_m102_seed9610/optimized_checkpoint.pt \
  --checkpoint-policy m105_a10=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --checkpoint-policy m105_a10_reset=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m105_a10_zero_current=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m105_a10_zero_all=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m105_a10_noact=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m105_anchor10_behavior_gate_seed9500
```

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.2250 | 0.7750 | 37.659345 | 0.099179 | -0.309701 |
| M62 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| M102 | 0.8625 | 0.1375 | 65.527537 | 1.854237 | -0.113690 |
| M103 | 0.8750 | 0.1250 | 66.955627 | 1.844280 | -0.118577 |
| M105 anchor10 | 0.8625 | 0.1375 | 65.440304 | 1.854093 | -0.111374 |
| M105 no-action-history | 0.8625 | 0.1375 | 64.597540 | 1.862572 | -0.113513 |
| M105 reset-hidden | 0.8500 | 0.1500 | 64.134341 | 1.853825 | -0.143508 |
| M105 zero-current-response | 0.8250 | 0.1750 | 62.242646 | 1.864090 | -0.145839 |
| M105 zero-all-response | 0.8250 | 0.1750 | 62.242646 | 1.864090 | -0.145839 |

This is the first M101-M105 result where normal behavior retention passes and
both reset-hidden and zero-response ablations reduce success on the same
behavior gate. No-action-history is still behavior-neutral on this gate.

## Hidden-Envelope Probe

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9510 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m105_anchor10_hidden_envelope_probe_seed9510
```

| target | response hidden R2 | reset hidden R2 | response-minus-reset R2 |
| --- | ---: | ---: | ---: |
| future braking deceleration | 0.546640 | 0.335242 | 0.211398 |
| future lateral accel response | 0.292850 | -0.264276 | 0.557126 |
| future yaw response | 0.263177 | 0.230063 | 0.033114 |

M105 restores positive response-hidden-minus-reset lift on braking, lateral,
and yaw for the tested seed. This fixes the M103 hidden-envelope regression on
the same probe setup.

## Decision

M105 is a qualified positive objective result:

- objective repeats are stable across seeds `9710`, `9711`, and `9712`;
- broad action retention remains tight, with after-anchor MSE around `2.6e-4`
  to `2.8e-4`;
- normal behavior retention matches M62 on the 80-seed gate;
- reset-hidden and zero-response ablations now reduce behavior success;
- hidden-envelope retention is positive for braking, lateral, and yaw.

M105 is not yet a fully admitted driver checkpoint. The current evidence is
still limited to one full behavior/probe gate on the `9710` checkpoint. Before
PPO continuation or a stronger claim, the next task should repeat behavior and
hidden-envelope gates across the `9711` and `9712` optimized checkpoints and
add stronger history interventions such as delayed history and matched
wrong-history where available.

## Next Step

M106 should be a formal repeat gate for the M105 recipe:

```text
benchmark 9711/9712 under the same ablations;
probe 9711/9712 hidden-envelope retention;
add delayed-history and wrong-history interventions if harness support is ready;
admit only if retention and behavior dependence survive repeats.
```
