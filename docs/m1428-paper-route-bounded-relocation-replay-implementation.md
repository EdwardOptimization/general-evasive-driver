# M1428 Paper-Route Bounded Relocation Replay Implementation

## Summary

M1428 implements the bounded no-training relocation replay probe designed in
M1427:

```text
src/autodrift/bounded_relocation_replay_probe.py
tests/test_bounded_relocation_replay_probe.py
```

Decision:

```text
bounded_relocation_replay_implementation_admit_public_replay_smoke
```

M1428 does not run the public replay probe, train, run PPO, promote, use private
holdout, export a training corpus, or change actor inputs.

## What Changed

The new probe can:

```text
1. read M1425 outcome-pressure rows;
2. select source-balanced history-variant candidates;
3. reconstruct preferred and wrong warmup traces;
4. build requested history/control hiddens;
5. apply bounded obstacle relocation to the preferred snapshot;
6. replay normal, requested history variant, reset-hidden, and zero-current;
7. count history-positive only from actual replay outcomes.
```

The implementation reuses existing repo primitives:

```text
collect_fault_trace_window
build_warmup_variant_hiddens
replay_probe_variant
TracePoint
OutcomeSnapshot
relocate_outcome_snapshot
response_feature_dim_for_model
```

## Accounting Rules

History-positive requires actual replay:

```text
normal_success == true
normal_margin >= 0
sequence_action_l2_mean >= 0.025
and (
  success_drop == true
  or margin_gap >= 0.02
)
variant in warmup-history variants
```

Controls are reported separately:

```text
reset_hidden
zero_current_response
```

Controls cannot enter `history_positive_rows`.

## Verification

Focused tests passed:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_bounded_relocation_replay_probe.py

4 passed
```

The tests cover:

```text
source-balanced replay candidate selection
relocation bound clipping
history-positive versus control-positive accounting
summary schema and contract flags
```

Compile check passed for the new implementation and tests.

## Guardrails

M1428 remains implementation-only:

```text
public_replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

The tool is ready for a separately registered public replay smoke. No replay
result exists yet from M1428.

## Next

Next milestone:

```text
m1429-paper-route-bounded-relocation-replay-smoke
```

M1429 should run the probe once on M1425 pressure rows with the pre-registered
public smoke limits. It must remain no-training and no-promotion.
