# M1447 Paper-Route Source-Step Preflight Support Implementation

## Summary

M1447 implements the source-step candidate support designed in M1446.

Decision:

```text
source_step_preflight_support_implemented_admit_source_step_preflight_smoke
```

M1447 does not run source preflight, bounded replay, outcome interventions,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.

## Implementation

Updated:

```text
src/autodrift/bounded_relocation_replay_probe.py
tests/test_bounded_relocation_replay_probe.py
```

New support:

```text
--candidate-step-column reveal_step
--candidate-step-column source_step
```

Default:

```text
reveal_step
```

M1445 follow-up should use:

```text
source_step
```

The implementation routes the candidate step column through both:

```text
preflight-only trace reconstruction
bounded replay preferred/wrong trace reconstruction
```

Artifacts now preserve:

```text
reveal_step
candidate_step
candidate_step_column
```

## Tests

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_bounded_relocation_replay_probe.py
```

Result:

```text
14 passed in 0.97s
```

Covered behavior:

```text
default reveal_step candidate anchor
explicit source_step candidate anchor
missing candidate step column error
preflight trace reconstruction uses source_step when requested
preflight trace reconstruction defaults to reveal_step
CLI parser defaults to reveal_step
```

## Guardrails

M1447 guardrail status:

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
m1448-paper-route-source-step-preflight-smoke
```

M1448 should run preflight-only on:

```text
runs/m1445_forward_geometry_source_miner_smoke/selected_candidate_rows.csv
```

with:

```text
--candidate-step-column source_step
```

It must not run bounded replay, outcome interventions, training, PPO,
promotion, private holdout, corpus export, or actor-input changes.
