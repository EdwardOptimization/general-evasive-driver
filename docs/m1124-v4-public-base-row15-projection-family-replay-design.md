# M1124 V4 Public Base Row15 Projection Family Replay Design

## Purpose

M1124 designs the next proof gate for the M1123 alpha `0.15` candidate.

This milestone is design-only. It does not run replay, train actor weights, run
PPO, run full public gate, run fresh/OOD, run behavior gates, promote, use
private holdout, or change actor inputs.

## Parent Candidate

M1123 selected:

```text
candidate_label: alpha_0_15
candidate_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

result_class: row15_unsafe_margin_projection_first_replay_candidate
exact M1107 delta vs base: -0.000417471
target-base trajectory MSE: 0.0000000336
combined trajectory MSE: 0.0000050340
first replay: pass
```

This candidate has passed only row15 unsafe-margin and target-base
old-public/source-diverse first replay. It is not promotable and must not enter
full public gate or PPO until family-intersection replay is known.

## Family Gate

M1125 should run the existing M1061 family-intersection public gate wrapper:

```text
src/autodrift/family_intersection_public_gate.py
```

Source policies:

```text
short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

Source corpora:

```text
short61049:
  runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv

short61050:
  runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv

short61051:
  runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
```

Candidate:

```text
alpha_0_15:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.family_intersection_public_gate \
  --source-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --source-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --source-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --source-corpus short61049=runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv \
  --source-corpus short61050=runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv \
  --source-corpus short61051=runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv \
  --candidate-policy alpha_0_15=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-rows 0 \
  --max-continuation-steps 60 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m1125_row15_projection_family_replay
```

## Pass Criteria

M1125 passes only if:

```text
result_class == family_intersection_public_gate_pass
overall_pass == true
replay_gate_count == 3
replay_gates_passed == 3
actor_inputs_changed == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

For each source corpus:

```text
gate_pass == true
candidate_success_drop_count >= baseline_success_drop_count
normal_success_delta >= -0.0
normal_margin_mean_delta >= -0.005
margin_gap_mean_delta >= -0.001
```

## Stop Rules

If any source-to-candidate replay gate fails, M1125 must stop and route to a
family-replay failure audit. It must not continue to full public gate, fresh/OOD,
behavior gates, PPO, or promotion.

If all three family gates pass, M1125 may route to an expanded full public gate
design. Passing M1125 alone still does not promote the checkpoint.

## Decision

```text
row15_projection_family_replay_design_admit_m1125
```

Next milestone:

```text
m1125-v4-public-base-row15-projection-family-replay
```
