# M756 V4 Sequence-Outcome Corpus Export Audit

## Purpose

M756 audits the M755 v4 corpus export before any objective design, actor update,
PPO, checkpoint promotion, or simulator-fidelity claim.

The question is:

```text
Is M755's v4 sequence-outcome corpus clean enough to preserve, and can it admit
a constrained objective-design branch despite sparse hard negatives?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint loading
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M755 exported a clean positive corpus:

```text
result_class: v4_sequence_outcome_corpus_hard_negative_sparse

positive_rows: 1213
positive_sentinel_rows: 0
positive_source_role_sentinel_rows: 0
sentinel_false_positive_rows_exported_as_positive: 0
duplicate_positive_keys: 0
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0

unique_positive_seeds: 27
unique_positive_fault_family_pairs: 17
max_positive_seed_dominance: 0.171476
max_positive_fault_family_pair_dominance: 0.136026

contrast_groups: 1213
normal_rows: 1213
positive_intervention_rows: 1213
hard_negative_rows: 1009
positives_without_hard_negative: 338

positive_corpus_gate_pass: true
v4_metadata_gate_pass: true

training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

Coverage by variant and horizon:

```text
variant:
  zero_command_obs: 1044
  reset_hidden_each_step: 169

horizon:
  H=2: 25
  H=4: 168
  H=6: 455
  H=8: 565
```

V4 claim boundary:

```text
claim_boundary_level:
  current_model_or_proxy
future_only_fault_count: 14
current_model_fault_count: 8
current_model_proxy_fault_count: 20
positive_source_kinds:
  v4_reset_source
positive_source_pools:
  m749_v4_reset_only
```

## Supported Claims

M756 supports:

```text
1. M755 is a valid, auditable, v4-aware positive corpus export.

2. M752's sequence-intervention evidence was not lost: the corpus preserves
   `1213` non-sentinel outcome-sensitive rows with matched normal rows.

3. The coverage-mining hypothesis is now supported by the M749 -> M752 -> M755
   chain:
     M749: 1171 reset-only rows, 0 wrong-history action rows
     M752: 1213 sequence outcome rows
     M755: 1213 clean exported positives

4. The current corpus is suitable for a constrained objective-design branch
   that treats hard negatives as optional/sparse contrast rows.

5. The corpus should not be treated as a complete positive-vs-action-only
   hard-negative contrast corpus.
```

## Falsified Claims

M756 falsifies:

```text
1. The v4 reset-only branch was a dead end.

2. The M755 hard-negative sparsity invalidates the positive corpus.

3. M752/M755 can be ignored in favor of immediate simulator-fidelity work.
```

M756 does not prove:

```text
1. A trained driver improves after learning from the M755 corpus.

2. PPO can retain these rows without proof washout.

3. The current model/proxy faults are true single-wheel blowout, split-mu,
   stuck-caliper, halfshaft-break, per-wheel ABS, or suspension-damage physics.

4. The current public corpus is enough for paper-level generalization evidence.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
M755's positive corpus is clean, but the hard-negative contrast set is sparse
(`1009 < 1213`) and `338` positives lack a same-source/same-horizon action-only
hard-negative candidate.
```

Residual risks:

```text
public_gate_overfit:
  M755 positives are public diagnostics derived from the M752 wave.

claim_boundary:
  V4 contains current-model/proxy capability faults plus future-only labels, but
  not true four-wheel asymmetric failure physics.

hard_negative_sparsity:
  Complete positive-vs-action-only contrast design needs repair or a loss that
  treats hard negatives as optional.
```

Not failures:

```text
not contract_violation
not proof_washout
not promotion_gate_failure
not metric_artifact
not training_instability
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate to high if objective work starts
immediately.

Reasons:

```text
1. The `1213` positives are all from one public M752 run family.
2. The strongest mechanism is dominated by `zero_command_obs` at long horizons.
3. The corpus is large enough to overfit if it becomes a direct supervised loss.
4. Hard negatives are sparse, so a naive contrastive objective would overweight
   rows with available action-only negatives.
```

Mitigation:

```text
M757 should be design-only.
The objective should separate positive-vs-normal retention from optional
hard-negative contrast.
Any implementation should start with exact/offline objective sanity, not PPO.
No checkpoint promotion is allowed before an audit and closed-loop gates.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v4_sequence_objective_design
```

Rationale:

```text
M755 is clean enough to preserve and is now broader than the v3 corpus on
positive count and seed diversity. It is appropriate to design an objective that
uses the positive rows while explicitly acknowledging hard-negative sparsity.
```

M757 should design a constrained v4 sequence objective that:

```text
1. uses M755 positives with matched normal rows as the required contrast;
2. treats hard_negative_action_only rows as optional sparse contrast, not as a
   required row for every positive;
3. preserves normal-history behavior and first-step safety;
4. keeps v4 claim-boundary metadata in every objective batch;
5. reports exact full-corpus losses before any actor update;
6. blocks PPO and checkpoint promotion;
7. blocks true four-wheel/single-wheel physical claims.
```

The objective-design branch should remain separate from PPO continuation.
