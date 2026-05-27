# M1126 V4 Public Base Row15 Projection Full Public Gate Design

## Purpose

M1126 designs the expanded full public gate for the M1123 alpha `0.15`
candidate after M1125 passed family-intersection replay.

This milestone is design-only. It does not run replay or evaluation, train
actor weights, run PPO, promote, use private holdout, or change actor inputs.

## Candidate

```text
candidate_label: alpha_0_15
candidate_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Current evidence:

```text
M1123 exact M1107 delta vs base: -0.000417471
M1123 row15 unsafe-margin gate: pass
M1123 six-surface first replay: pass
M1125 family-intersection gate: pass
```

The candidate is not promotable until the expanded full public gate passes and
a separate promotion audit decides whether to promote it.

## Gate Stack

M1127 should run two commands in order.

### 1. M1107 Exact Recheck

M1127 should first rerun the branch-specific exact objective check:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy alpha_0_15=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --device cpu \
  --exact \
  --baseline-policy proof_current \
  --logprob-margin 0.05 \
  --run-dir runs/m1127_row15_projection_m1107_exact_eval
```

Required:

```text
alpha_0_15 exact M1107 loss <= proof_current exact M1107 loss
alpha_0_15 exact M1107 delta remains negative
```

### 2. Expanded Full Public Gate

Then run the existing expanded full public gate wrapper:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.candidate_b_combined_active_set_full_public_gate \
  --base-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --candidate-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --temporal-corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --temporal-base-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --combined-anchor-npz runs/m1037_candidate_b_combined_active_set_anchor_export/combined_active_set_anchor_row16x4.npz \
  --fresh-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --ood-env-config configs/eval_m574_moderate_ood_l3.json \
  --behavior-env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --fresh-seeds 103900,103901 \
  --ood-seeds 103920 \
  --behavior-seeds 9505,9506,103930,103931 \
  --fresh-episodes 256 \
  --ood-episodes 128 \
  --behavior-episodes 80 \
  --max-continuation-steps 60 \
  --preference-margin 0.05 \
  --lambda-pref 1.0 \
  --lambda-anchor 0.25 \
  --device auto \
  --run-dir runs/m1127_row15_projection_full_public_gate
```

The wrapper includes:

```text
allowed changed-parameter contract
M297/M270 exact gate
old public replay proof gates
M1061 family-intersection public gate
source-diverse protected diagnostic
fresh public randomized eval
moderate OOD eval
behavior seeds and reset/zero-all ordering
```

## Pass Criteria

M1127 can be considered a full-public-gate candidate only if both are true:

```text
M1107 exact recheck passes
full public wrapper result_class == candidate_b_combined_active_set_full_public_gate_candidate
```

Required full wrapper fields:

```text
actor_inputs_changed: false
allowed_surface_contract_pass: true
exact_pass: true
proof_pass: true
family_intersection_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
ppo_used: false
promoted: false
private_holdout_used: false
```

## Stop Rules

If any tier fails, M1127 must stop and route to a failure audit of that tier.
It must not continue to promotion, private holdout, PPO, or backup-candidate
switching.

If every tier passes, M1127 should route to a separate promotion audit or branch
synthesis. M1127 itself must not promote.

## Decision

```text
row15_projection_full_public_gate_design_admit_m1127
```

Next milestone:

```text
m1127-v4-public-base-row15-projection-full-public-gate
```
