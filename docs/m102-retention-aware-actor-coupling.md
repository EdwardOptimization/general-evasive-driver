# M102 Retention-Aware Actor Coupling

M102 tests whether the M101 actor-coupling signal can be softened enough to
retain M98 hidden-envelope belief while keeping behavior-level recurrent
dependence.

M101 proved that fixed-batch actor coupling can make reset and zero-response
ablations hurt behavior, but it also moved the closed-loop trajectory
distribution enough that braking and lateral hidden-envelope probes regressed.
M102 therefore keeps the same no-wheel actor input and same fixed-batch
optimizer, but increases the normal-action anchor and lowers the reset-action
contrast.

## Hypothesis

Simple action-coupling strength may be the tradeoff knob:

```text
strong contrast: behavior dependence appears, but hidden-envelope retention fails
strong anchor:   hidden-envelope retention survives, but behavior dependence may vanish
```

M102 asks whether a middle point can pass both.

## Smoke Sweep

All smoke runs start from:

```text
runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt
```

Common smoke settings:

```text
episodes: 8
horizon_steps: 10
sample_stride: 4
max_samples: 160
steps: 40
batch_size: 64
learning_rate: 0.0001
action_margin: 0.04
```

| run | anchor | contrast | before test distance | after test distance | gain | anchor MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `runs/m102_anchor30_contrast05_smoke_seed9540` | 30.0 | 0.50 | 0.340223 | 0.537500 | 0.197276 | 0.000062 |
| `runs/m102_anchor50_contrast05_smoke_seed9541` | 50.0 | 0.50 | 0.334124 | 0.481131 | 0.147008 | 0.000111 |
| `runs/m102_anchor50_contrast025_smoke_seed9542` | 50.0 | 0.25 | 0.188133 | 0.268018 | 0.079884 | 0.000059 |

The smoke sweep confirmed the expected tradeoff: stronger anchoring suppresses
normal-action drift, but also weakens reset-action divergence.

## Conservative Repeat

The first formal M102 repeat used the most conservative setting:

```text
anchor_coef: 50.0
contrast_coef: 0.25
action_margin: 0.04
episodes: 30
horizon_steps: 15
sample_stride: 3
max_samples: 800
steps: 200
batch_size: 256
```

| seed | samples | before test distance | after test distance | gain | anchor MSE | margin pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9550 | 719 | 0.300829 | 0.621903 | 0.321074 | 0.000472 | 0.903766 |
| 9551 | 735 | 0.219812 | 0.462019 | 0.242207 | 0.000130 | 1.000000 |
| 9552 | 721 | 0.292700 | 0.670830 | 0.378130 | 0.008363 | 0.868421 |

Seed 9550 had the best retention/action balance and was gated first.

### Conservative Behavior Gate

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
  --checkpoint-policy m102_9551=runs/m102_retention_actor_coupling_seed9551/optimized_checkpoint.pt \
  --checkpoint-policy m102_9552=runs/m102_retention_actor_coupling_seed9552/optimized_checkpoint.pt \
  --checkpoint-policy m102_9550_reset=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m102_9550_zero_current=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m102_9550_zero_all=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m102_9550_noact=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m102_retention_actor_coupling_behavior_gate_seed9500
```

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| m62_a250 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| m98_9480 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| m101_9530 | 0.8625 | 0.1375 | 65.908976 | 1.864457 | -0.111205 |
| m102_9550 | 0.8625 | 0.1375 | 65.527537 | 1.854237 | -0.113690 |
| m102_9550_noact | 0.8625 | 0.1375 | 64.663968 | 1.863430 | -0.114274 |
| m102_9550_reset | 0.8750 | 0.1250 | 65.285411 | 1.855151 | -0.160266 |
| m102_9550_zero_current | 0.8500 | 0.1500 | 63.497257 | 1.856661 | -0.151330 |
| m102_9550_zero_all | 0.8500 | 0.1500 | 63.497257 | 1.856661 | -0.151330 |
| m102_9551 | 0.8625 | 0.1375 | 65.521371 | 1.852674 | -0.115961 |
| m102_9552 | 0.8625 | 0.1375 | 65.624768 | 1.850084 | -0.117000 |

The conservative setting preserves normal behavior, but it does not preserve
M101's behavior-dependence signal. Reset hidden improves success to `0.8750`.
Zero-response drops only slightly to `0.8500`.

### Conservative Hidden-Envelope Probe

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9510 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m102_retention_actor_coupling_hidden_envelope_probe_seed9510
```

