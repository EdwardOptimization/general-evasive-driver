# M1303 Paper-Route Source-History Trainable-Scope Repeat Result Audit

## Summary

M1303 audits the M1302 `fusion_head` split-repeat probe.

Decision:

```text
source_history_trainable_scope_repeat_audit_mixed_route_to_failed_offset_audit
```

M1302 is useful evidence, but it is not robust enough for proof-retention,
PPO, checkpoint promotion, or paper-level claims. The repeat passed `3/5`
deterministic pair-disjoint split offsets, but the mean eval row/group
fractions stayed below the pre-registered repeat-strong threshold.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1303.

## Evidence

M1302 repeat result:

```text
result_class: source_history_trainable_scope_repeat_mixed
scope: fusion_head
offset_count: 5
offset_pass_count: 3
required_pass_count: 3
mean_eval_both_directional_fraction: 0.2335317460
mean_eval_group_all_rows_both_positive_fraction: 0.2335317460
mean_full_both_positive_count: 38.0
mean_full_group_all_rows_both_positive_count: 19.0
forbidden_parameter_mutation_detected: false
```

Per-offset outcome:

```text
offset 0: pass, eval row/group 0.2500000000, full 46/152 rows and 23/76 groups
offset 1: pass, eval row/group 0.2777777778, full 48/152 rows and 24/76 groups
offset 2: fail, eval row/group 0.1875000000, full 32/152 rows and 16/76 groups
offset 3: pass, eval row/group 0.2857142857, full 40/152 rows and 20/76 groups
offset 4: fail, eval row/group 0.1666666667, full 24/152 rows and 12/76 groups
```

Comparison to M1295:

```text
M1295 best full both-positive rows: 30/152
M1302 mean full both-positive rows: 38/152

M1295 best full all-rows-both-positive groups: 15/76
M1302 mean full all-rows-both-positive groups: 19/76
```

## Supported Claims

Supported:

```text
The widened `fusion_head` scope has a real source-history directional signal.
It is not a single-offset artifact because offsets 0, 1, and 3 pass.
```

Supported:

```text
The mutation guard is clean across repeat offsets. No forbidden parameter group
mutation was detected.
```

Supported:

```text
The trainable-scope direction remains materially better than the earlier
actor_mean-only branch on full-corpus directional counts.
```

## Falsified Or Blocked Claims

Blocked:

```text
The M1299 single-split result is repeat-robust.
```

The repeat mean eval row/group fractions are `0.2335317460`, below the `0.25`
threshold.

Blocked:

```text
The current result is sufficient to design proof-retention or PPO continuation.
```

The failed offsets make that premature. The next step has to explain whether
the failures are caused by harder eval pairs, source/fault-family imbalance,
probe-template concentration, or an underweighted objective.

Not supported:

```text
Closed-loop driver performance.
```

Not supported:

```text
Strong online self-identification.
```

## Failure Interpretation

This is not a contract failure or training instability. It is a split-sensitive
diagnostic result.

Failure taxonomy:

```text
scenario_sampling_failure risk: possible
seed_fragility analog: possible, but not established
objective_overfit: possible, but not established
contract_violation: false
training_instability: false
metric_artifact: not observed
```

The right next question is not "can we tune harder?" It is:

```text
Which source-history pairs, fault families, probe templates, or margin buckets
make offsets 2 and 4 fail?
```

## Public-Gate Overfit Risk

Risk:

```text
moderate to high
```

The public split repeat found a real signal, but the failed offsets show the
branch could overfit to favorable pair partitions. The project should not use
these split metrics as promotion evidence. They are diagnostic evidence for the
paper-route source-history objective.

## Next Routing

Next:

```text
m1304-paper-route-source-history-repeat-failed-offset-audit
```

M1304 should be a no-training failed-offset/corpus audit. It should inspect:

```text
passing versus failing offsets;
failed eval pair IDs and physical pair IDs;
source/fault family distribution;
probe_template concentration;
margin and directional-metric distributions;
group-level failure rows;
whether failed offsets lack source families that passing offsets cover.
```

M1304 should not train, run PPO, change actor inputs, relax thresholds, use a
private holdout, or promote a checkpoint.

## Guardrails

M1303 preserves:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
self_identification_claimed: false
```

## Decision

The `fusion_head` branch remains scientifically useful, but it is not yet
robust. The next correct move is a failed-offset audit before any objective
tuning, proof-retention design, PPO continuation, or promotion attempt.
