# M744 V3 Reset-Source Sequence Intervention Audit

## Purpose

M744 audits the M743 positive diagnostic before converting it into any corpus,
objective, or training recipe.

The question is:

```text
Is M743's v3_reset_sequence_outcome_positive result clean enough to justify a
sentinel-filtered v3 sequence-outcome corpus export design?
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

M743 passed the registered source, action, outcome, sentinel, and actor-safety
checks:

```text
result_class: v3_reset_sequence_outcome_positive

source_candidate_rows: 512
source_reset_rows: 461
source_sentinel_rows: 51
source_unique_seeds: 25
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 8
source_unique_fault_family_pairs: 30
source_max_seed_dominance: 0.134766
source_max_preferred_family_dominance: 0.123047
source_sentinel_fraction: 0.099609

sequence_action_critical_rows: 5304
sequence_outcome_critical_rows: 995
unique_sequence_action_seeds: 25
unique_sequence_outcome_seeds: 20
unique_sequence_outcome_fault_family_pairs: 26
max_sequence_outcome_seed_dominance: 0.169849

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

Compared with M740:

```text
M740 wrong-history action rows: 0
M740 reset-only rows: 744
M743 sequence outcome rows: 995
```

So the evidence increment is substantial: persistent command-response
interventions on the v3 reset surface convert a reset-only source surface into
many closed-loop outcome-sensitive rows.

## Variant And Horizon Effects

Outcome rows by variant:

```text
zero_command_obs: 950
reset_hidden_each_step: 45
```

Outcome rows by horizon:

```text
H=2: 3
H=4: 145
H=6: 370
H=8: 477
```

This supports the interpretation:

```text
brief interventions are often recovered by feedback, but sustained corruption
of command-response history changes terminal clearance and success.
```

The strongest variant is `zero_command_obs`, which targets the human-view
closed-loop command-response channel directly.

## Supported Claims

M744 supports:

```text
1. M743 is a valid diagnostic positive result.

2. Broader v3 extreme-fault coverage plus sequence-level command-response
   intervention exposes source-diverse outcome sensitivity.

3. The M740 reset-only surface was not a dead end; it contained useful
   closed-loop history dependence once tested with persistent interventions.

4. The positive rows are clean enough to justify a sentinel-filtered v3 corpus
   export design.
```

## Falsified Claims

M744 falsifies:

```text
1. The v3 reset-only result means the current actor has no useful closed-loop
   history dependence.

2. The project must immediately jump to simulator fidelity before preserving
   the M743 positive corpus.

3. M743 can be used directly for PPO or checkpoint promotion.
```

M744 does not prove:

```text
1. A trained policy improves after learning from M743 rows.

2. The result generalizes to private holdout or higher-fidelity vehicle models.

3. The current single-track proxy faults prove true single-wheel blowout or
   halfshaft-break physics.
```

## Failure Taxonomy Summary

Primary:

```text
none
```

Reason:

```text
M743 passed source-balance, sequence-action, sequence-outcome, sentinel, normal
retention, and actor checksum gates.
```

Residual risks:

```text
public_gate_overfit:
  M743 is still a public diagnostic wave and should be exported/audited before
  objective design.

claim_boundary:
  V3 faults include single-track proxies and must not be overclaimed as true
  per-wheel failure physics.
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate.

Reasons:

```text
1. M743 rows are public diagnostics.
2. Positive rows are now abundant and easy to overfit with an objective.
3. The strongest variant is known to be zero_command_obs at longer horizons.
```

Mitigation:

```text
Export a compact sentinel-filtered corpus first.
Keep normal, positive, sentinel, variant, horizon, source, and v3-fidelity
metadata intact.
Do not run PPO or actor update until a later objective sanity gate exists.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v3_sequence_outcome_corpus_export
```

Rationale:

```text
M743 is too strong to leave as only a run directory, but it is still diagnostic.
The next step should preserve positive rows as an auditable corpus before any
objective or PPO work.
```

M745 should design a v3-aware corpus export that:

```text
1. filters sentinel rows from positives;
2. keeps only sequence_outcome_critical positives;
3. preserves source_kind, pair_id, pairing_rule, reset_action_l2_gap,
   reset_margin_gap, match_distance, source_role, fault families, severity, and
   future-only claim-boundary metadata;
4. includes matched normal rows;
5. records hard-negative action-only rows separately;
6. reports source, variant, horizon, seed, fault-family, and sentinel balance;
7. blocks objective training, PPO, and promotion.
```

Recommended minimum corpus targets:

```text
positive_rows >= 500
positive_sentinel_rows == 0
unique_positive_seeds >= 16
unique_positive_fault_family_pairs >= 16
matched_normal_rows == positive_rows
sentinel_false_positive_rows_exported_as_positive == 0
```

Objective design should remain a later audit decision.
