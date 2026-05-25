# M770 V4 Limited Residual Holdout Replay Implementation

## Purpose

M770 runs the limited no-PPO residual replay designed in M769 on the fresh but
sparse M767 source-holdout corpus.

The question is:

```text
Does the M761 residual closed-loop mechanism signal transfer to fresh
disjoint-seed source rows under limited-holdout caveats?
```

This milestone is diagnostic only:

```text
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Registered Run

Command:

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

## Evidence Summary

Registered result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 995
reconstructed_rows: 995
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0

replay_rows: 7960
objective_rows: 3980
candidate_alpha_count: 3
candidate_alphas:
  0.2
  0.5
  1.0

actor_backbone_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Actor checksum remained unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Alpha Metrics

Base alpha:

```text
alpha 0.0:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_success_rate: 0.979899
  intervention_collision_rate: 0.020101
  intervention_action_gap_mean/p10: 0.043862 / 0.039491
  margin_gap_mean: 0.026641
```

Primary holdout alpha:

```text
alpha 0.2:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_margin_regression_mean/p95_vs_base: 0.000153 / 0.001002
  normal_first_action_drift_mean/p95_vs_base: 0.000553 / 0.001208
  intervention_action_gap_mean/p10: 0.050473 / 0.045717
  margin_gap_mean: 0.030329
  outcome_sensitivity_retention_rate: 1.000000
  intervention_success_rate: 0.976884
  intervention_collision_rate: 0.023116
  closed_loop_replay_candidate: true
```

Diagnostic alphas:

```text
alpha 0.5:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_first_action_drift_mean/p95_vs_base: 0.001383 / 0.003020
  intervention_action_gap_mean/p10: 0.060874 / 0.055506
  margin_gap_mean: 0.036110
  intervention_collision_rate: 0.028141
  closed_loop_replay_candidate: true

alpha 1.0:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_first_action_drift_mean/p95_vs_base: 0.002766 / 0.006041
  intervention_action_gap_mean/p10: 0.079103 / 0.072538
  margin_gap_mean: 0.046439
  intervention_collision_rate: 0.031156
  closed_loop_replay_candidate: true
```

## Collision Concentration

The normal branch has zero collisions for every alpha.

The intervention branch already has collisions at base alpha `0.0`:

```text
alpha 0.0:
  intervention collisions: 20 / 995
  dominant seed: 76519
  dominant preferred fault family: combined_fault
  dominant wrong families: global_mu_drop, brake_authority_drop
```

Residual alpha increases wrong/ablated-history branch sensitivity:

```text
alpha 0.2:
  intervention collisions: 23 / 995
  added collision concentration:
    seed 76521
    seed 76573
    preferred_fault_family front_lateral_authority_drop
    wrong_fault_family combined_fault

alpha 1.0:
  intervention collisions: 31 / 995
```

This is mechanism evidence, not normal-driver failure, but it must be audited
because the collision rows are source-concentrated.

## Supported Claims

M770 supports:

```text
1. The M761 residual mechanism signal transfers to a fresh disjoint-seed holdout
   corpus under limited/sparse-source caveats.

2. Alpha 0.2, the pre-registered primary holdout alpha, passes closed-loop
   candidate gates.

3. Normal branch behavior is retained on the fresh holdout: 995/995 normal
   success and 0 normal collisions for every alpha.

4. Intervention action gap and margin gap increase monotonically with alpha.
```

## Falsified Claims

M770 falsifies:

```text
1. The M761 residual signal is purely public-corpus overfit.

2. Alpha 0.2 fails immediately on fresh source rows.

3. Residual replay necessarily damages normal branch success on this holdout.
```

M770 does not prove:

```text
1. Broad generalization.

2. Promotion readiness.

3. PPO safety.

4. True four-wheel / single-wheel physical fault fidelity.
```

## Failure Taxonomy Summary

Primary residual risk:

```text
scenario_sampling_failure
```

Reason:

```text
The holdout corpus is fresh and positive, but sparse and source-concentrated.
M770 is a limited holdout mechanism positive, not a broad generalization gate.
```

Additional audit risk:

```text
subgroup_concentration:
  intervention collisions concentrate in a small number of seeds and fault
  family pairs.
```

Not failures:

```text
not metadata_artifact
not reconstruction_blocked
not private_holdout_contamination
not contract_violation
not training_instability
not promotion_gate_failure
```

## Next Branch Decision

Decision:

```text
limited_residual_holdout_replay_candidate_admit_audit
```

M771 should audit whether M770 is enough to continue toward broader
source-holdout coverage, or whether the collision/source concentration requires
another source-balanced fresh wave before further residual replay.

PPO and checkpoint promotion remain blocked.
