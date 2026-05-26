# M966 V4 Public Base Direction Target Actor-Fit Replay Gate Implementation

## Purpose

M966 implements the no-training public replay/proof gate designed in M965 for
the M964 direction-target actor-fit candidates.

It does not train, update model weights, run PPO, change actor inputs, use
private holdout, or promote.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_direction_target_actor_fit_replay_gate
```

## Artifacts

```text
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/summary.json
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/candidate_preflight_summary.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/public_replay_gate_summary.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/behavior_summary.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/behavior_comparison.csv
runs/m966_v4_public_base_direction_target_actor_fit_replay_gate/route_decision.csv
```

Implementation added:

```text
src/autodrift/public_base_direction_target_actor_fit_replay_gate.py
tests/test_public_base_direction_target_actor_fit_replay_gate.py
```

## Candidate Preflight

M966 evaluates all M964 candidate alphas on the full M267/M264 replay surface
before selecting a candidate for the full public replay stack.

```text
alpha 1.00: pass, success_drop_count 17 / 17
alpha 0.50: pass, success_drop_count 17 / 17
alpha 0.20: pass, success_drop_count 17 / 17
alpha 0.10: pass, success_drop_count 17 / 17
alpha 0.05: pass, success_drop_count 17 / 17
```

The highest-ranked passing candidate is:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

## Public Replay Result

Selected candidate:

```text
alpha: 1.00
label: m964_direction_target_a1
```

All six public replay surfaces pass:

```text
M183/M168: pass, success_drop_count 16 / 16
M183/M170: pass, success_drop_count 17 / 17
M193/M189: pass, success_drop_count 14 / 14
M212/M204: pass, success_drop_count 17 / 17
M223/M219: pass, success_drop_count 17 / 17
M267/M264: pass, success_drop_count 17 / 17
```

Margin deltas are positive on the normal branch for all six public surfaces.
The M267/M264 full surface improves normal-margin mean by about `0.00025` while
retaining the full `17 / 17` wrong-history success-drop count.

Source-diverse protected diagnostics also pass:

```text
current_m333_surface: pass
m317_continuity_surface: pass
m314_continuity_surface: pass
```

The old key `9944|perturbed|28|28` remains diagnostic-only, not a singleton
veto.

## Behavior Seeds

Behavior seeds `9505` and `9506` both retain baseline success:

```text
seed 9505:
  base success:      0.8625
  candidate success: 0.8625
  reset success:     0.8500
  zero-all success:  0.8000

seed 9506:
  base success:      0.8625
  candidate success: 0.8625
  reset success:     0.8500
  zero-all success:  0.8000
```

For both seeds:

```text
normal success >= reset success >= zero_all success
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
result_class: direction_target_actor_fit_replay_gate_pass
failure_types: none
candidate_preflight_pass_count: 5
public_replay_gates_passed: 6
six_public_replay_gates_pass: true
behavior_pass: true
source_diverse_protected_status: pass
```

## Interpretation

M966 is the first closed-loop replay/proof gate in this branch where the
direction-target actor-fit candidate survives the full public replay stack.

Supported:

- the exported M962 direction targets can be fit into `actor_mean`;
- the strongest M964 candidate, `alpha=1.00`, preserves M267/M264 wrong-history
  proof over the full `17` row surface;
- older public replay surfaces and source-diverse protected diagnostics remain
  intact;
- broad behavior seeds `9505/9506` do not regress;
- actor inputs and recurrent contract remain unchanged.

Not yet proven:

- candidate should become the new public-gate base;
- generalization beyond public proof surfaces;
- robustness on fresh randomized scenario distributions;
- PPO continuation from this candidate is safe;
- paper-quality private-holdout evidence.

## Next Blocker

M966 routes to:

```text
m967-v4-public-base-direction-target-actor-fit-promotion-generalization-design
```

M967 should design the proof + generalization + promotion protocol for the
M966 replay-gate-passing candidate. It should keep PPO and promotion blocked
until public proof retention, fresh randomized generalization, behavior
retention, and holdout discipline are explicit.
