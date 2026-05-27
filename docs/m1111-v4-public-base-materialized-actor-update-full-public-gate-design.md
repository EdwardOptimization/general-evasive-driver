# M1111 V4 Public Base Materialized Actor Update Full Public Gate Design

## Purpose

M1111 designs the closed-loop gate for the exact-pass M1110 materialized
actor-update candidate.

This milestone is design-only. It does not train actor weights, run PPO, run
replay, build a corpus, mine rows, promote a checkpoint, use private holdout, or
change actor inputs.

## Candidate Selection

M1110 produced three exact-improving, contract-clean candidates. The primary
candidate is selected by lowest exact M1107 loss:

```text
candidate label: m1110_110901
candidate checkpoint:
  runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt

base checkpoint:
  runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt

base exact M1107 loss: 0.6791173219680786
candidate exact M1107 loss: 0.6743494868278503
delta: -0.0047678351402282715
```

The other two candidates are diagnostics only. M1112 must not switch to them
after seeing a failed gate unless a separate audit admits a new candidate
selection rule.

## M1112 Gate Plan

M1112 should run two commands in order.

First, rerun the exact M1107 materialized objective check for the selected
candidate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz \
  --checkpoint-policy proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy m1110_110901=runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt \
  --device cpu \
  --exact \
  --baseline-policy proof_current \
  --logprob-margin 0.05 \
  --run-dir runs/m1112_materialized_actor_update_m1107_exact_eval
```

Second, run the expanded full public gate wrapper:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.candidate_b_combined_active_set_full_public_gate \
  --base-checkpoint runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --candidate-checkpoint runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt \
  --run-dir runs/m1112_materialized_actor_update_full_public_gate \
  --device auto
```

## Required Gate Stack

The M1112 result must report:

```text
M1107 exact objective no-regression
P0 actor-input contract unchanged
allowed changed-parameter surface pass
M297/M270 exact gate pass from full public wrapper
old public replay pass
M1061 family-intersection pass
source-diverse diagnostic pass
fresh/OOD generalization diagnostic pass
behavior seeds pass
no PPO
no actor training
no promotion
no private holdout
```

The candidate may become a full-public-gate candidate only if all tiers pass.
Any failed tier rejects the candidate and routes to an audit of that tier.

## Pass/Fail Classification

Use these result classes:

```text
materialized_actor_update_full_public_gate_candidate:
  exact M1107 and expanded full public gate both pass.

materialized_actor_update_m1107_exact_regression:
  selected candidate no longer improves or retains the M1107 exact objective.

materialized_actor_update_contract_artifact:
  actor inputs or allowed changed-parameter surface fail.

materialized_actor_update_public_replay_washout:
  old public replay or family-intersection proof gates fail.

materialized_actor_update_source_or_generalization_regression:
  source-diverse, fresh/OOD, or behavior gates fail.

materialized_actor_update_gate_execution_failure:
  gate command fails or required artifact is missing.
```

## Non-Goals

M1111 and M1112 must not:

- promote the candidate;
- start PPO;
- tune from private holdout;
- change actor inputs;
- skip the exact M1107 check;
- switch candidate after seeing full-gate failure.

If M1112 passes, the next step should be an audit/synthesis milestone, not
automatic promotion. The candidate is an action-grounding posttrain candidate,
not a demonstrated new ideal driver.

## Decision

```text
materialized_actor_update_full_public_gate_design_admit_run
```

Next milestone:

```text
m1112-v4-public-base-materialized-actor-update-full-public-gate
```
