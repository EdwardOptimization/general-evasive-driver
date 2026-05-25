# M769 V4 Limited Residual Holdout Replay Design

## Purpose

M769 designs the limited no-PPO residual replay on the fresh but sparse M767
source-holdout corpus.

The question is:

```text
Does the M761 residual closed-loop mechanism signal transfer to a disjoint-seed
fresh holdout corpus, under limited/sparse-source caveats?
```

This milestone is design-only:

```text
no replay run
no actor training
no residual retraining
no PPO
no checkpoint promotion
```

## Inputs

M770 should use:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
runs/m767_v4_source_holdout_corpus_export/positive_sequence_outcomes.csv
runs/m767_v4_source_holdout_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_scenarios.json
```

The holdout corpus is fresh relative to M761 by seed range, but sparse:

```text
positive_rows: 995
unique_positive_seeds: 25
unique_positive_fault_family_pairs: 13
max_positive_seed_dominance: 0.247236
```

Therefore M770 may only claim limited holdout evidence.

## Alpha Plan

M770 should run:

```text
alpha 0.0: base actor
alpha 0.2: primary conservative residual alpha
alpha 0.5: diagnostic residual alpha
alpha 1.0: aggressive diagnostic residual alpha
```

Alpha `0.2` is the primary candidate because M765 found it conservative on the
public corpus. Alpha `0.5` and `1.0` must not be selected after seeing holdout
results and then presented as unbiased primary alphas.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m767_v4_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m767_v4_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m770_v4_limited_residual_holdout_replay \
  --device cpu \
  --alphas 0.0,0.2,0.5,1.0
```

## Pass/Fail Framing

M770 should reuse M764's closed-loop replay gates, but the result class must be
interpreted with M767/M768 caveats:

```text
positive:
  limited source-holdout mechanism positive

negative:
  limited holdout failure or source-sparsity-limited failure

not allowed:
  promotion
  PPO admission
  broad generalization claim
```

Required reporting:

```text
sample_reconstruction_success_rate
metadata_missing_rows
normal_success_rate
normal_collision_rate
normal_first_action_drift_mean/p95_vs_base
intervention_action_gap_mean/p10_vs_normal
normal_minus_intervention_margin_gap_mean
outcome_sensitivity_retention_rate
variant/horizon/fault-family stratification
intervention collision concentration
actor checksum unchanged
optimizer_started == false
ppo_used == false
promoted == false
```

## Stop Rules

M770 must stop and report a clean negative/blocker if:

```text
reconstruction_success_rate < 0.98
metadata_missing_rows > 0
normal branch regresses broadly
alpha 0.2 fails and stronger alphas only pass by becoming aggressive
actor checksum changes
optimizer/PPO/promotion starts
```

## Next Step

Decision:

```text
admit_m770_limited_residual_holdout_replay_implementation
```

M770 should run the no-PPO limited holdout replay. Any result must be audited by
M771 before further source waves, objective redesign, PPO, or promotion.
