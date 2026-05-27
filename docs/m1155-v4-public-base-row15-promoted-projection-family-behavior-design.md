# M1155 V4 Public Base Row15 Promoted Projection Family Behavior Design

## Purpose

M1155 designs the next public diagnostics for the M1154 selected projection
candidate:

```text
candidate_label: alpha_0_05
candidate_checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

This milestone is design-only. It does not run replay, behavior eval, PPO,
actor training, mining, promotion, private holdout, or actor-input changes.

## Parent Evidence

M1154 established:

```text
exact M1144 delta: -0.000378
failed-row unsafe-margin pass: 76 / 76
M1149 first replay pass: 10 / 10 surfaces
selected alpha: 0.05
```

The candidate is not promotable. The row15-promoted materialized wrong-history
margin is very close to zero:

```text
wrong_history_margin_max: -0.000000497
```

So the next run must remain diagnostic and must stop on any proof or behavior
regression.

## Diagnostic Gate Stack

M1156 should run two commands in order.

### 1. M1144 Exact Recheck

Recheck the branch-specific exact objective against the current public-gate
base:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy alpha_0_05=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --device cpu \
  --exact \
  --baseline-policy row15_current \
  --logprob-margin 0.05 \
  --run-dir runs/m1156_row15_promoted_projection_m1144_exact_eval
```

Required:

```text
alpha_0_05 exact M1144 loss <= row15_current exact M1144 loss
alpha_0_05 exact M1144 delta remains negative
```

### 2. Expanded Public Diagnostic Wrapper

Run the existing expanded public wrapper with the current public-gate base as
base and `alpha_0_05` as candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.candidate_b_combined_active_set_full_public_gate \
  --base-checkpoint runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --candidate-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
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
  --run-dir runs/m1156_row15_promoted_projection_expanded_public_diagnostic
```

This wrapper includes:

```text
allowed changed-parameter contract
M297/M270 exact gate
old-public replay proof gates
M1061 family-intersection public gate
source-diverse protected diagnostic
fresh public randomized eval
moderate OOD eval
behavior seeds and reset/zero-all ordering
```

## Pass Criteria

M1156 passes only if:

```text
M1144 exact recheck passes
expanded wrapper result_class == candidate_b_combined_active_set_full_public_gate_candidate
```

Required expanded-wrapper fields:

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

If M1144 exact recheck fails, M1156 should stop and route to exact regression
audit. It should not run the expanded wrapper.

If any expanded wrapper tier fails, M1156 should route to a tier-specific
failure audit:

```text
contract_artifact
exact_regression
old_public_or_source_proof_washout
family_intersection_proof_washout
generalization_regression
behavior_regression
```

If all diagnostics pass, the next step is not promotion. It should route to a
separate synthesis or promotion-audit design because `alpha_0_05` is a
near-boundary proof repair.

## Decision

```text
decision: row15_promoted_projection_family_behavior_design_admit_diagnostic_run
next: m1156-v4-public-base-row15-promoted-projection-family-behavior-run
```
