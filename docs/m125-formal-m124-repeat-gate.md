# M125 Formal M124 Repeat Gate

M124 produced the best current calibrated objective candidate. M125 repeats the
behavior and hidden-envelope gates on fresh seeds before deciding whether M124
can be admitted for PPO or continuation.

## Gate

Admit M124 only if:

- normal behavior retention survives fresh behavior seeds;
- zero-response ablation still degrades success or safety margin;
- yaw and lateral response-hidden lift survive fresh probe seeds;
- stronger history interventions do not remain behavior-neutral;
- the decision explicitly states whether PPO continuation is admitted.

## Behavior Repeat

All behavior runs use `configs/m121_human_view_zero_obstacle_relvel.json`, `80`
episodes, and compare M105 against the three calibrated M124 repeats.

Run directories:

```text
runs/m125_m124_behavior_gate_seed9501
runs/m125_m124_behavior_gate_seed9502
```

Fresh seed `9501`:

| Policy | Success | Termination | Return mean | Clearance margin mean | Clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M105 | 0.8625 | 0.1375 | 66.070205 | 1.878774 | -0.115310 |
| M124 9821 | 0.8625 | 0.1375 | 66.151242 | 1.878626 | -0.125811 |
| M124 9822 | 0.8625 | 0.1375 | 66.145910 | 1.879146 | -0.124606 |
| M124 9823 | 0.8625 | 0.1375 | 66.155999 | 1.879406 | -0.124812 |
| M124 9821 reset | 0.8500 | 0.1500 | 64.415253 | 1.873592 | -0.169498 |
| M124 9821 zero-current | 0.8000 | 0.2000 | 61.118468 | 1.888154 | -0.148345 |
| M124 9821 zero-all | 0.8000 | 0.2000 | 61.118468 | 1.888154 | -0.148345 |
| M124 9821 no-action | 0.8625 | 0.1375 | 65.665856 | 1.882705 | -0.120653 |

Fresh seed `9502`:

| Policy | Success | Termination | Return mean | Clearance margin mean | Clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M105 | 0.8625 | 0.1375 | 65.602408 | 1.850164 | -0.115310 |
| M124 9821 | 0.8625 | 0.1375 | 65.673907 | 1.849902 | -0.125811 |
| M124 9822 | 0.8625 | 0.1375 | 65.669515 | 1.850418 | -0.124606 |
| M124 9823 | 0.8625 | 0.1375 | 65.679698 | 1.850668 | -0.124812 |
| M124 9821 reset | 0.8500 | 0.1500 | 63.941431 | 1.846277 | -0.169498 |
| M124 9821 zero-current | 0.8000 | 0.2000 | 60.639104 | 1.860214 | -0.148345 |
| M124 9821 zero-all | 0.8000 | 0.2000 | 60.639104 | 1.860214 | -0.148345 |
| M124 9821 no-action | 0.8625 | 0.1375 | 65.191544 | 1.853713 | -0.120653 |

Behavior conclusion:

- normal M124 behavior retention passes on both fresh seeds;
- zero-response ablation repeatably degrades success from `0.8625` to `0.8000`;
- reset-hidden degrades to `0.8500`;
- no-action history remains behavior-neutral.

## Hidden-Envelope Repeat

Run directories:

```text
runs/m125_m105_hidden_probe_seed9511
runs/m125_m124_9821_hidden_probe_seed9511
runs/m125_m105_hidden_probe_seed9512
runs/m125_m124_9821_hidden_probe_seed9512
```

All hidden probes use `configs/m121_human_view_zero_obstacle_relvel.json`, `30`
episodes, horizon `15`, stride `3`, max samples `800`, and ridge `0.1`.

Response-hidden minus reset R2:

| Policy/probe seed | Braking | Lateral | Yaw |
| --- | ---: | ---: | ---: |
| M105 seed 9510 | -0.259482 | 0.368120 | 0.133647 |
| M124 seed 9510 | -0.212614 | 0.543924 | 0.115071 |
| M105 seed 9511 | 25.655085 | -3.663584 | -0.482697 |
| M124 seed 9511 | 14.011373 | -2.982733 | -0.570959 |
| M105 seed 9512 | -0.762989 | -0.353693 | -1.952766 |
| M124 seed 9512 | -1.694324 | -0.303982 | -2.534112 |

Hidden-envelope conclusion:

- fresh probe seeds do not support yaw or lateral response-hidden retention;
- M124 does not beat M105 robustly on fresh probe seeds;
- probe seed `9511` shows unstable extreme braking lift for both M105 and M124,
  indicating the current hidden-envelope probe surface remains fragile;
- seed `9512` is broadly negative.

## Decision

M125 rejects PPO/continuation admission for M124.

What passed:

- behavior retention across fresh behavior seeds;
- repeatable zero-response success degradation;
- reset-hidden degradation is small but present.

What failed:

- yaw hidden-envelope lift fails fresh probe seeds;
- lateral hidden-envelope lift also fails fresh probe seeds;
- no-action history remains neutral;
- the hidden-envelope proof surface still looks probe-seed fragile.

The next step should not be PPO. M126 should diagnose and rebuild the
zero-relvel belief proof surface, including target reliability and stronger
history-intervention gates, before more continuation training.
