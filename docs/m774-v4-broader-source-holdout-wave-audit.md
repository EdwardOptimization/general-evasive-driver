# M774 V4 Broader Source-Holdout Wave Audit

## Purpose

M774 audits the M773 broader source-holdout wave before residual replay,
training, PPO, or promotion.

The decision question is:

```text
Is M773 broad enough to justify a limited no-PPO residual replay diagnostic, or
should we first do more source-balancing / fault-pair mining?
```

This audit is process-only:

```text
no residual replay
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Evidence Summary

M773 broader source wave:

```text
seed range: 77024..78047
config: configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

stage 1 result_class: cross_fault_reset_only
stage 2 result_class: v4_reset_sequence_outcome_positive
stage 3 result_class: v4_sequence_outcome_corpus_hard_negative_sparse
```

Stage 1:

```text
scenario_count: 29696
snapshot_count: 201913
matched_pair_count: 24576
reset_only_rows: 1389
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 1389
```

Stage 2:

```text
source_candidate_rows: 1024
source_unique_seeds: 63
source_unique_fault_family_pairs: 22
source_max_seed_dominance: 0.114258
source_max_preferred_family_dominance: 0.203125

sequence_outcome_critical_rows: 2652
unique_sequence_outcome_seeds: 49
unique_sequence_outcome_fault_family_pairs: 17
max_sequence_outcome_seed_dominance: 0.171569
sentinel_false_positive_rows: 0
normal_history_retention_pass: true
```

Stage 3:

```text
positive_rows: 2652
normal_rows: 2652
positive_intervention_rows: 2652
hard_negative_rows: 2134
positives_without_hard_negative: 872

sentinel_positive_candidates: 0
positive_sentinel_rows: 0
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0
rejected_rows: 0

unique_positive_seeds: 49
unique_positive_fault_family_pairs: 17
max_positive_seed_dominance: 0.171569
max_positive_fault_family_pair_dominance: 0.208145
claim_boundary_level: current_model_or_proxy

training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

## Comparison With M767

M773 is materially broader than M767:

```text
matched_pair_count:
  M767: 12288
  M773: 24576

reset_only_rows:
  M767: 390
  M773: 1389

source_candidate_rows:
  M767: 441
  M773: 1024

positive_rows:
  M767: 995
  M773: 2652

unique_positive_seeds:
  M767: 25
  M773: 49

unique_positive_fault_family_pairs:
  M767: 13
  M773: 17

max_positive_seed_dominance:
  M767: 0.247236
  M773: 0.171569

max_positive_fault_family_pair_dominance:
  M767: 0.265327
  M773: 0.208145
```

This directly supports the user's concern that prior validation may simply not
have mined enough extreme scenarios. Expanding coverage changed the evidence
surface substantially.

## M772 Broad Gate Audit

M772 broader targets:

```text
positive_rows >= 1500:
  2652 -> pass

unique_positive_seeds >= 40:
  49 -> pass

unique_positive_fault_family_pairs >= 18:
  17 -> fail by 1

max_positive_seed_dominance <= 0.15:
  0.171569 -> fail

max_positive_fault_family_pair_dominance <= 0.22:
  0.208145 -> pass
```

Artifact gates:

```text
sentinel positives: 0 -> pass
missing normal matches: 0 -> pass
missing v4 metadata: 0 -> pass
missing fidelity metadata: 0 -> pass
duplicate positive keys: 0 -> pass
claim boundary current_model_or_proxy -> pass
training / optimizer / PPO / promotion flags false -> pass
```

Interpretation:

```text
M773 is not strong enough for a broad generalization or promotion claim because
two strict M772 broad gates miss. It is strong enough for a limited no-PPO
residual replay diagnostic because ordinary corpus validity is clean and the
strict misses are small relative to the coverage improvement.
```

## Hard-Negative Audit

The corpus remains hard-negative sparse:

```text
hard_negative_rows: 2134
positive_rows: 2652
positives_without_hard_negative: 872
hard_negative_complete: false
result_class: v4_sequence_outcome_corpus_hard_negative_sparse
```

This blocks any claim that the contrast corpus is complete. It does not block
a no-PPO residual closed-loop replay diagnostic, because the replay evaluator
can operate on positives and contrast rows while reporting hard-negative
sparsity as a caveat.

## Source Concentration Audit

Dominant concentration remains visible:

```text
max_positive_seed_dominance: 0.171569
dominant seed: 77069

max_positive_fault_family_pair_dominance: 0.208145
dominant pair: mass_cg_shift->front_lateral_authority_drop
```

The concentration is lower than M767 but still too high for broad evidence.
M775 must preserve this caveat and stratify any residual replay result by seed,
fault-family pair, variant, and horizon.

## Supported Claims

M774 supports:

```text
1. M773 materially supports the coverage-limited hypothesis.

2. The current v4 proxy-fault mining surface is much larger than M767 showed:
   2652 clean positives across 49 seeds and 17 fault-family pairs.

3. The broader corpus is artifact-clean: no sentinel positives, no missing
   normal matches, no missing metadata, and no mutation/training/PPO flags.

4. A limited no-PPO residual replay diagnostic is justified, with caveats.
```

## Falsified Claims

M774 falsifies:

```text
1. M767's sparse corpus was already the full reachable v4 positive surface.

2. Broader source mining only increases raw rows without increasing positive
   sequence-outcome evidence.

3. The current blocker is purely training instability; scenario coverage is a
   first-class blocker.
```

M774 does not prove:

```text
1. Broad generalization.

2. Checkpoint promotion readiness.

3. PPO safety.

4. Residual replay success on M773.

5. True single-wheel or four-wheel physical fidelity.
```

## Failure Taxonomy Summary

Residual risk:

```text
scenario_sampling_failure
```

Reason:

```text
M773 improves coverage substantially, but strict broad-coverage gates still
miss on positive fault-family pairs and seed dominance, and hard negatives are
incomplete.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not proof_washout
not behavior_regression
not training_instability
not promotion_gate_failure
```

## Decision

Decision:

```text
promote_to_limited_broader_residual_replay_design
```

M775 should design a limited no-PPO residual replay on the M773 corpus:

```text
primary alpha: 0.2
diagnostic alphas: 0.5 and 1.0
inputs:
  runs/m761_v4_sequence_objective_probe/residual_head.pt
  runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv
  runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
  configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
```

M775 must report:

```text
normal success / collision / margin retention
intervention action-gap and margin-gap changes
seed and fault-family-pair concentration
variant and horizon stratification
hard-negative sparsity caveat
claim boundary current_model_or_proxy
no actor mutation, training, PPO, or promotion
```

If M775 replay fails or remains too concentrated, the next branch should
target source-balanced or fault-pair-targeted mining before any PPO.
