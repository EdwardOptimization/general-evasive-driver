# M2141 Paper-Route Outcome-Supported Decisive Comparison-Support Denominator-Source Inventory Materialization

- status: completed
- decision: `denominator_source_inventory_pass_route_to_audit`
- result class: `comparison_support_denominator_source_inventory_pass`
- implementation: `src/autodrift/paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory.py`
- tests: `tests/test_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory.py`
- run artifact: `runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/summary.json`
- reset/rollout/measured execution in M2141: `false`
- policy actions executed in M2141: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M2141 adds a no-rerun denominator inventory materializer. It joins:

```text
M2138 panel units and support matrix
M2128 outcome_by_profile_source_kind rows
M2125 measured profile universe and claim boundary
```

This produces denominator availability rows for:

```text
6 panel source kinds * 5 measured profiles = 30 rows
```

It does not run the environment or policies.

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory.py
```

Result:

```text
3 passed
```

Materialization:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory \
  --protocol-summary runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json \
  --panel-units runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/panel_units_normalized.csv \
  --support-matrix runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_matrix.csv \
  --protocol-claim-boundary runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/claim_boundary.csv \
  --profile-source-kind runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/outcome_by_profile_source_kind.csv \
  --measured-summary runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/summary.json \
  --profile-aggregate runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/profile_aggregate.csv \
  --measured-claim-boundary runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/claim_boundary.csv \
  --output-dir runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory \
  --expected-panel-units 6 \
  --expected-profile-count 5 \
  --expected-denominator-count 30 \
  --next-blocker m2142-paper-route-outcome-supported-decisive-comparison-support-denominator-source-inventory-audit
```

Result:

```text
result_class: comparison_support_denominator_source_inventory_pass
panel_unit_count: 6
measured_profile_count: 5
denominator_inventory_row_count: 30
available_denominator_row_count: 30
guardrail_violation_count: 0
```

## Result Summary

From `summary.json`:

```text
protocol_result_class: comparison_support_comparison_protocol_materialization_pass
source_result_class: comparison_support_measured_execution_pass
panel_unit_count: 6
measured_profile_count: 5
expected_denominator_row_count: 30
denominator_inventory_row_count: 30
available_denominator_row_count: 30
missing_denominator_row_count: 0
duplicate_denominator_row_count: 0
nonfinite_denominator_row_count: 0
claim_boundary_violation_count: 0
guardrail_violation_count: 0
winner_or_rank_computed: false
finite_window_vs_gru_verdict_computed: false
```

Measured profile universe:

```text
L0_current_masked
L1_one_step
L2_window_50
L3_online_gru
L3_reset_control_corrected
```

Profile denominator summary:

```text
L0_current_masked: 6/6 available, 60 episodes, 3 successes, 15 collisions, 42 offtrack outcomes
L1_one_step: 6/6 available, 60 episodes, 5 successes, 18 collisions, 37 offtrack outcomes
L2_window_50: 6/6 available, 60 episodes, 0 successes, 0 collisions, 60 offtrack outcomes
L3_online_gru: 6/6 available, 60 episodes, 22 successes, 8 collisions, 30 offtrack outcomes
L3_reset_control_corrected: 6/6 available, 60 episodes, 26 successes, 10 collisions, 24 offtrack outcomes
```

These are denominator inventory counts. They enable a later audited comparison
design, but M2141 itself does not rank or compare controller families.

## Claim Boundary

Allowed by M2141:

```text
complete denominator-source inventory over the M2138 panel and M2125 measured
profile universe;
availability of row-level denominator-backed metrics for later audit.
```

Blocked by M2141:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Decision

M2141 passes and routes to denominator inventory result audit.

The audit should decide whether the denominator inventory is sufficient to
design a denominator-backed controlled comparison protocol, or whether the
generated-proxy boundary still requires scenario redesign before any comparison
execution.

## Next

Next milestone:

```text
m2142-paper-route-outcome-supported-decisive-comparison-support-denominator-source-inventory-audit
```
