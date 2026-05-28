# M1296 Paper-Route Source-History Pair-Group Objective Result Audit

## Summary

M1296 audits the M1295 pair-group objective probe.

Decision:

```text
source_history_pair_group_objective_result_audit_route_to_branch_synthesis
```

M1295 is a valid diagnostic run, but the result is mixed and not strong enough
to justify PPO, checkpoint promotion, or another narrow actor_mean-only probe
before branch synthesis.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1296.

## Evidence

The active branch is:

```text
paper_route_source_history_objective_only_update
```

The branch began after M1286 promoted source-history objective-only update as
the next evidence path. The key evidence so far is:

```text
M1288: exact combined loss improved from 18.6105005714 to 7.1793530621
M1290: all 152/152 rows remained mutually exclusive after M1288
M1292: best actor_mean directional feasibility reached 28/152 both-positive rows
M1292: best all-rows-both-positive groups reached 14/76
M1295: best pair-group objective reached 30/152 both-positive rows
M1295: best all-rows-both-positive groups reached 15/76
```

M1295 best candidate:

```text
best_init_name: base_init
best_candidate_class: pair_group_directional_mixed
best_both_directional_fraction: 0.1973684211
best_both_positive_count: 30
best_mutually_exclusive_fraction: 0.6710526316
best_group_all_rows_both_positive_count: 15
best_group_all_rows_both_positive_fraction: 0.1973684211
best_group_min_margin_mean: -0.2857604090
best_group_min_margin_p10: -1.8031842709
```

M1294 strong gate:

```text
group_all_rows_both_positive_fraction >= 0.25
both_directional_fraction >= 0.25
group_all_rows_both_positive_count > 14
non_actor_mean_mutation_detected == false
```

M1295 only satisfies the count improvement and mutation guard:

```text
group_all_rows_both_positive_fraction: 0.1973684211
both_directional_fraction: 0.1973684211
group_all_rows_both_positive_count: 15
any_non_actor_mean_mutation_detected: false
```

## Supported Claims

Supported:

```text
The pair-group objective is implemented and reports finite row-level and
group-level directional metrics.
```

Supported:

```text
Actor_mean-only optimization can move the source-history directional surface.
M1295 improves both-positive rows from 28/152 to 30/152 and all-rows-positive
groups from 14/76 to 15/76.
```

Supported:

```text
The diagnostic update respects the narrow mutation guard:
non_actor_mean_l2_from_base=0.0 and non_actor_mean_mutation_detected=false.
```

Supported:

```text
The M1277/M1280 source-history artifacts remain usable for exact objective and
directional diagnostics without adding labels or hidden source metadata to actor
inputs.
```

## Falsified Claims

Falsified:

```text
A row-only actor_mean update is enough to repair source-history directionality.
M1290 and M1292 show persistent mutually exclusive rows and weak both-positive
fractions.
```

Falsified:

```text
Adding a pair-group floor/balance objective solves the directional repair.
M1295 remains below the strong 0.25 row and group thresholds.
```

Falsified:

```text
The objective-only branch is ready for PPO continuation. PPO remains blocked
because the policy-side source-history gate is still mixed and non-promotable.
```

Not yet proven:

```text
Allowing a wider trainable scope, refreshing the source-history corpus, or
switching to sequence/trajectory preference objectives would solve the
directional conflict.
```

## Failure Taxonomy

M1296 is a process audit, not a failed infrastructure run. The M1295 run itself
completed cleanly.

Scientific diagnosis:

```text
objective_underpowered_for_directional_repair
```

Nearest current taxonomy labels:

```text
none
```

Reason:

```text
The run did not violate process gates, mutate forbidden parameters, or regress
a promoted checkpoint. The negative part is an evidence result: actor_mean-only
pair-group optimization is not enough.
```

## Public-Gate Overfit Risk

Risk:

```text
moderate_to_high
```

Reason:

```text
The branch has repeatedly optimized the same fixed 152-row source-history
surface. Even though the result is still mixed, continuing narrow objective
edits would increasingly optimize a public diagnostic corpus rather than answer
the branch-level research question.
```

Mitigation:

```text
Stop the narrow branch after M1296 and run M1297 branch synthesis before any
more source-history objective-only implementation.
```

## Branch Decision

M1296 does not choose the next technical branch directly. It routes to the
required synthesis milestone:

```text
m1297-paper-route-source-history-objective-only-update-synthesis
```

M1297 must decide between at least these options:

```text
1. trainable-scope escalation under strict proof guards;
2. source-history corpus refresh with stronger matched action-divergent rows;
3. sequence/trajectory preference objective design;
4. stopping this source-history path if the evidence is too weak.
```

The current narrow branch should not continue with another actor_mean-only
objective before that synthesis.

## Guardrails

M1296 preserves:

```text
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
self_identification_claimed: false
```

## Next Step

Pre-register and execute:

```text
m1297-paper-route-source-history-objective-only-update-synthesis
```

PPO and promotion remain blocked.
