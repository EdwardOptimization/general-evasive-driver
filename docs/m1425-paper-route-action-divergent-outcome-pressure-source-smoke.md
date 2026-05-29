# M1425 Paper-Route Action-Divergent Outcome-Pressure Source Smoke

## Summary

M1425 ran the M1424 no-training constructor on the public M1421 outcome rows:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.action_divergent_outcome_pressure \
  --outcome-rows runs/m1421_m1419_source_collision_stratified_outcome_probe/outcome_rows.csv \
  --run-dir runs/m1425_action_divergent_outcome_pressure_source_smoke
```

Decision:

```text
action_divergent_outcome_pressure_proxy_no_history_positive_route_to_audit
```

M1425 does not run closed-loop replay, outcome interventions, train, run PPO,
promote, use private holdout, export a training corpus, or change actor inputs.

## Result

```text
result_class: action_divergent_outcome_pressure_proxy_no_history_positive
input_rows: 2016
candidate_pool_rows: 625
candidate_rows: 256
outcome_pressure_rows: 846
history_positive_rows: 0
control_action_divergent_rows: 490
relocation_grid_size: 100
relocation_rejected_rows: 24754
proxy_only: true
requires_replay: true
```

Candidate diversity was good:

```text
candidate unique_source_seeds: 12
candidate unique_capability_pairs: 16
candidate unique_reveal_buckets: 52
candidate max_single_seed_share: 0.2266
candidate max_single_capability_pair_share: 0.0938
```

Pressure-row diversity was also nontrivial:

```text
outcome_pressure unique_source_seeds: 7
outcome_pressure unique_capability_pairs: 16
outcome_pressure unique_reveal_buckets: 31
outcome_pressure max_single_seed_share: 0.2695
outcome_pressure max_single_capability_pair_share: 0.1489
```

But the pre-registered source smoke fails because:

```text
history_positive_rows: 0
history_positive_unique_source_seeds: 0
history_positive_unique_capability_pairs: 0
history_positive_unique_reveal_buckets: 0
```

## Diagnostic

The failure is not absence of action divergence. The constructor found many
history-variant action-divergent rows:

```text
warmup_removed rows: 456
warmup_shortened_8 rows: 306
delayed_warmup_history_16 rows: 72
delayed_warmup_history_8 rows: 12
```

The failure is that the existing outcome margins do not separate enough.
Across the selected candidates:

```text
candidate_rows margin_gap max: 0.016403
candidate_rows margin_gap p95: 0.003603
candidate_rows margin_gap >= 0.02: 0
```

Across proxy pressure rows:

```text
outcome_pressure_rows margin_gap max: 0.002712
outcome_pressure_rows margin_gap p95: 0.000535
outcome_pressure_rows margin_gap >= 0.02: 0
```

So a shared-margin proxy can move normal-history rows into a near-boundary
normal band, but it cannot by itself create a history-positive result when
normal and variant margins move together.

## Interpretation

M1425 is a useful negative result:

```text
action divergence is source-diverse;
proxy obstacle pressure is source-diverse;
history-positive terminal-margin separation is still absent.
```

This means the next step should not be training and should not lower the
threshold after seeing the result. The right next step is an audit deciding
whether to:

```text
1. implement a bounded closed-loop relocation replay probe on the M1425 pressure rows;
2. redesign the constructor to use a directional action-to-margin pressure model;
3. abandon this branch if the gap is only action-level and not terminal-relevant.
```

## Guardrails

M1425 remains a public diagnostic only:

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

The constructor artifacts are proxy-only and require replay before any outcome
or self-identification claim.

## Next

Next milestone:

```text
m1426-paper-route-action-divergent-pressure-result-audit
```

M1426 should audit whether the zero history-positive proxy result is a source
failure or a limitation of the shared-margin proxy, and should decide the next
route before any replay, training, or corpus export.
