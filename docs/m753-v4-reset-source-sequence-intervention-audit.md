# M753 V4 Reset-Source Sequence Intervention Audit

## Purpose

M753 audits the M752 positive diagnostic before converting it into any corpus,
objective, or training recipe.

The question is:

```text
Is M752's v4_reset_sequence_outcome_positive result clean enough to justify a
sentinel-filtered v4 sequence-outcome corpus export design?
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

M752 passed the registered source, action, outcome, sentinel, and actor-safety
checks:

```text
result_class: v4_reset_sequence_outcome_positive
base_result_class: sequence_outcome_positive

source_candidate_rows: 512
source_reset_rows: 461
source_sentinel_rows: 51
source_unique_seeds: 31
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 7
source_unique_fault_family_pairs: 21
source_max_seed_dominance: 0.121094
source_max_preferred_family_dominance: 0.126953
source_sentinel_fraction: 0.099609

sequence_action_critical_rows: 5429
sequence_outcome_critical_rows: 1213
unique_sequence_action_seeds: 31
unique_sequence_outcome_seeds: 27
unique_sequence_outcome_fault_family_pairs: 17
max_sequence_outcome_seed_dominance: 0.171476

sentinel_rows: 1224
sentinel_false_positive_rows: 0
sentinel_false_positive_rate: 0.0
normal_history_retention_pass: true
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Compared with M749:

```text
M749 wrong-history action rows: 0
M749 reset-only rows: 1171
M752 sequence outcome rows: 1213
```

So the evidence increment is substantial: persistent command-response
interventions on the v4 reset surface convert a reset-only source surface into
many closed-loop outcome-sensitive rows.

## Variant And Horizon Effects

Outcome rows by variant:

```text
zero_command_obs: 1044
reset_hidden_each_step: 169
```

Outcome rows by horizon:

```text
H=2: 25
H=4: 168
H=6: 455
H=8: 565
```

This supports the interpretation:

```text
brief interventions are often recovered by feedback, but sustained corruption
of command-response history changes terminal clearance and success.
```

The strongest variant is `zero_command_obs`, which targets the human-view
closed-loop command-response channel directly.

## Supported Claims

M753 supports:

```text
1. M752 is a valid diagnostic positive result.

2. Broader v4 current-model/proxy extreme-fault coverage plus sequence-level
   command-response intervention exposes source-diverse outcome sensitivity.

3. The M749 reset-only surface was not a dead end; it contained useful
   closed-loop history dependence once tested with persistent interventions.

4. The user's coverage hypothesis is supported: earlier negative results could
   plausibly be caused by insufficient or poorly targeted extreme-scenario
   mining rather than by the absence of self-ID evidence.

5. The positive rows are clean enough to justify a sentinel-filtered v4 corpus
   export design.
```

## Falsified Claims

M753 falsifies:

```text
1. The v4 reset-only result means the current actor has no useful closed-loop
   history dependence.

2. The project must immediately jump to simulator fidelity before preserving
   the M752 positive corpus.

3. M752 can be used directly for PPO or checkpoint promotion.
```

M753 does not prove:

```text
1. A trained policy improves after learning from M752 rows.

2. The result generalizes to private holdout or higher-fidelity vehicle models.

3. The current two-wheel/current-proxy faults prove true single-wheel blowout,
   split-mu, stuck caliper, halfshaft-break, or per-wheel brake physics.

4. Reset-only rows are equivalent to wrong-history self-identification proof.
```

## Failure Taxonomy Summary

Primary:

```text
none
```

Reason:

```text
M752 passed source-balance, sequence-action, sequence-outcome, sentinel, normal
retention, and actor checksum gates.
```

Residual risks:

```text
public_gate_overfit:
  M752 is still a public diagnostic wave and should be exported/audited before
  objective design.

claim_boundary:
  V4 contains current-model/proxy faults plus future-only labels. Current
  results must not be overclaimed as true per-wheel or four-wheel failure
  physics.

hard_negative_sparsity_unknown:
  The sequence-positive surface is abundant, but same-source/same-horizon
  hard-negative availability has not yet been exported or audited.
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate.

Reasons:

```text
1. M752 rows are public diagnostics.
2. Positive rows are now abundant and easy to overfit with an objective.
3. The strongest variant is known to be zero_command_obs at longer horizons.
4. Outcome rows cover fewer fault-family pairs than v3 M743 despite more rows:
   M752 has 17 pairs; M743 had 26 pairs.
```

Mitigation:

```text
Export a compact sentinel-filtered corpus first.
Keep normal, positive, sentinel, variant, horizon, source, and v4 claim-boundary
metadata intact.
Do not run PPO or actor update until a later objective sanity gate exists.
Do not treat the exported corpus as private holdout.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v4_sequence_outcome_corpus_export
```

Rationale:

```text
M752 is too strong to leave as only a run directory, but it is still diagnostic.
The next step should preserve positive rows as an auditable v4-aware corpus
before any objective or PPO work.
```

M754 should design a v4-aware corpus export that:

```text
1. filters sentinel rows from positives;
2. keeps only sequence_outcome_critical positives;
3. preserves source_kind, source_pool, claim_boundary_level, pair_id,
   pairing_rule, reset_action_l2_gap, reset_margin_gap, action_l2_gap,
   history_margin_gap, match_distance, source_role, fault families, severity,
   and future-only claim-boundary metadata;
4. includes matched normal rows;
5. records hard-negative action-only rows separately;
6. reports source, variant, horizon, seed, fault-family, and sentinel balance;
7. blocks objective training, PPO, and promotion.
```

Recommended minimum corpus targets:

```text
positive_rows >= 1000
positive_sentinel_rows == 0
unique_positive_seeds >= 24
unique_positive_fault_family_pairs >= 16
matched_normal_rows == positive_rows
sentinel_false_positive_rows_exported_as_positive == 0
```

Objective design should remain a later audit decision.
