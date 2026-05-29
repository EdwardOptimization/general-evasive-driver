# M1424 Paper-Route Action-Divergent Outcome-Pressure Source Implementation

## Summary

M1424 implements the no-training constructor designed in M1423:

```text
src/autodrift/action_divergent_outcome_pressure.py
tests/test_action_divergent_outcome_pressure.py
```

Decision:

```text
action_divergent_outcome_pressure_constructor_implemented_admit_source_smoke
```

M1424 does not run a full source smoke, replay outcome interventions, train, run
PPO, promote, use private holdout, export a training corpus, or change actor
inputs.

## What Changed

The new constructor reads existing outcome-probe CSV rows and separates:

```text
action-critical:
  a history/control intervention changes the action sequence.

outcome-pressure candidate:
  a history action-divergent row can be paired with a bounded obstacle relocation
  proxy that places normal history near a terminal margin band.

history-positive proxy:
  a history variant, not reset or zero-current, remains the responsible variant
  under the proxy pressure accounting.
```

The constructor writes:

```text
summary.json
candidate_rows.csv
outcome_pressure_rows.csv
history_positive_rows.csv
variant_summary.csv
source_diversity_summary.csv
relocation_summary.csv
rejected_rows.csv
```

All generated pressure rows carry:

```text
proxy_only: true
requires_replay: true
relocated_obstacle_geometry_used: true
```

This prevents the output from being mistaken for closed-loop outcome evidence.

## Accounting Rules

History-positive accounting only accepts variants in:

```text
delayed_warmup_history_8
delayed_warmup_history_16
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
warmup_removed
warmup_shortened_8
```

Controls are diagnostic only:

```text
reset_hidden
zero_current_response
```

If reset or zero-current is action-divergent, it is counted in
`control_action_divergent_rows`, but it cannot enter `history_positive_rows`.

## Verification

Focused tests passed:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_action_divergent_outcome_pressure.py

5 passed
```

The tests cover:

```text
history-positive versus reset/zero-current accounting
relocation proxy rows marked proxy_only and requires_replay
source-balanced candidate selection
summary schema and contract flags
deterministic relocation-grid construction
```

Compile check passed for the new implementation and tests.

## Guardrails

M1424 is infrastructure only:

```text
source_smoke_started: false
outcome_probe_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

The constructor may use existing public outcome CSVs to form future source
proposals, but it does not add actor inputs or claim self-identification.

## Next

Next milestone:

```text
m1425-paper-route-action-divergent-outcome-pressure-source-smoke
```

M1425 should run the constructor once on the public M1421 outcome rows and
check whether enough source-diverse proxy pressure rows exist to justify a later
closed-loop replay probe. It must remain no-training and no-promotion.
