# M1019 V4 Public Base M1013 Candidate B Full Replay Gate

## Purpose

M1019 runs the full public proof/generalization/behavior gate for M1013
Candidate B after M1018 design.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote.

## Candidate

```text
candidate: m1013_lam0030_a050
checkpoint:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
source:
  M1013 lambda_wrong_trust=0.03, alpha=0.5
```

Candidate B was selected because M1016 showed it passes M267/M264 preflight,
and M1017 showed the unsigned branch-L2 metric was a detector, not an ordering
gate.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.m1013_candidate_b_full_replay_gate \
  --base-checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --candidate-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --temporal-corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --temporal-metadata runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv \
  --base-temporal-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --run-dir runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate \
  --device auto \
  --max-continuation-steps 60
```

## Result

```text
result_class: m1013_candidate_b_full_replay_gate_pass
inner_result_class: temporal_sequence_public_replay_gate_pass
exact_contract_pass_count: 1
candidate_preflight_pass_count: 1
public_replay_gates_passed: 6
source_diverse_pass: true
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Artifact:

```text
runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate/summary.json
```

## Exact Temporal Retention

M1019 recomputed the M997 temporal exact metrics instead of relying on cached
M1013 metrics.

```text
weighted_total_loss: -0.883306770
total_loss_improvement: 0.001893922
weighted_normal_sequence_nll: -1.372992072
weighted_temporal_preference_loss: 0.489685301
weighted_logp_gap_mean: 0.647042760
temporal_logp_gap_p10: 0.055578701
candidate_action_l2_mean: 0.001016231
candidate_action_l2_max: 0.001998572
changed parameters: actor_mean.bias; actor_mean.weight
actor inputs changed: false
non-actor parameters changed: false
exact_contract_gate_pass: true
```

## Public Replay Surfaces

All six public replay surfaces passed:

| surface | rows | base drops | candidate drops | normal success delta | margin delta | gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 | 16 | 0.0 | -0.000081 | pass |
| M183/M170 | 17 | 17 | 17 | 0.0 | -0.000083 | pass |
| M193/M189 | 14 | 14 | 14 | 0.0 | -0.000079 | pass |
| M212/M204 | 17 | 17 | 17 | 0.0 | -0.000074 | pass |
| M223/M219 | 17 | 17 | 17 | 0.0 | -0.000074 | pass |
| M267/M264 | 17 | 17 | 17 | 0.0 | -0.000074 | pass |

Interpretation:

```text
Candidate B preserves normal success and wrong-history success-drop counts on
all six public proof surfaces. The small normal-margin deltas are within the
pre-registered tolerance.
```

## Source-Diverse Diagnostics

The source-diverse protected diagnostic passed:

```text
replay_gate_count: 3
replay_gates_passed: 3
replay_gates_failed: 0
overall_pass: true
failed_replay_gates: []
```

The three surfaces were:

```text
current_m333_surface
m317_continuity_surface
m314_continuity_surface
```

## Behavior Seeds

Behavior seeds `9505` and `9506` retained baseline success and reset/zero-all
ordering:

| seed | base success | candidate success | reset success | zero-all success | gate |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9505 | 0.8625 | 0.8625 | 0.8500 | 0.8000 | pass |
| 9506 | 0.8625 | 0.8625 | 0.8500 | 0.8000 | pass |

## Interpretation

M1019 is the first full public replay pass for the M1013 Candidate B direction.
The earlier M1011 unsigned branch trust loss rejected it because the action
change was large, but M1016 and M1019 show that the direction is
outcome-safe on public proof rows: wrong-history margins stay on the failing
side, and normal-history success is retained.

This does not promote Candidate B. It establishes that Candidate B is a
public-gate candidate that deserves either a separate promotion/generalization
audit or branch-level synthesis before more local objective work.

## Cadence Decision

The temporal sequence objective branch has now run M1010-M1019 after the M1009
synthesis. This reaches the 10-milestone synthesis cadence. The next step should
therefore synthesize M1010-M1019 before any promotion audit, PPO continuation,
or another objective update.

## Decision

```text
candidate_b_full_replay_gate_pass_route_to_branch_synthesis
```

Next:

```text
m1020-v4-public-base-temporal-sequence-objective-post-candidate-b-synthesis
```
