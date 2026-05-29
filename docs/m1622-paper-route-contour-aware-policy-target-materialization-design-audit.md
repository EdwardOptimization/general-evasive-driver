# M1622 Paper-Route Contour-Aware Policy Target Materialization Design Audit

## Summary

M1622 audits the M1621 policy-side target materialization design.

Decision:

```text
contour_aware_policy_target_materialization_audit_admit_traceability_preflight
```

The design is directionally correct, but full materialization should not be
implemented immediately. Existing artifacts show enough row keys to design the
route, but the availability of every required variant and tensor-capture source
must be checked by a bounded traceability preflight first.

## Audit Result

M1621 correctly identifies the key issue:

```text
M1619's evaluator residual is metadata/row-metric only;
direct actor objective update is unsafe;
policy-side targets require observation/hidden/action tensors;
existing source CSVs expose first actions, margins, and hidden norms, not full
observation/hidden tensors.
```

The M1615 positive rows are traceable by stable metadata:

```text
source_run
contour_pair_id
selected_pair_id
original_pair_id
target_anchor_id
donor_anchor_id
target_anchor_window
donor_anchor_window
source_edge
```

Known source run mapping is plausible:

```text
m1592_clean_repair ->
  runs/m1592_clean_history_control_source_generation_repair_smoke

m1595_balanced_repair ->
  runs/m1595_selector_balanced_clean_source_repair_smoke

M1609 replay package ->
  runs/m1609_diagnostic_complete_bounded_replay
```

However, the audit should not assume full target materialization is safe until
a script confirms row-level matches and variant availability.

## Supported Claims

M1622 supports:

```text
M1621's target schemas are explicit;
positive and diagnostic roles remain separated;
the next useful step is traceability preflight, not training;
full tensor materialization remains blocked until traceability is measured.
```

## Unsupported Claims

M1622 does not support:

```text
all source rows are already traceable;
all normal/wrong/donor variants are available;
observation/hidden tensors are already materialized;
policy target corpus implementation is safe without preflight;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
level3 self-identification.
```

## Risk Assessment

Main implementation risks:

```text
source_run labels are aliases, not direct directory names;
diagnostic rows may not all have the same variant coverage as positives;
source CSVs store hidden norms, not hidden vectors;
tensor capture likely requires deterministic rerun plumbing;
public proof rows remain narrow and overfit-prone.
```

Mitigation:

```text
run traceability preflight before materialization;
write missing-row artifacts instead of partial training targets;
keep diagnostics non-positive;
keep tensor capture separate from objective construction;
audit preflight before any materialization implementation.
```

## Next Route

Admit one bounded infrastructure preflight:

```text
m1623-paper-route-contour-aware-policy-target-traceability-preflight
```

M1623 should not materialize tensors. It should only verify source resolution
and variant availability.

Expected outputs:

```text
runs/m1623_contour_aware_policy_target_traceability_preflight/summary.json
runs/m1623_contour_aware_policy_target_traceability_preflight/positive_traceability_rows.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/diagnostic_traceability_rows.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/source_run_resolution_summary.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/variant_availability_summary.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/missing_traceability_rows.csv
```

Preflight gates should include:

```text
positive_candidate_count == 39
diagnostic_guardrail_count == 232
source_run_resolution_failure_count == 0
positive_replay_pair_match_count == 39
positive_normal_variant_match_count == 39
positive_wrong_history_variant_match_count == 39
positive_donor_plus_hidden_variant_match_count == 39
diagnostic_rows_used_as_positive == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
level3_self_id_claim_made == false
```

If those gates fail, route to source-artifact discovery or broader candidate
refresh rather than full materialization.

## Next

```text
m1623-paper-route-contour-aware-policy-target-traceability-preflight
```
