# M1000 V4 Public Base Temporal Sequence Objective Evaluator

## Purpose

M1000 implements the exact no-update evaluator designed in M999.

It evaluates the M997 temporal sequence corpus under the M974 public base and
does not train, run PPO, promote a checkpoint, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_temporal_sequence_objective \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --metadata runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv \
  --run-dir runs/m1000_v4_public_base_temporal_sequence_objective_evaluator
```

## Result

```text
result_class: temporal_sequence_objective_evaluator_pass
row_count: 277
positive_row_count: 277
sequence_length_mean: 46.790615
sequence_length_min: 29
sequence_length_max: 48
row_weight_mean: 1.0
normal_action_replay_l2_max: 0.0
finite_metrics: true
mask_sanity_passed: true
weight_sanity_passed: true
replay_sanity_passed: true
exact_objective_sanity_passed: true
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

## Objective Metrics

Unweighted metrics:

```text
normal_sequence_logp_sum_mean: 63.870464
variant_on_normal_sequence_logp_sum_mean: 30.271999
normal_sequence_nll_mean: -1.365235
variant_on_normal_sequence_nll_mean: -0.651213
temporal_preference_loss_mean: 0.470187
temporal_logp_gap_sum_mean: 33.598469
temporal_logp_gap_mean: 0.714021
temporal_logp_gap_p10: 0.053981
temporal_logp_gap_p50: 0.419248
temporal_logp_gap_p90: 1.734969
```

Weighted metrics:

```text
weighted_normal_sequence_nll: -1.373014
weighted_temporal_preference_loss: 0.491601
weighted_logp_gap_mean: 0.640106
weighted_base_logp_anchor: 0.0
weighted_total_loss: -0.881413
```

The `weighted_base_logp_anchor` is zero because this is the baseline checkpoint
evaluated against itself. Future actor-update probes should compute the same
metrics for candidate checkpoints and require exact non-regression gates before
any replay gates.

## Interpretation

The M997 corpus is usable for exact objective work:

```text
normal uninterrupted history has a positive per-step log-prob gap over
temporally disrupted history on the normal safe sequence.
```

But this is still a no-update objective sanity result. It does not prove that an
actor update will improve behavior without proof washout.

## Variant Counts

```text
reset_then_warm_history: 253
delayed_capability_history: 24
```

The evaluator uses `row_weight`, so later objective probes have an explicit way
to reduce domination by the reset-then-warm group.

## Guardrails Preserved

```text
No hidden fault labels are actor inputs.
No diagnostic cross-fault rows are positive targets.
Variant histories are contrast-only.
No actor parameters changed.
No PPO or promotion occurred.
```

## Decision

```text
temporal_sequence_objective_evaluator_pass_route_to_update_design
```

Next:

```text
m1001-v4-public-base-temporal-sequence-objective-update-design
```

The next milestone should design a tiny objective-only actor update and its
exact/public replay gates. It should not run the update yet.
