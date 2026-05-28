# M1380 Paper-Route Promoted-Base Source-Rich Sequence Expanded Result Audit

## Purpose

M1380 audits the expanded sequence probe M1379 and chooses a route before any
further local expansion, corpus export, objective update, PPO, promotion, private
holdout, L0/L1/L2/L3 comparison, or claim expansion.

M1380 does not train, run PPO, run new evaluation, promote, use private holdout,
change actor inputs, export a corpus, or make high-fidelity physical claims.

## M1379 Evidence

M1379 artifact:

```text
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json
```

M1379 result:

```text
result_class: sequence_temporal_history_positive
selected_source_rows: 768
intervention_rows: 13824
accepted_sequence_rows: 224
accepted_temporal_sequence_rows: 224
accepted_cross_fault_sequence_rows: 0
sequence_action_critical_rows: 2790
normal_failed_rows: 0
rejected_trace_rows: 0
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 10
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Expanded thresholds:

```text
accepted_temporal_sequence_rows >= 200
unique_temporal_accepted_fault_pairs >= 8
unique_temporal_accepted_seeds >= 12
```

Observed:

```text
accepted_temporal_sequence_rows: 224
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 10
```

M1379 passes the row and fault-pair thresholds, but still misses the
accepted-seed threshold.

## Branch Evidence Summary

Source-rich cross-fault wrong-history evidence:

```text
M1373 smoke:
  accepted_rows: 2
  reset_only_rows: 174

M1375 larger public wave:
  accepted_rows: 3
  reset_only_rows: 1281
```

Interpretation:

```text
current cross-fault hidden swap remains sparse;
seed scaling mostly increases reset-only rows, not accepted wrong-history rows;
cross-fault wrong-history self-identification is not supported.
```

Temporal sequence evidence:

```text
M1377 sequence probe:
  accepted_temporal_sequence_rows: 180
  unique_temporal_accepted_fault_pairs: 8
  unique_temporal_accepted_seeds: 9
  accepted_cross_fault_sequence_rows: 0

M1379 expanded sequence probe:
  accepted_temporal_sequence_rows: 224
  unique_temporal_accepted_fault_pairs: 9
  unique_temporal_accepted_seeds: 10
  accepted_cross_fault_sequence_rows: 0
```

Interpretation:

```text
temporal-history dependence is repeatable and source-rich by rows/fault pairs;
accepted-seed diversity remains below threshold;
cross-fault sequence self-ID remains unsupported.
```

## Route Decision

Do not run another local expansion immediately.

Reason:

```text
M1377 -> M1379 doubled selected source rows from 384 to 768.
Temporal rows increased from 180 to 224.
Fault-pair coverage increased from 8 to 9.
Accepted seed coverage increased only from 9 to 10, still below 12.
```

Another blind expansion may consume time without changing the decision quality.
The branch now needs synthesis:

```text
m1381-paper-route-promoted-base-source-rich-comparison-readiness-synthesis
```

M1381 should decide between:

```text
1. source-selection redesign for temporal seed diversity;
2. temporal sequence corpus design with explicit seed-thin caveat;
3. cross-fault intervention redesign;
4. moving to L0/L1/L2/L3 fair-comparison refresh with source-rich temporal
   diagnostics as a public evidence axis;
5. a branch stop if source-rich current-model proxies are no longer the highest
   leverage route.
```

## Supported Claims

M1380 supports:

```text
1. M1379 is a clean structural expanded sequence probe.
2. The promoted M1362 base has repeatable temporal-history dependence under
   source-rich capability-step rows.
3. Temporal evidence is positive by row and fault-pair coverage.
4. Accepted-seed diversity remains below the pre-registered threshold even after
   expansion.
5. Cross-fault wrong-history self-identification remains unsupported.
6. The next step should be synthesis, not another local expansion.
```

## Unsupported Claims

M1380 does not support:

```text
1. temporal corpus export without a separate design and source-diversity policy;
2. cross-fault self-identification;
3. training, objective update, PPO, or promotion;
4. private-holdout evidence;
5. L0/L1/L2/L3 comparison conclusions;
6. high-fidelity per-wheel or real-vehicle transfer claims;
7. level3 anticipatory recurrent-belief self-identification.
```

## Decision

Decision:

```text
promoted_base_source_rich_sequence_expanded_audit_route_to_branch_synthesis
```

Next:

```text
m1381-paper-route-promoted-base-source-rich-comparison-readiness-synthesis
```
