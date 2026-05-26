# M1022 V4 Public Base Candidate B Promotion Generalization Gate

## Purpose

M1022 runs the no-training promotion/generalization gate for Candidate B after
M1021 design.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote. Passing M1022 only makes Candidate B eligible for a
separate promotion audit.

## Candidate

```text
candidate: m1013_lam0030_a050
checkpoint:
  runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
base:
  runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.m1013_candidate_b_promotion_generalization_gate \
  --base-checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --candidate-checkpoint runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt \
  --temporal-corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --base-temporal-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --run-dir runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate \
  --device auto \
  --fresh-episodes 256 \
  --ood-episodes 128 \
  --behavior-episodes 80 \
  --max-continuation-steps 60
```

## Result

```text
result_class: candidate_b_promotion_gate_candidate
exact_contract_pass_count: 1
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
reset_zero_all_ordering_retained: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Artifact:

```text
runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/summary.json
```

## Exact Retention

M1022 recomputed exact temporal retention:

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

## Proof Replay

All six public proof replay surfaces passed:

| surface | rows | base drops | candidate drops | normal success delta | margin delta | gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 | 16 | 0.0 | -0.000081 | pass |
| M183/M170 | 17 | 17 | 17 | 0.0 | -0.000083 | pass |
| M193/M189 | 14 | 14 | 14 | 0.0 | -0.000079 | pass |
| M212/M204 | 17 | 17 | 17 | 0.0 | -0.000074 | pass |
| M223/M219 | 17 | 17 | 17 | 0.0 | -0.000074 | pass |
| M267/M264 | 17 | 17 | 17 | 0.0 | -0.000074 | pass |

Source-diverse protected diagnostics also passed:

```text
replay_gates_passed: 3
replay_gates_failed: 0
overall_pass: true
```

## Fresh Public Generalization

Candidate B retained M974 performance on fresh public seeds:

| distribution | seed | base success | candidate success | success delta | base margin | candidate margin | gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| fresh_public | 102100 | 0.902344 | 0.902344 | 0.0 | 1.859991 | 1.860026 | pass |
| fresh_public | 102101 | 0.902344 | 0.902344 | 0.0 | 1.873517 | 1.873553 | pass |
| moderate_ood | 102120 | 0.664062 | 0.664062 | 0.0 | 1.305711 | 1.305817 | pass |

Collision and termination deltas were `0.0` on all three rows.

## Behavior And Ablation Retention

All behavior seeds passed:

| seed | base success | candidate success | reset success | zero-all success | gate |
| ---: | ---: | ---: | ---: | ---: | --- |
| 9505 | 0.8625 | 0.8625 | 0.8500 | 0.8000 | pass |
| 9506 | 0.8625 | 0.8625 | 0.8500 | 0.8000 | pass |
| 102130 | 0.9125 | 0.9125 | 0.8750 | 0.8625 | pass |
| 102131 | 0.9125 | 0.9125 | 0.8750 | 0.8625 | pass |

The normal >= reset >= zero-all ordering was retained.

## Interpretation

Candidate B is now a promotion-audit candidate:

```text
It preserves exact temporal evidence.
It preserves all public proof replay surfaces.
It preserves source-diverse protected diagnostics.
It does not regress fresh public or moderate-OOD scenario behavior.
It retains behavior/ablation ordering.
```

This still does not promote the checkpoint. The next step must be an explicit
promotion audit that updates the official public base only if the evidence and
lineage are accepted.

## Decision

```text
candidate_b_promotion_gate_candidate_route_to_promotion_audit
```

Next:

```text
m1023-v4-public-base-candidate-b-promotion-audit
```
