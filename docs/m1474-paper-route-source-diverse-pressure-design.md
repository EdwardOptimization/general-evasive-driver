# M1474 Paper-Route Source-Diverse Pressure Design

## Summary

M1474 designs the next no-training route after M1472 found a live local
positive-neighborhood surface that still remained source-singleton.

Decision:

```text
source_diverse_pressure_design_admit_implementation
```

M1474 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Problem

M1472 improved the M1461 result from:

```text
2 history-positive rows, 2 relocation keys
```

to:

```text
8 history-positive rows, 7 relocation keys
```

But all history positives still came from one source family:

```text
seed: 141901
capability_pair: brake_authority_drop->mass_cg_shift
bucket: vx6|yaw-2|steer-4|ox0|oy0
variant: warmup_removed
```

The same family also produced zero-current control positives:

```text
control_positive_rows: 12
control_positive_unique_source_seeds: 1
control_positive_unique_capability_pairs: 1
```

So M1472 is useful as a live local boundary diagnostic, but it is not a
source-diverse corpus and must not be used for training or promotion.

## Design Principle

The next step should stop expanding the original source and instead pressure
neighbor sources.

Use M1472 as:

```text
boundary map: which body-frame relocation keys are locally live
source audit: which neighbor sources stayed non-positive on those keys
control audit: which zero-current rows can mimic history-positive sensitivity
```

Do not use M1472 as:

```text
training corpus
promotion evidence
paper-level self-identification evidence
level3 anticipatory self-identification evidence
```

## Source-Diverse Pressure Generator

Implement a no-training generator:

```text
src/autodrift/source_diverse_pressure.py
```

Inputs:

```text
runs/m1472_positive_neighborhood_bounded_replay_smoke/actual_replay_rows.csv
runs/m1472_positive_neighborhood_bounded_replay_smoke/history_positive_rows.csv
runs/m1472_positive_neighborhood_bounded_replay_smoke/control_positive_rows.csv
runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv
```

Outputs:

```text
source_diverse_pressure_candidate_rows.csv
source_diverse_pressure_source_audit.csv
source_diverse_pressure_control_audit.csv
summary.json
```

The generator should:

```text
1. Identify history-positive relocation keys from M1472.
2. Mark the original positive source separately.
3. Collect neighbor-source rows that share live relocation keys but did not
   become history-positive.
4. Rank neighbor sources by replay pressure potential:
   - normal margin already near the local boundary;
   - positive or near-positive margin gap;
   - sequence action divergence above threshold;
   - source seed and capability pair not equal to the original source.
5. Build source-diverse pressure candidates by retargeting neighbor sources
   toward the live relocation keys and tighter boundary bands.
6. Preserve `source_step` and `candidate_step_column == source_step`.
7. Keep zero-current controls in a separate diagnostic output and never count
   them as history positives.
8. Cap original-source rows so they cannot dominate the selected candidates.
```

## Pressure Policy

M1472 showed that many neighbor rows share the live relocation keys but remain
non-positive. The design should therefore create pressure candidates in three
groups:

```text
anchor_diagnostic:
  a small capped sample from the original positive source, only for regression
  checking.

neighbor_pressure:
  rows from different seeds and capability pairs that share live relocation
  keys and have replay evidence near the local boundary.

control_diagnostic:
  zero-current rows, always reported separately and never used as
  history-positive evidence.
```

Recommended ranking score for neighbor pressure:

```text
score =
  + near_boundary_normal_margin
  + max(0, margin_gap)
  + sequence_action_l2_mean
  + source_diversity_bonus
  - original_source_penalty
  - control_variant_penalty
```

Use only public M1472/M1470 artifacts. Do not use private holdout.

## Candidate Caps

The selected pressure candidate set should enforce diversity:

```text
max_candidates: 192
per_seed_cap: 24
per_capability_pair_cap: 24
per_reveal_bucket_cap: 24
per_relocation_key_cap: 32
per_variant_cap: 64
original_source_cap: 12
control_diagnostic_cap: 32
```

The proposal smoke should report:

```text
selected_candidate_rows
unique_source_seeds
unique_capability_pairs
unique_reveal_buckets
unique_relocation_keys
original_source_rows
neighbor_source_rows
control_diagnostic_rows
candidate_step_column
duplicate_pressure_key_rows
```

## Future Gate

M1475 should implement the generator and focused tests only. It should not run
preflight or replay.

Implementation passes if:

```text
source-diverse pressure generator exists
focused tests cover original-source separation
focused tests cover control-positive separation
focused tests cover source_step preservation
focused tests cover source diversity caps
focused tests cover duplicate pressure-key filtering
no preflight, replay, training, PPO, promotion, private holdout, corpus export,
or actor-input change occurs
```

After M1475, admit a proposal smoke only. A future replay smoke is allowed only
after the proposal smoke proves that source-diverse candidate pressure actually
exists.

## Stop Conditions

Stop this branch and synthesize if:

```text
neighbor_source_rows cannot be built without replaying the original source;
selected candidates collapse back to one seed or capability pair;
zero-current controls cannot be separated from history-positive candidates;
the generator requires actor-input changes or hidden/oracle fields;
the next proposal smoke again produces only original-source candidates.
```

## Guardrails

M1474 guardrail status:

```text
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1475-paper-route-source-diverse-pressure-implementation
```
