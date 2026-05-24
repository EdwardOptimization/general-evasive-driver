# M735 Sequence-Level Command-Response Intervention Audit

## Purpose

M735 audits the M734 positive diagnostic before converting it into any corpus or
training objective.

The question is:

```text
Is M734's sequence_outcome_positive result clean enough to justify a
sentinel-filtered compact corpus export design?
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

M734 passes the registered sequence outcome gate:

```text
source_candidate_rows: 512
source_unique_seeds: 236
source_unique_preferred_fault_families: 8
source_unique_fault_family_pairs: 30
source_max_seed_dominance: 0.017578
source_max_preferred_family_dominance: 0.126953

sequence_action_critical_rows: 5262
sequence_outcome_critical_rows: 73
unique_sequence_outcome_seeds: 28
unique_sequence_outcome_fault_family_pairs: 10
max_sequence_outcome_seed_dominance: 0.082192

normal_failed_rejected: 0
sentinel_false_positive_rate: 0.002451
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Compared with M731:

```text
M731 accepted outcome rows: 1
M734 sequence outcome rows: 73
```

So the positive is not a small numerical fluctuation. Changing the intervention
from one-step to multi-step is the meaningful evidence increment.

## Variant And Horizon Effects

Outcome rows by variant:

```text
zero_command_obs: 67
reset_hidden_each_step: 6
```

Outcome rows by horizon:

```text
H=2: 0
H=4: 9
H=6: 26
H=8: 38
```

This supports the interpretation that:

```text
short one-step perturbations were being repaired by feedback;
persistent loss of command-response history creates terminal outcome changes.
```

## Sentinel Audit

M734 has:

```text
sentinel_rows: 1224
sentinel_false_positive_rows: 3
sentinel_false_positive_rate: 0.002451
```

The three sentinel rows are all `zero_command_obs` margin-gap rows:

```text
seed 72073, H=6:
  combined_fault->front_lateral_authority_drop
  normal_margin: 0.757402
  variant_margin: 0.731494
  margin_gap: 0.025908
  terminal_reason: obstacle_completed

seed 72073, H=8:
  combined_fault->front_lateral_authority_drop
  normal_margin: 0.757402
  variant_margin: 0.724741
  margin_gap: 0.032660
  terminal_reason: obstacle_completed

seed 72239, H=8:
  front_lateral_authority_drop->combined_fault
  normal_margin: 0.401317
  variant_margin: 0.376286
  margin_gap: 0.025032
  terminal_reason: obstacle_completed
```

They are not collision rows. The false-positive rate is far below the gate
threshold, but corpus export must filter all sentinel rows.

After sentinel filtering:

```text
non-sentinel outcome rows: 70
non-sentinel outcome variants:
  zero_command_obs: 64
  reset_hidden_each_step: 6

non-sentinel outcome horizons:
  H=4: 9
  H=6: 25
  H=8: 36
```

## Supported Claims

M735 supports:

```text
1. M734 is a valid diagnostic positive result.

2. Sequence-level command-response history interventions reveal outcome
   sensitivity that one-step boundary mining did not.

3. The strongest diagnostic is sustained loss of previous-command observation,
   consistent with the project's closed-loop command-response-history claim.

4. The positive rows are diverse enough to justify a compact corpus export
   design after sentinel filtering.
```

## Falsified Claims

M735 falsifies:

```text
1. The project must immediately pivot to higher-fidelity dynamics before
   obtaining outcome-sensitive self-ID evidence.

2. M731's one-step boundary-negative result means the current actor has no
   closed-loop command-response dependence.

3. M734 can be used directly as a PPO or promotion result.
```

M735 does not prove:

```text
1. The policy improves if trained on the M734 rows.

2. PPO will preserve the sequence-outcome proof.

3. The result generalizes to private holdout or higher-fidelity vehicle models.
```

## Failure Taxonomy Summary

Primary:

```text
none
```

Reason:

```text
M734 passed the registered source-balance, sequence-outcome, sentinel,
normal-retention, and actor-checksum gates.
```

Residual risk:

```text
metric_artifact risk remains if action-only or sentinel rows are exported as
outcome-positive corpus rows. M736 must filter them.
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate.

M734 uses public M731 source rows and a public horizon set:

```text
H in {2,4,6,8}
```

However, the result is diagnostic and no checkpoint is promoted. The correct
next step is not PPO. It is:

```text
1. export a compact sentinel-filtered corpus;
2. audit corpus diversity;
3. then design a sequence-preference objective or repeat/holdout validation.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: sequence_outcome_corpus_export
```

Rationale:

```text
M734 has enough clean non-sentinel outcome rows to preserve as a durable corpus,
but not enough evidence to train or promote directly.
```

M736 should design a no-training corpus export that:

```text
1. filters sentinel rows;
2. keeps only sequence_outcome_critical rows plus matched normal and rejected
   sequence variants;
3. preserves source, variant, horizon, margin, and action-distance metadata;
4. balances by seed, fault-family pair, variant, and horizon;
5. writes a compact corpus and audit summary;
6. blocks PPO and promotion.
```

Recommended corpus policy:

```text
positive rows:
  non-sentinel sequence_outcome_critical == true

paired contrast rows:
  same source_index and horizon normal row
  same source_index and horizon selected intervention row
  optional same source_index/horizon action-only non-outcome rows as hard
  negatives

minimum export target:
  >= 50 positive rows if available
  >= 20 source seeds
  >= 6 fault-family pairs
```

If M736 finds the exported corpus remains diverse after filtering, M737 can
implement the export. Objective design should remain a later audit decision.