| checkpoint | braking lift | lateral lift | yaw lift |
| --- | ---: | ---: | ---: |
| M98 | 0.358433 | 0.682472 | -0.014135 |
| M101 | -0.411792 | -0.148631 | 0.160665 |
| M102 conservative | 0.404079 | 0.801162 | -0.065070 |

The conservative setting retains the M98 hidden-envelope belief on braking and
lateral response, but that retained belief is not behavior-critical.

## Pareto Repeat

Because the conservative setting kept hidden belief but lost behavior
dependence, M102 also tried a middle point:

```text
anchor_coef: 30.0
contrast_coef: 0.50
```

| seed | samples | before test distance | after test distance | gain | anchor MSE | margin pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9560 | 761 | 0.280120 | 0.754509 | 0.474389 | 0.001233 | 0.929204 |
| 9561 | 763 | 0.353197 | 0.848753 | 0.495556 | 0.000142 | 1.000000 |
| 9562 | 764 | 0.293613 | 0.731061 | 0.437449 | 0.000230 | 1.000000 |

Seed 9561 had the strongest action-distance gain with low anchor MSE.

### Pareto Behavior Gate

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| m62_a250 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| m98_9480 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| m101_9530 | 0.8625 | 0.1375 | 65.908976 | 1.864457 | -0.111205 |
| m102_p9561 | 0.8625 | 0.1375 | 65.516318 | 1.853247 | -0.114506 |
| m102_p9561_noact | 0.8625 | 0.1375 | 64.565694 | 1.866637 | -0.112138 |
| m102_p9561_reset | 0.8750 | 0.1250 | 66.874062 | 1.827447 | -0.100288 |
| m102_p9561_zero_current | 0.8750 | 0.1250 | 66.650679 | 1.853399 | -0.153560 |
| m102_p9561_zero_all | 0.8750 | 0.1250 | 66.650679 | 1.853399 | -0.153560 |

The middle point also fails the behavior-dependence gate: reset and
zero-response variants improve success.

### Pareto Hidden-Envelope Probe

| checkpoint | braking lift | lateral lift | yaw lift |
| --- | ---: | ---: | ---: |
| M98 | 0.358433 | 0.682472 | -0.014135 |
| M101 | -0.411792 | -0.148631 | 0.160665 |
| M102 pareto | 0.324147 | 0.732367 | -0.029710 |

The middle point also retains the M98-style hidden-envelope signal but does not
make that signal behavior-critical.

## Decision

M102 is negative for simple retention-aware actor-coupling.

What worked:

- normal behavior and clearance are retained;
- fixed-batch action dependence increases across repeated seeds;
- the M98 braking/lateral hidden-envelope belief is retained under conservative
  and middle settings.

What failed:

- M101's behavior-level dependence disappears once the action coupling is
  softened enough to retain hidden-envelope belief;
- reset hidden and zero-response variants match or exceed normal success;
- no-action-history remains behavior-neutral.

Conclusion:

```text
fixed-batch normal-vs-reset action distance is not sufficient.
```

M103 should not continue sweeping anchor and contrast. The next objective must
be outcome-aware or closed-loop: only reward recurrent-action dependence when it
causes better clearance/success than reset, zero-response, delayed-history, or
wrong-history interventions.
