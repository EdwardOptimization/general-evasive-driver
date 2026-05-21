# M123 M122 Zero-Relvel Objective Sanity

M122 admitted a strict zero obstacle-relative-velocity wrong-history corpus for
objective-sanity only. M123 tests whether that corpus can be optimized with a
retention anchor without damaging broad behavior or belief diagnostics.

## Setup

Initial checkpoint:

```text
runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt
```

Snippet corpus:

```text
runs/m122_zero_relvel_m105_strict_60ep_seed9720/outcome_intervention_snippets.npz
```

All objective runs use:

```text
--steps 120
--batch-size 64
--learning-rate 0.0001
--logprob-margin 0.05
--train-scope actor_coupling
--action-anchor-checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt
--action-anchor-env-config configs/m121_human_view_zero_obstacle_relvel.json
--action-anchor-coef 10.0
--action-anchor-episodes 30
--action-anchor-horizon-steps 15
--action-anchor-sample-stride 3
--action-anchor-max-samples 800
```

Run directories:

```text
runs/m123_m122_zero_relvel_objective_seed9810
runs/m123_m122_zero_relvel_objective_seed9811
runs/m123_m122_zero_relvel_objective_seed9812
```

## Objective Result

| Seed | Before loss | After loss | Improvement | After anchor MSE | Objective pass |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9810 | 0.086424 | 0.055829 | 0.030595 | 0.000744 | yes |
| 9811 | 0.086424 | 0.054460 | 0.031964 | 0.000826 | yes |
| 9812 | 0.086424 | 0.056457 | 0.029967 | 0.000763 | yes |

The fixed M122 objective is optimizable from M105 with small action-anchor MSE.
This is a repeatable objective-sanity positive.

## Behavior Gate

Command artifact:

```text
runs/m123_zero_relvel_behavior_gate_seed9500
```

Evaluation uses `configs/m121_human_view_zero_obstacle_relvel.json`, `80`
episodes, seed `9500`.

| Policy | Success | Termination | Return mean | Clearance margin mean | Clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M62 | 0.8625 | 0.1375 | 64.467211 | 1.856243 | -0.096955 |
| M105 | 0.8625 | 0.1375 | 65.548247 | 1.859915 | -0.115310 |
| M123 9810 | 0.8625 | 0.1375 | 65.556386 | 1.860908 | -0.154383 |
| M123 9811 | 0.8625 | 0.1375 | 65.595058 | 1.860069 | -0.156437 |
| M123 9812 | 0.8625 | 0.1375 | 65.593241 | 1.858710 | -0.153603 |
| M123 9811 reset | 0.8500 | 0.1500 | 63.695488 | 1.853710 | -0.168546 |
| M123 9811 zero-current | 0.8000 | 0.2000 | 60.475772 | 1.868746 | -0.146170 |
| M123 9811 zero-all | 0.8000 | 0.2000 | 60.475772 | 1.868746 | -0.146170 |
| M123 9811 no-action | 0.8625 | 0.1375 | 65.151237 | 1.862139 | -0.141938 |

Behavior retention passes on this gate: all normal M123 repeats retain M105
success, and zero-response ablations degrade success by `0.0625`.
Reset-hidden degrades by `0.0125`. No-action history remains behavior-neutral on
this benchmark.

## Hidden-Envelope Probe

Run directories:

```text
runs/m123_m105_zero_relvel_hidden_envelope_probe_seed9510
runs/m123_9811_zero_relvel_hidden_envelope_probe_seed9510
```

Both probes use `configs/m121_human_view_zero_obstacle_relvel.json`, `30`
episodes, seed `9510`, horizon `15`, stride `3`, and max samples `800`.

| Target | M105 hidden-reset R2 | M123 9811 hidden-reset R2 | Change |
| --- | ---: | ---: | ---: |
| future braking deceleration | -0.259482 | -0.193512 | +0.065970 |
| future lateral accel response | 0.368120 | 0.442902 | +0.074782 |
| future yaw response | 0.133647 | 0.031559 | -0.102088 |

The probe is mixed. Braking remains negative versus reset, but less negative
than M105. Lateral improves. Yaw response-hidden lift regresses materially.

## Decision

M123 is a qualified objective-sanity positive and a driver-admission rejection.

What passed:

- fixed M122 loss improves across three seeds;
- action-anchor MSE remains below `0.001`;
- normal behavior success and mean clearance margin are retained on the
  zero-relvel behavior gate;
- reset and zero-response ablations reduce success for the selected 9811
  checkpoint.

What blocks PPO or driver admission:

- hidden-envelope evidence is mixed, especially yaw response-hidden lift;
- no-action history is still neutral on the behavior gate;
- M122 snippets are perturbed-source only, so the objective signal is not yet a
  symmetric hidden-dynamics surface;
- this is one behavior seed and one hidden probe seed, not a formal repeat gate.

Do not start PPO from M123. The next step should reduce the update strength or
add a retention/belief guard so M122 outcome fitting preserves yaw belief while
keeping the zero-response behavior gap.
