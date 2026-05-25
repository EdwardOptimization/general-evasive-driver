# M761 V4 Sequence Objective-Only Probe Implementation

## Purpose

M761 implements the no-PPO residual objective probe designed in M760.

The question is:

```text
Can a frozen-backbone residual head improve exact M758 sequence gap metrics
while leaving normal-history behavior effectively unchanged?
```

This milestone is diagnostic only:

```text
base actor frozen
residual head trained separately
no PPO
no driver checkpoint promotion
no actor-input change
```

## Implementation

M761 adds:

```text
src/autodrift/v4_sequence_objective_probe.py
tests/test_v4_sequence_objective_probe.py
```

The implementation:

```text
loads runs/m568_scaled_l3_bc_seed5660/checkpoint.pt;
freezes all base actor parameters;
reconstructs M755 positive sequence rows by replaying seed/fault/step metadata;
extracts frozen recurrent actor features for normal and intervention branches;
trains only a bounded residual head;
evaluates alpha ladder 0.02,0.05,0.10,0.20,0.50,1.00;
writes alpha_metrics.csv, objective_rows.csv, training_metrics.csv,
rejected_rows.csv, residual_head.pt, and summary.json.
```

The residual head has `4355` trainable parameters. The actor backbone checksum
before and after the run is identical:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_objective_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m761_v4_sequence_objective_probe \
  --device cpu \
  --epochs 40 \
  --seed 7610
```

Output:

```text
runs/m761_v4_sequence_objective_probe/summary.json
runs/m761_v4_sequence_objective_probe/alpha_metrics.csv
runs/m761_v4_sequence_objective_probe/objective_rows.csv
runs/m761_v4_sequence_objective_probe/training_metrics.csv
runs/m761_v4_sequence_objective_probe/rejected_rows.csv
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

## Evidence Summary

Registered result:

```text
result_class: v4_sequence_objective_probe_candidate

positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0

residual_parameter_count: 4355
epochs: 40
seed: 7610

candidate_alpha_count: 3
candidate_alphas:
  0.2
  0.5
  1.0

actor_backbone_changed: false
residual_only_training: true
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Best first passing alpha:

```text
alpha: 0.2
sample_count: 1213
normal_anchor_mse_mean: 0.000000111
normal_anchor_mse_p95: 0.000000294
first_action_drift_from_base_mean: 0.000480
first_action_drift_from_base_p95: 0.000939
normal_intervention_gap_mean: 0.029079
normal_intervention_gap_p10: 0.023874
gap_deficit_mean: 0.012637
gap_deficit_p95: 0.016976
target_gap_mean: 0.041716
hard_negative_available_fraction: 0.721352
normal_retention_pass: true
gap_lift_pass: true
exact_probe_candidate: true
```

Largest gap alpha:

```text
alpha: 1.0
normal_anchor_mse_mean: 0.000002785
normal_anchor_mse_p95: 0.000007354
first_action_drift_from_base_mean: 0.002401
first_action_drift_from_base_p95: 0.004697
normal_intervention_gap_mean: 0.047347
normal_intervention_gap_p10: 0.028827
gap_deficit_mean: 0.000000337
gap_deficit_p95: 0.0
normal_retention_pass: true
gap_lift_pass: true
exact_probe_candidate: true
```

## Supported Claims

M761 supports:

```text
1. The M755/M758 v4 sequence corpus can drive a frozen-backbone residual
   objective-only probe without reconstruction failures.

2. The residual head can increase exact normal-vs-intervention first-action
   gap metrics while staying within the registered normal-history drift gates.

3. The strongest passing alpha reduces the exact gap deficit nearly to zero on
   this public objective corpus.

4. Actor backbone parameters remain unchanged; the result is residual-only and
   not a base-driver update.
```

## Falsified Claims

M761 falsifies:

```text
1. The v4 sequence objective has no actor-coupling signal at all.

2. Any attempt to increase the sequence intervention gap necessarily causes
   normal first-action drift under the registered gates.

3. The M755/M758 reconstruction path is too fragile to support a residual
   objective-only probe.
```

M761 does not prove:

```text
1. Closed-loop replay gates will pass after applying the residual head.

2. PPO is safe.

3. The residual head should be promoted into the deployed driver.

4. The current-model/proxy faults are true four-wheel or single-wheel fault
   physics.
```

## Failure Taxonomy Summary

Primary:

```text
none
```

Residual risks:

```text
scenario_sampling_failure:
  hard-negative availability remains 0.721352, so hard-negative contrast is
  still sparse.

public_gate_overfit_risk:
  this probe optimizes and evaluates on the public M755/M758 objective corpus.

closed_loop_unknown:
  exact first-action objective metrics improved, but no closed-loop replay gate
  has audited the residual behavior yet.
```

Not observed:

```text
not metadata_artifact
not reconstruction_blocked
not contract_violation
not proof_washout
not training_instability
not promotion_gate_failure
```

## Public Gate Overfit Risk

The public-gate overfit risk remains real.

M761 is a positive objective-only probe, but the positive result is still on
the same public corpus that defined the exact objective. Therefore M761 can
admit an audit and possibly a closed-loop replay design, but it must not admit
PPO or promotion directly.

## Next Branch Decision

Decision:

```text
promote_to_m762_audit
```

M762 should audit:

```text
1. whether alpha 0.2, 0.5, or 1.0 is a sensible residual candidate;
2. whether the exact objective gains are likely useful for closed-loop replay;
3. whether sparse hard negatives require a source refresh before replay;
4. whether the next admissible step is closed-loop residual replay, a corpus
   refresh, or a stricter objective audit.
```

PPO and checkpoint promotion remain blocked.
