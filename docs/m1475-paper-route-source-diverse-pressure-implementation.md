# M1475 Paper-Route Source-Diverse Pressure Implementation

## Summary

M1475 implements the no-training source-diverse pressure candidate generator
designed in M1474.

Decision:

```text
source_diverse_pressure_generator_implemented_admit_proposal_smoke
```

M1475 does not run preflight, replay, outcome interventions, train, run PPO,
promote, use private holdout, export corpus, or change actor inputs.

## Implementation

Added:

```text
src/autodrift/source_diverse_pressure.py
tests/test_source_diverse_pressure.py
```

The generator reads:

```text
actual replay rows
history-positive rows
control-positive rows
candidate pool rows
```

and emits:

```text
source_diverse_pressure_anchor_rows.csv
source_diverse_pressure_source_audit.csv
source_diverse_pressure_proposal_rows.csv
source_diverse_pressure_candidate_rows.csv
summary.json
```

## Core Behavior

The implementation separates M1472 rows into:

```text
original_source:
  the source family that produced M1472 history positives.

neighbor_source:
  other source families sharing live relocation keys and eligible for pressure.

control_diagnostic:
  zero-current/control rows on the original family, kept separate from history
  evidence.
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
without starting replay in M1475.

## Selection Rules

Selection prioritizes neighbor-source pressure rows, then capped original-source
diagnostics, then capped control diagnostics.

Caps implemented:

```text
per_seed_cap
per_capability_pair_cap
per_reveal_bucket_cap
per_relocation_key_cap
per_variant_cap
original_source_cap
control_diagnostic_cap
duplicate source_diverse_pressure_key filtering
```

This prevents the next candidate pool from collapsing back to the original
source family.

## Focused Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_source_diverse_pressure.py tests/test_research_validate.py
```

Result:

```text
31 passed in 2.12s
```

Covered:

```text
history anchors exclude control rows
source audit separates original, neighbor, and control rows
pressure deltas tighten easy rows
proposal rows preserve source_step and replay offset fields
selection caps original-source and control diagnostics
duplicate pressure keys are removed
```

## Guardrails

M1475 guardrail status:

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
m1476-paper-route-source-diverse-pressure-proposal-smoke
```
