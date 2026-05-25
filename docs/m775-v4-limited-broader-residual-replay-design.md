# M775 V4 Limited Broader Residual Replay Design

## Purpose

M775 designs a limited no-PPO residual replay on the broader M773 source-holdout
corpus.

The question for the next implementation is:

```text
Does the M761 residual self-ID mechanism transfer from the sparse M767 holdout
to the larger M773 broader corpus while preserving normal behavior?
```

This milestone is design-only:

```text
no replay run
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Inputs

Fixed actor checkpoint:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

Fixed residual head:

```text
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

Broader corpus:

```text
runs/m773_v4_broader_source_holdout_corpus_export/summary.json
runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv
runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
```

Scenario config:

```text
configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
```

M773 caveats to preserve:

```text
result_class: v4_sequence_outcome_corpus_hard_negative_sparse
positive_rows: 2652
unique_positive_seeds: 49
unique_positive_fault_family_pairs: 17
max_positive_seed_dominance: 0.171569
max_positive_fault_family_pair_dominance: 0.208145
hard_negative_rows: 2134
positives_without_hard_negative: 872
claim_boundary_level: current_model_or_proxy
```

## Registered Post-Synthesis Replay Command

The next implementation should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m776_v4_limited_broader_residual_replay \
  --device cpu \
  --alphas 0.0,0.2,0.5,1.0
```

## Alpha Policy

Pre-registered alpha interpretation:

```text
alpha 0.0:
  base diagnostic, not a candidate

alpha 0.2:
  primary conservative broader-holdout candidate

alpha 0.5:
  diagnostic stronger residual

alpha 1.0:
  aggressive diagnostic only
```

Do not tune alpha from M773 results. Do not promote any alpha in M776.

## Required M776 Metrics

The implementation must report:

```text
reconstructed_rows
sample_reconstruction_success_rate
metadata_missing_rows
rejected_rows
replay_rows
objective_rows
candidate_alphas
actor_backbone_changed
optimizer_started
training_started
ppo_used
promoted
```

For each alpha:

```text
normal_success_rate
normal_collision_rate
normal_margin_regression_mean
normal_margin_regression_p95
normal_first_action_drift_mean
normal_first_action_drift_p95
intervention_action_gap_mean
intervention_action_gap_p10
margin_gap_mean
outcome_sensitivity_retention_rate
intervention_success_rate
intervention_collision_rate
closed_loop_replay_candidate
```

M776 must also report stratification:

```text
seed concentration
fault-family-pair concentration
variant and horizon metrics
dominant collision seeds
dominant collision fault pairs
hard-negative sparsity caveat
current_model_or_proxy claim boundary
```

## Candidate Gates

Primary alpha `0.2` is only a limited broader replay candidate if the
post-synthesis implementation reports:

```text
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
normal_success_rate == 1.0
normal_collision_rate == 0.0
normal_first_action_drift_p95 remains small relative to M770/M764 scale
intervention_action_gap_mean > base alpha 0.0
margin_gap_mean > base alpha 0.0
outcome_sensitivity_retention_rate == 1.0
actor_backbone_changed == false
optimizer_started == false
training_started == false
ppo_used == false
promoted == false
```

Even if alpha `0.2` passes, M776 can only claim:

```text
limited broader-corpus residual replay support
```

It cannot claim:

```text
broad generalization
promotion readiness
PPO safety
true single-wheel or four-wheel physical fidelity
```

## Failure Classification

If alpha `0.2` fails normal retention:

```text
failure_type: behavior_regression
next: audit before changing alpha or residual objective
```

If alpha `0.2` does not improve intervention sensitivity:

```text
failure_type: objective_overfit
next: audit public/holdout mismatch and residual objective alignment
```

If only alpha `0.5` or `1.0` passes:

```text
failure_type: scenario_sampling_failure
next: audit whether M773 concentration requires source-balanced replay
```

If candidate metrics are dominated by one seed or pair:

```text
failure_type: scenario_sampling_failure
next: source-balanced or targeted pair mining before stronger claims
```

## Workflow Cadence

The branch has reached the workflow synthesis cadence. Therefore M775 does not
directly admit the replay implementation, even though the command is defined.
The next required milestone is a synthesis gate:

```text
m776-v4-residual-source-holdout-replay-synthesis
```

If M776 synthesis decides to continue, the replay implementation should be:

```text
m777-v4-limited-broader-residual-replay-implementation
```

The implementation may only run the registered no-PPO replay command. PPO,
actor/residual training, checkpoint promotion, and alpha retuning remain
blocked.
