# M759 V4 Sequence Objective Sanity Audit

## Purpose

M759 audits the M758 exact/offline objective sanity result before any actor
update, PPO, checkpoint promotion, or simulator-fidelity claim.

The question is:

```text
Is M758 clean enough to justify designing a no-PPO objective-only probe?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M758 reconstructed all M755 positive groups:

```text
result_class: v4_sequence_objective_hard_negative_sparse

positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
duplicate_group_ids: 0
missing_normal_rows: 0
missing_source_snapshots: 0
rejected_rows: 0
normal_group_count: 1213

normal_anchor_mse_mean: 0.0
intervention_anchor_mse_mean: 0.0
normal_intervention_gap_mean: 0.024908
normal_intervention_gap_p10: 0.021141
target_gap_mean: 0.041716
gap_deficit_mean: 0.016809
gap_deficit_p95: 0.021590

hard_negative_available_fraction: 0.721352
hard_negative_sparse: true
claim_boundary_levels:
  current_model_or_proxy

training_started: false
optimizer_started: false
checkpoint_loaded_for_eval_only: true
ppo_used: false
promoted: false
actor_parameters_changed: false
```

## Supported Claims

M759 supports:

```text
1. M758 is a valid no-training exact objective sanity result.

2. The M755 corpus can be reconstructed into replayable objective samples:
   1213/1213 rows reconstructed with no missing metadata, normal rows, or
   source snapshots.

3. The objective is not degenerate: normal-vs-intervention gap mean is
   0.024908 and p10 is 0.021141.

4. A no-PPO objective-only probe design is now admissible.

5. Hard-negative sparsity remains real and must shape the next design.
```

## Falsified Claims

M759 falsifies:

```text
1. The M755 corpus cannot be reconstructed into objective samples.

2. The v4 sequence objective is immediately degenerate at the base checkpoint.

3. Hard-negative sparsity should block all objective design.
```

M759 does not prove:

```text
1. An actor update will improve behavior.

2. An actor update can preserve public proof gates.

3. PPO is safe to run.

4. The current-model/proxy faults are true four-wheel or single-wheel failure
   physics.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
M758's exact reconstruction and metrics pass, but hard-negative availability is
only 0.721352. Objective design must treat hard negatives as optional sparse
contrast instead of a required row for every positive.
```

Not failures:

```text
not reconstruction_blocked
not metadata_artifact
not objective_degenerate
not contract_violation
not proof_washout
not promotion_gate_failure
not training_instability
```

## Public Gate Overfit Risk

The public-gate overfit risk remains high if an update directly optimizes M755
rows without exact gates.

Reasons:

```text
1. M755/M758 are public diagnostics.
2. The positive corpus is dominated by zero_command_obs at longer horizons.
3. The exact sanity metrics are evaluated on the same corpus that would drive
   the objective.
4. There is not yet a post-update closed-loop gate.
```

Mitigation:

```text
M760 should be design-only.
M760 should require exact before/after objective metrics, normal-retention
gates, first-action safety gates, source-stratified reporting, and no PPO.
Any M761 implementation should be objective-only, small-step, and auditable
before replay or promotion.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v4_sequence_objective_only_probe_design
```

Rationale:

```text
M758 proves the corpus can be reconstructed and the objective is numerically
well formed. The next research question is whether a small objective-only probe
can move the proposed exact metrics without normal-history behavior drift.
```

M760 should design:

```text
1. a no-PPO objective-only probe;
2. frozen or tightly anchored base actor behavior;
3. exact before/after M758 metrics;
4. alpha/interpolation ladder if any actor parameters are updated;
5. normal first-action drift and normal sequence retention gates;
6. sparse hard-negative handling;
7. no checkpoint promotion.
```

PPO should remain blocked until an objective-only probe is implemented, audited,
and shown not to wash out proof surfaces.
