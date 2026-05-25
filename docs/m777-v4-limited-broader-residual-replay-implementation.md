# M777 V4 Limited Broader Residual Replay Implementation

## Purpose

M777 runs the limited no-PPO residual replay admitted by M776 synthesis on the
broader M773 source-holdout corpus.

The question is:

```text
Does the M761 residual head transfer to the broader M773 corpus while preserving
normal behavior at the conservative alpha 0.2?
```

This run is replay-only:

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
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m777_v4_limited_broader_residual_replay \
  --device cpu \
  --alphas 0.0,0.2,0.5,1.0
```

## Evidence Summary

Registered result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 2652
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

replay_rows: 21120
objective_rows: 10560
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

The script-level candidate gate passes for alpha `0.2`, `0.5`, and `1.0`.
However, the stricter M775 pre-registered normal-retention gate does not fully
pass because all nonzero alphas introduce one unique normal-branch collision
source.

## Rejected Rows

Rejected rows:

```text
rejected_rows: 12
reason: unsupported_variant:command_shift_obs
affected seeds:
  77025
affected sources:
  source_index 3
  source_index 12
  source_index 93
```

This is not metadata loss:

```text
metadata_missing_rows: 0
```

## Alpha Metrics

Base alpha:

```text
alpha 0.0:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_success_rate: 0.986364
  intervention_collision_rate: 0.013636
  intervention_action_gap_mean/p10: 0.040348 / 0.025782
  margin_gap_mean: 0.029796
```

Primary alpha:

```text
alpha 0.2:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  normal_margin_regression_mean/p95_vs_base: 0.000353 / 0.001418
  normal_first_action_drift_mean/p95_vs_base: 0.000391 / 0.000938
  intervention_action_gap_mean/p10: 0.046317 / 0.027627
  margin_gap_mean: 0.033918
  outcome_sensitivity_retention_rate: 1.000000
  intervention_success_rate: 0.986364
  intervention_collision_rate: 0.013636
  script_closed_loop_replay_candidate: true
```

Diagnostic alphas:

```text
alpha 0.5:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  normal_first_action_drift_mean/p95_vs_base: 0.000978 / 0.002344
  intervention_action_gap_mean/p10: 0.055697 / 0.030935
  margin_gap_mean: 0.040438
  script_closed_loop_replay_candidate: true

alpha 1.0:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  normal_first_action_drift_mean/p95_vs_base: 0.001956 / 0.004688
  intervention_action_gap_mean/p10: 0.072106 / 0.036748
  margin_gap_mean: 0.052275
  script_closed_loop_replay_candidate: true
```

## Strict Gate Audit

M775 stricter alpha `0.2` gate:

```text
sample_reconstruction_success_rate >= 0.98:
  0.995475 -> pass

metadata_missing_rows == 0:
  0 -> pass

normal_success_rate == 1.0:
  0.995455 -> fail

normal_collision_rate == 0.0:
  0.004545 -> fail

intervention_action_gap_mean > base:
  0.046317 > 0.040348 -> pass

margin_gap_mean > base:
  0.033918 > 0.029796 -> pass

outcome_sensitivity_retention_rate == 1.0:
  1.0 -> pass

actor/training/PPO/promotion flags false:
  pass
```

Interpretation:

```text
The residual mechanism transfers to the broader corpus in the sense that it
increases action-gap and margin-gap metrics monotonically. It does not satisfy
the stricter normal-retention standard because the broader corpus reveals a
small but real normal-branch collision source.
```

## Normal Collision Concentration

All nonzero alpha normal collisions concentrate in one unique source:

```text
alpha 0.2 normal collision rows: 12
unique alpha 0.2 collision sources: 1

seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
terminal_reason: collision
min_clearance_margin at alpha 0.2: -0.000062
```

The same unique source fails for alpha `0.5` and `1.0`, with larger negative
margins:

```text
alpha 0.5 min_clearance_margin: -0.000370
alpha 1.0 min_clearance_margin: -0.000972
```

This looks like a near-boundary normal branch cliff, not broad normal behavior
collapse. It still blocks a strict pass until audited.

## Supported Claims

M777 supports:

```text
1. The residual action/margin separation signal transfers to the broader M773
   corpus: alpha 0.2 improves intervention action gap and margin gap over base.

2. The replay path works at broader scale: 2640/2652 rows reconstruct with no
   metadata misses and no actor/training/PPO mutation.

3. The broader corpus is useful: it exposes a normal-retention boundary source
   that M770's sparse holdout did not reveal.
```

## Falsified Claims

M777 falsifies:

```text
1. The residual signal disappears completely on the broader corpus.

2. Broader residual replay is purely a routing or reconstruction artifact.

3. Alpha 0.2 cleanly satisfies the stricter M775 normal-retention gate on M773.
```

M777 does not prove:

```text
1. Broad generalization.

2. Driver promotion readiness.

3. PPO safety.

4. Strict normal-retention pass on the broader corpus.

5. True four-wheel or single-wheel physical fidelity.
```

## Failure Taxonomy

Primary classification:

```text
behavior_regression
```

Reason:

```text
M775 required normal_success_rate == 1.0 and normal_collision_rate == 0.0 for
alpha 0.2. M777 alpha 0.2 has normal_success_rate 0.995455 and normal_collision
rate 0.004545.
```

Secondary risk:

```text
scenario_sampling_failure
```

Reason:

```text
The normal collision is concentrated in one source and one fault-family pair,
so the next step should audit whether this is a repairable near-boundary row or
a systematic broader-corpus retention problem.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not training_instability
not promotion_gate_failure
```

## Decision

M777 admits audit only:

```text
m778-v4-limited-broader-residual-replay-audit
```

M778 should decide whether to:

```text
1. treat source 12 / seed 77025 as a near-boundary repair target;
2. design an alpha below 0.2 only after audit, not by retroactive tuning;
3. return to source-balanced or targeted fault-pair mining;
4. revise the residual objective to include stricter normal-margin retention.
```

PPO, training, promotion, and alpha retuning remain blocked.
