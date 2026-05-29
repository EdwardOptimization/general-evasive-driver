# M1596 Paper-Route Selector-Balanced Repair Result Audit

## Summary

M1596 audits M1595 against M1592.

Decision:

```text
selector_balanced_repair_audit_route_to_branch_synthesis_before_further_repair
```

M1595 is a negative result. It shows that broad source-edge round-robin can
satisfy selection diversity while destroying clean-row yield. Since M1592 was a
near-pass and M1595 was a clean-count failure, another local cap tweak would be
public-row over-optimization. The next step should be branch synthesis before
any further repair design or implementation.

## M1592 Baseline

M1592 targeted clean source edges:

```text
selected_source_edge_count: 7
clean_directed_pair_count: 34
clean_source_edge_count: 5
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.35294117647058826
null_result_classification: source_concentrated_clean_surface
```

M1592 was a near-pass: high clean yield, but narrowly over the source-share cap.

## M1595 Result

M1595 used source-edge round-robin:

```text
selected_source_edge_count: 24
clean_directed_pair_count: 10
clean_source_edge_count: 4
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.4
null_result_classification: clean_count_shortfall
```

The selection became much broader but less useful. Most added source edges were
pairable but history-null or control-only.

## Interpretation

M1595 falsifies:

```text
more selected source-edge diversity alone preserves clean history-control evidence;
a lower per-edge cap is sufficient to fix M1592;
round-robin over all pairable edges is the right active-set rule.
```

M1592 and M1595 together support:

```text
the clean-source repair signal is real but highly active-set sensitive;
the useful clean contour is concentrated around a small set of source edges;
current-frame/action-history controls remain strong diagnostics;
more local tuning on the same public rows has high overfit risk.
```

## Failure Taxonomy

```text
scenario_sampling_failure
objective_overfit
```

`scenario_sampling_failure` applies because the balanced sample missed the
clean active set. `objective_overfit` applies as a risk because further cap
tuning would chase fixed public rows.

## Supported Claims

M1596 supports:

```text
M1592 remains the best clean-source diagnostic result in this branch;
M1595 is a valid negative result;
source-edge balance must be active-set aware, not broad pairability round-robin;
the branch needs synthesis before any further repair.
```

## Unsupported Claims

M1596 does not support:

```text
M1595 pass;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification;
level3 anticipatory self-identification;
another immediate cap tweak.
```

## Route Decision

Route to branch synthesis:

```text
m1597-paper-route-clean-source-repair-branch-synthesis
```

M1597 should synthesize M1591-M1596 and decide whether to:

```text
continue with a new active-set contour branch;
pivot to task/source redesign;
stop clean-source repair and preserve M1592 as diagnostic evidence.
```

Do not run another implementation before M1597.

## Guardrails

```text
history_interventions_executed: false in M1596
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1597-paper-route-clean-source-repair-branch-synthesis
```
