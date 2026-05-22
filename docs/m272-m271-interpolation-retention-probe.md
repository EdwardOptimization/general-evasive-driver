# M272 M271 Interpolation Retention Probe

M272 performs a no-training interpolation sweep from the current public-gate
base `m264_a001` toward the rejected M271 multi-surface actor-update checkpoint.

No PPO, actor update, or actor-input change was performed.

## Setup

Base checkpoint:

```text
runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

Target checkpoint:

```text
runs/m271_m264_actor_coupling_m270_multisurface_anchor100_s10_lr5e5_seed10074/optimized_checkpoint.pt
```

Objective corpus:

```text
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

## Objective Sweep

The coarse sweep confirms that the M271 direction improves the M270 objective,
but replay gates constrain the safe alpha.

| Policy | Alpha | Exact M270 delta | Sampled M270 delta | Replay surfaces passed |
| --- | ---: | ---: | ---: | ---: |
| `m272_a0_0001` | 0.0001 | -0.000000596 | -0.000000679 | 6 / 6 |
| `m272_a001` | 0.0010 | -0.000006557 | -0.000006610 | 6 / 6 |
| `m272_a005` | 0.0050 | -0.000032961 | -0.000033128 | 6 / 6 |
| `m272_a010` | 0.0100 | -0.000066161 | -0.000066280 | 6 / 6 |
| `m272_a020` | 0.0200 | -0.000132382 | -0.000132596 | 5 / 6 |
| `m272_a050` | 0.0500 | -0.000331104 | -0.000331679 | 5 / 6 |
| `m272_a200` | 0.2000 | -0.001328945 | -0.001331040 | 4 / 6 |
| `m272_a500` | 0.5000 | -0.003344655 | -0.003349495 | 3 / 6 |

Artifacts:

- `runs/m272_m264_to_m271_interpolation`
- `runs/m272_exact_m270_objective_eval`
- `runs/m272_sampled_m270_objective_eval_seed37`
- `runs/m272_retention_gate_matrix`

## Boundary Refinement

The first failing surface is M183/M170. The limiting row is:

```text
row_id = 16
target = future_braking_deceleration
physical_pair_key = 9530:6:9550:6
```

Refinement around the boundary:

| Policy | Alpha | M183/M170 pass | Row 16 normal margin |
| --- | ---: | --- | ---: |
| `m272_a010` | 0.01000 | true | not isolated in this run |
| `m272b_a0_01025` | 0.01025 | true | 0.000000636 |
| `m272b_a0_0105` | 0.01050 | false | -0.000000087 |
| `m272b_a0_01075` | 0.01075 | false | row 16 collision |
| `m272b_a011` | 0.01100 | false | row 16 collision |
| `m272r_a012` | 0.01200 | false | row 16 collision |

The selected candidate is the largest alpha tested at this resolution that
still preserves the limiting M183/M170 row:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

## Selected Objective

| Policy | Exact M270 loss | Sampled M270 loss |
| --- | ---: | ---: |
| `m264_a001` | 0.681443 | 0.681660 |
| `m272b_a0_01025` | 0.681376 | 0.681592 |

Both exact and sampled objective checks improve versus `m264_a001`.

Artifacts:

- `runs/m272_selected_exact_m270_eval`
- `runs/m272_selected_sampled_m270_eval_seed37`

## Replay Gates

The selected candidate passes every old, intermediate, and refreshed replay
surface.

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | -0.004103 | +0.001063 | true |
| M183 M170 | 17 | 17 / 17 | -0.004453 | +0.000944 | true |
| M193 M189 | 14 | 14 / 14 | -0.003301 | +0.001142 | true |
| M212 M204 | 17 | 17 / 17 | -0.002269 | +0.000409 | true |
| M223 M219 | 17 | 17 / 17 | -0.001707 | +0.000144 | true |
| M267 M264 | 17 | 17 / 17 | -0.000029 | +0.000001 | true |

Artifacts:

- `runs/m272_selected_m183_m168_replay_gate`
- `runs/m272_selected_m183_m170_replay_gate`
- `runs/m272_selected_m193_m189_replay_gate`
- `runs/m272_selected_m212_m204_replay_gate`
- `runs/m272_selected_m223_m219_replay_gate`
- `runs/m272_selected_m267_m264_replay_gate`

## Protected Key

The old protected key remains a diagnostic rather than the sole current-family
protected surface. The selected candidate still passes it, and the guard remains
discriminative because `m239_a750` fails.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| `m263_a005` | true | 0.199909 | 0.099300 | 0.100609 |
| `m264_a001` | true | 0.199971 | 0.099368 | 0.100604 |
| `m272b_a0_01025` | true | 0.199770 | 0.099129 | 0.100640 |
| `m239_a750` | false | 0.200336 | 0.099817 | 0.100519 |

Artifact:

```text
runs/m272_critical_key_seed9944
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | `m264_a001` | 0.8625 | 0.1375 | 1.835352 | 65.963971 |
| 9505 | `m272b_a0_01025` | 0.8625 | 0.1375 | 1.835337 | 65.964540 |
| 9505 | `m272b_a0_01025_reset` | 0.8500 | 0.1500 | 1.833994 | 64.059306 |
| 9505 | `m272b_a0_01025_zero_all` | 0.8000 | 0.2000 | 1.853238 | 61.043611 |
| 9506 | `m264_a001` | 0.8625 | 0.1375 | 1.852869 | 66.240421 |
| 9506 | `m272b_a0_01025` | 0.8625 | 0.1375 | 1.852854 | 66.240994 |
| 9506 | `m272b_a0_01025_reset` | 0.8500 | 0.1500 | 1.850263 | 64.349270 |
| 9506 | `m272b_a0_01025_zero_all` | 0.8000 | 0.2000 | 1.871146 | 61.306183 |

Artifacts:

- `runs/m272_behavior_gate_seed9505`
- `runs/m272_behavior_gate_seed9506`

## Interpretation

M272 shows that the M271 update direction is useful, but only inside an
extremely narrow trust region. Full M271 washes out closed-loop proof surfaces;
`alpha=0.01025` preserves them while giving a small M270 objective improvement;
`alpha=0.0105` already flips the limiting M183/M170 row.

This supports promoting the calibrated interpolation, but it does not justify
running another actor update or PPO with the same objective. The next blocker is
the boundary row itself: row 16 needs a terminal-margin or trajectory-level
retention mechanism before further learning steps.

## Decision

Promote `m272b_a0_01025` as the current public-gate base:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Decision:

```text
promote_m272_a0_01025_public_gate_base
```

Next step:

```text
m273-m272-boundary-trust-region-audit
```

M273 should audit the limiting M183/M170 row 16 and design a window-aware
terminal-margin or trajectory-retention guard before any further actor update or
PPO continuation.
