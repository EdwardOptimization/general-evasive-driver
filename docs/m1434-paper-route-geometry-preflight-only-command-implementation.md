# M1434 Paper-Route Geometry Preflight-Only Command Implementation

## Summary

M1434 implements a no-replay preflight-only path for the geometry-aware selector.

Decision:

```text
preflight_only_command_implemented_admit_public_smoke
```

M1434 does not run source preflight on the public corpus, run bounded replay,
train, run PPO, promote, use private holdout, export a training corpus, or
change actor inputs.

## Implementation

Updated:

```text
src/autodrift/bounded_relocation_replay_probe.py
tests/test_bounded_relocation_replay_probe.py
```

New API:

```text
write_geometry_preflight_outputs
run_geometry_preflight_only_probe
```

New CLI mode:

```text
--preflight-only
```

The preflight-only mode reconstructs candidate source geometry, applies the
M1432 geometry-aware selector, writes preflight artifacts, and exits before any
closed-loop replay.

## Outputs

The preflight-only path writes:

```text
geometry_preflight_rows.csv
selected_candidate_rows.csv
geometry_rejected_rows.csv
source_diversity_summary.csv
summary.json
```

The summary reports:

```text
run_type: geometry_aware_preflight_only_probe
source_preflight_started: true
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

Preflight rows remain source-validation artifacts only. They are not replay
evidence, history-positive rows, training data, or promotion evidence.

## Tests

Focused tests cover:

```text
preflight-only summary fields
artifact writing
replay_started false guardrail
CLI parser exposing --preflight-only
existing geometry filters and diversity caps
```

Focused result:

```text
tests/test_bounded_relocation_replay_probe.py: 10 passed
```

CLI smoke:

```text
PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe --help
```

confirmed `--preflight-only` is exposed.

## Guardrails

M1434 guardrail status:

```text
source_preflight_run_started: false
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
m1435-paper-route-geometry-aware-preflight-smoke
```

M1435 should run the preflight-only command on the public M1425 source rows. It
must not run bounded replay or training. Passing M1435 only proves source
geometry and diversity viability for a later replay design; it does not prove
history necessity.
