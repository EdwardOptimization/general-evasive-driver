# M1484 Paper-Route Neighbor Viability Calibration Implementation

## Summary

M1484 implements the no-training neighbor normal-viability calibration generator
designed in M1483.

Decision:

```text
neighbor_viability_calibration_generator_implemented_admit_proposal_smoke
```

M1484 does not run preflight, bounded replay, outcome interventions, training,
PPO, promotion, private holdout, corpus export, or actor-input changes.

## Implementation

Added:

```text
src/autodrift/neighbor_viability_calibration.py
tests/test_neighbor_viability_calibration.py
```

The generator reads:

```text
actual replay rows
history-positive rows
control-positive rows
```

and emits:

```text
neighbor_viability_audit_rows.csv
neighbor_viability_proposal_rows.csv
neighbor_viability_candidate_rows.csv
summary.json
```

## Core Behavior

The implementation separates rows into:

```text
original_source:
  the source family that produced M1481 history positives.

neighbor_source:
  source-diverse rows that should be calibrated into normal-viable,
  margin-gap-sensitive windows.

control_diagnostic:
  zero-current/reset rows on the original family, kept separate from history
  evidence.
```

Neighbor rows are classified as:

```text
too_hard:
  normal branch fails or normal margin is negative.

near_boundary:
  normal branch is viable and normal margin is in the target band with
  nonnegative intervention gap.

too_easy:
  normal branch is viable but margin is too large or intervention gap is weak.
```

Candidate rows preserve:

```text
candidate_step_column: source_step
source_step
candidate_step
body_longitudinal_offset
body_lateral_offset
half_width_inflation
```

Those fields keep the output compatible with later bounded relocation replay
without starting preflight or replay in M1484.

## Selection Rules

Selection prioritizes neighbor-source rows, then capped original-source
diagnostics, then capped control diagnostics.

Caps implemented:

```text
per_seed_cap
per_capability_pair_cap
per_reveal_bucket_cap
per_viability_class_cap
per_variant_cap
original_source_cap
control_diagnostic_cap
duplicate neighbor_viability_key filtering
```

This prevents the next candidate pool from collapsing back to the original
source family.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_neighbor_viability_calibration.py tests/test_research_validate.py
```

Result:

```text
32 passed in 2.17s
```

Covered:

```text
original-source families exclude controls
too_hard / near_boundary / too_easy classification
too_hard deltas ease geometry and too_easy deltas tighten geometry
audit separates original, neighbor, and control rows
proposal rows preserve source_step and replay offset fields
selection caps original-source and control diagnostics
duplicate neighbor_viability_key rows are removed
```

## Guardrails

M1484 guardrail status:

```text
source_preflight_started: false
replay_started: false
outcome_interventions_started: false
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
m1485-paper-route-neighbor-viability-calibration-proposal-smoke
```
