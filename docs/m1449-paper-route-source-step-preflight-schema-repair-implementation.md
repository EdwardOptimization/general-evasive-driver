# M1449 Paper-Route Source-Step Preflight Schema Repair Implementation

## Summary

M1449 repairs the schema gap exposed by M1448.

Decision:

```text
source_step_preflight_schema_repair_implemented_admit_preflight_rerun
```

M1449 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Implementation

Updated:

```text
src/autodrift/bounded_relocation_replay_probe.py
tests/test_bounded_relocation_replay_probe.py
```

Change:

```text
prepare_candidate_frame no longer requires margin_gap.
if margin_gap is missing, it is created as 0.0.
```

Rationale:

```text
margin_gap is an outcome-pressure ranking feature.
M1445 source-step geometry rows are valid without it.
0.0 is a neutral ranking default and preserves explicit margin_gap rows.
```

## Tests

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_bounded_relocation_replay_probe.py
```

Result:

```text
15 passed in 0.90s
```

New coverage:

```text
M1445-style rows without margin_gap pass prepare_candidate_frame
missing margin_gap is filled with 0.0
```

## Guardrails

M1449 guardrail status:

```text
source_preflight_started: false
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
m1450-paper-route-source-step-preflight-rerun
```

M1450 should rerun the M1448 preflight command against M1445 candidates with
`--candidate-step-column source_step`. It must not run bounded replay, outcome
interventions, training, PPO, promotion, private holdout, corpus export, or
actor-input changes.
