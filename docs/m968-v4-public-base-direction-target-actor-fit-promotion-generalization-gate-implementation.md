# M968 V4 Public Base Direction Target Actor-Fit Promotion Generalization Gate Implementation

## Purpose

M968 implements the no-training proof, fresh generalization, and behavior gate
designed in M967 for the M966 replay-gate-passing candidate.

Candidate:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Baseline:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

M968 does not train, run PPO, use private holdout, change actor inputs, or
promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_direction_target_actor_fit_promotion_generalization_gate
```

## Artifacts

```text
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/summary.json
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/proof_replay_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/fresh_randomized_eval_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/ood_eval_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/generalization_comparison.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/behavior_summary.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/behavior_comparison.csv
runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/route_decision.csv
```

Implementation added:

```text
src/autodrift/public_base_direction_target_actor_fit_promotion_generalization_gate.py
tests/test_public_base_direction_target_actor_fit_promotion_generalization_gate.py
```

## Proof Gate

All six public replay surfaces pass:

```text
M183/M168: pass, success_drop_count 16 / 16
M183/M170: pass, success_drop_count 17 / 17
M193/M189: pass, success_drop_count 14 / 14
M212/M204: pass, success_drop_count 17 / 17
M223/M219: pass, success_drop_count 17 / 17
M267/M264: pass, success_drop_count 17 / 17
```

All normal-margin mean deltas are positive on the proof replay stack.

Source-diverse protected diagnostics:

```text
source_diverse_protected_status: pass
```

The old key `9944|perturbed|28|28` remains diagnostic-only.

## Fresh Generalization Gate

Fresh public distribution:

```text
config: configs/m121_human_view_zero_obstacle_relvel.json
episodes: 256 per seed
seeds: 96700, 96701
```

Results:

```text
seed 96700:
  base success:      0.83984375
  candidate success: 0.83984375
  success delta:     0.0
  margin delta:     -0.0005224

seed 96701:
  base success:      0.83984375
  candidate success: 0.83984375
  success delta:     0.0
  margin delta:     -0.0005119
```

Moderate OOD distribution:

```text
config: configs/eval_m574_moderate_ood_l3.json
episodes: 128
seed: 96720
```

Result:

```text
base success:      0.625
candidate success: 0.625
success delta:     0.0
margin delta:      0.0005235
```

All fresh and OOD comparison rows pass the non-regression thresholds.

## Behavior And Ablation Gate

Behavior seeds:

```text
9505
9506
96730
96731
```

Each seed uses:

```text
base normal
candidate normal
candidate reset_recurrent_state
candidate zero_all_response
```

Results:

```text
seed 9505:  base 0.8625, candidate 0.8625, reset 0.8500, zero_all 0.8000
seed 9506:  base 0.8625, candidate 0.8625, reset 0.8500, zero_all 0.8000
seed 96730: base 0.8375, candidate 0.8375, reset 0.8250, zero_all 0.8250
seed 96731: base 0.8375, candidate 0.8375, reset 0.8250, zero_all 0.8250
```

All seeds retain:

```text
candidate normal success >= reset success >= zero_all success
```

## Contract Check

```text
actor_inputs_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
private_holdout_used: false
```

## Result

```text
result_class: direction_target_actor_fit_promotion_gate_candidate
failure_types: none
proof_pass: true
generalization_pass: true
behavior_pass: true
```

## Interpretation

M968 supports promoting the M964 `alpha=1.0` candidate to a promotion audit.
It does not itself promote the checkpoint.

Supported:

- public proof replay remains intact;
- source-diverse protected diagnostics pass;
- fresh public randomized eval does not regress success, termination, collision,
  or margin beyond pre-registered tolerances;
- moderate OOD eval does not regress;
- behavior seeds and response ablation ordering remain intact;
- actor-input contract remains unchanged.

Not yet proven:

- alpha `1.0` is officially the public-gate base;
- PPO continuation from alpha `1.0` is safe;
- paper-quality private-holdout generalization;
- high-fidelity vehicle dynamics transfer.

## Next Blocker

M968 routes to:

```text
m969-v4-public-base-direction-target-actor-fit-promotion-audit
```

M969 should decide whether to promote alpha `1.0` as the new public-gate base
based on M966 and M968, while keeping PPO and private holdout blocked.
