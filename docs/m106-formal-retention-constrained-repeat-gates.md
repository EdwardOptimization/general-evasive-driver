# M106 Formal Retention-Constrained Repeat Gates

M106 repeats the M105 action-anchor outcome recipe before admitting it for PPO
continuation.

M105 was the first M101-M105 line where one checkpoint had:

```text
normal behavior retention
reset-hidden degradation
zero-response degradation
positive braking/lateral/yaw hidden-envelope lift
```

That evidence was still a smoke result because the full behavior/probe gate was
only run on checkpoint seed `9710`. M106 asks whether the same claim survives
repeat checkpoints and fresh probe seeds.

## Behavior Repeat Gate

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 80 \
  --seed 9500 \
  --policies heuristic \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102_9550=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105_9710=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --checkpoint-policy m105_9711=runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt \
  --checkpoint-policy m105_9711_reset=runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m105_9711_zero_current=runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m105_9711_zero_all=runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m105_9711_noact=runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt@zero_action_history \
  --checkpoint-policy m105_9712=runs/m105_anchor10_outcome_coupling_smoke_seed9712/optimized_checkpoint.pt \
  --checkpoint-policy m105_9712_reset=runs/m105_anchor10_outcome_coupling_smoke_seed9712/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m105_9712_zero_current=runs/m105_anchor10_outcome_coupling_smoke_seed9712/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m105_9712_zero_all=runs/m105_anchor10_outcome_coupling_smoke_seed9712/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m105_9712_noact=runs/m105_anchor10_outcome_coupling_smoke_seed9712/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m106_m105_repeat_behavior_gate_seed9500
```

| policy | success | termination | margin mean | margin min |
| --- | ---: | ---: | ---: | ---: |
| M62 | 0.8625 | 0.1375 | 1.852887 | -0.106535 |
| M102 | 0.8625 | 0.1375 | 1.854237 | -0.113690 |
| M105 9710 | 0.8625 | 0.1375 | 1.854093 | -0.111374 |
| M105 9711 | 0.8625 | 0.1375 | 1.853957 | -0.111715 |
| M105 9711 reset | 0.8500 | 0.1500 | 1.852786 | -0.144214 |
| M105 9711 zero-all | 0.8375 | 0.1625 | 1.864293 | -0.145943 |
| M105 9711 no-action | 0.8625 | 0.1375 | 1.862279 | -0.113920 |
| M105 9712 | 0.8625 | 0.1375 | 1.851823 | -0.112946 |
| M105 9712 reset | 0.8500 | 0.1500 | 1.851783 | -0.145076 |
| M105 9712 zero-all | 0.8250 | 0.1750 | 1.861718 | -0.147218 |
| M105 9712 no-action | 0.8625 | 0.1375 | 1.860556 | -0.115279 |

Behavior result:

- repeat normal success retention passes for both `9711` and `9712`;
- reset-hidden degradation repeats: `0.8625 -> 0.8500` for both checkpoints;
- zero-response degradation repeats: `0.8625 -> 0.8375` and `0.8625 -> 0.8250`;
- no-action-history remains behavior-neutral;
- strict M62 margin retention is borderline and fails for `9712`
  (`1.851823 < 1.852887`).

## Hidden-Envelope Repeat Probes

First, repeat checkpoint seeds on the original M105 probe seed `9510`:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9711/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9510 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m106_m105_9711_hidden_envelope_probe_seed9510
```

The same command was run for `9712` with
`runs/m106_m105_9712_hidden_envelope_probe_seed9510`.

| checkpoint | probe seed | braking lift | lateral lift | yaw lift |
| --- | ---: | ---: | ---: | ---: |
| 9710 | 9510 | 0.211398 | 0.557126 | 0.033114 |
| 9711 | 9510 | 0.231634 | 0.616504 | 0.037736 |
| 9712 | 9510 | 0.235603 | 0.602892 | 0.013037 |

On the original probe seed, repeat checkpoints pass hidden-envelope retention.

Then run fresh probe seeds:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9511 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m106_m105_9710_hidden_envelope_probe_seed9511
```

The same recipe was run for:

```text
9711 / 9511 -> runs/m106_m105_9711_hidden_envelope_probe_seed9511
9710 / 9512 -> runs/m106_m105_9710_hidden_envelope_probe_seed9512
9712 / 9512 -> runs/m106_m105_9712_hidden_envelope_probe_seed9512
```

| checkpoint | probe seed | braking lift | lateral lift | yaw lift |
| --- | ---: | ---: | ---: | ---: |
| 9710 | 9511 | 12.299186 | -2.270934 | -1.595636 |
| 9711 | 9511 | 12.550788 | -2.378211 | -1.561755 |
| 9710 | 9512 | -0.266590 | -0.648338 | -1.033484 |
| 9712 | 9512 | -0.261113 | -0.646388 | -1.018397 |

Fresh probe seeds fail badly. The fixed-seed positive hidden-envelope signal is
therefore not robust enough to admit M105 as a driver candidate.

## Decision

M106 rejects formal admission of the M105 recipe.

What passed:

- objective repeats from M105 were stable;
- behavior repeat gates on `9711` and `9712` retained normal success;
- reset-hidden and zero-response degradation repeated on behavior seed `9500`;
- hidden-envelope retention repeated across checkpoints on the original probe
  seed `9510`.

What failed:

- strict margin retention failed for `9712` by about `0.0011`;
- hidden-envelope lift does not generalize across fresh probe seeds;
- no-action-history remains behavior-neutral;
- delayed-history and matched wrong-history are not yet available as simple
  benchmark policy ablations.

Conclusion: M105 remains an important lead because behavior dependence repeats,
but the proof chain is not strong enough. The next step should be M107: replace
single-seed hidden-envelope admission with a multi-seed aggregate gate and then
decide whether M105 needs a stronger hidden-retention objective or a more stable
probe design.
