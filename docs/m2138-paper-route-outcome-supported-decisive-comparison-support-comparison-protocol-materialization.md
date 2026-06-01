# M2138 Paper-Route Outcome-Supported Decisive Comparison-Support Comparison Protocol Materialization

- status: completed
- decision: `comparison_support_protocol_materialization_pass_route_to_audit`
- result class: `comparison_support_comparison_protocol_materialization_pass`
- implementation: `src/autodrift/paper_route_outcome_supported_decisive_comparison_support_comparison_protocol.py`
- tests: `tests/test_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol.py`
- run artifact: `runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json`
- reset/rollout/measured execution in M2138: `false`
- policy actions executed in M2138: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M2138 adds a no-rerun protocol materializer that reads the M2134 controlled
panel and writes a machine-readable support matrix. It does not execute the
environment or policies.

Implementation:

```text
src/autodrift/paper_route_outcome_supported_decisive_comparison_support_comparison_protocol.py
```

The materializer writes:

```text
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/comparison_protocol.json
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/panel_units_normalized.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_matrix.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_summary.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/metric_contract.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/claim_boundary.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/run_state.json
```

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol.py
```

Result:

```text
3 passed
```

Materialization:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_comparison_protocol \
  --summary runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/summary.json \
  --controlled-panel-units runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/controlled_panel_units.csv \
  --excluded-qualified-candidates runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/excluded_qualified_candidates.csv \
  --claim-boundary runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/claim_boundary.csv \
  --output-dir runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol \
  --min-panel-units 6 \
  --min-profile-labels 3 \
  --next-blocker m2139-paper-route-outcome-supported-decisive-comparison-support-comparison-protocol-materialization-audit
```

Result:

```text
result_class: comparison_support_comparison_protocol_materialization_pass
panel_unit_count: 6
profile_label_count: 4
support_matrix_row_count: 24
guardrail_violation_count: 0
```

## Result Summary

From `summary.json`:

```text
source_result_class: comparison_support_controlled_panel_construction_pass
panel_unit_count: 6
profile_label_count: 4
support_matrix_row_count: 24
expected_support_matrix_row_count: 24
supported_intent_count: 3
supported_source_kind_count: 6
panel_duplicate_source_kind_count: 0
direct_broad_aggregate_panel_unit_count: 0
generated_proxy_boundary_panel_unit_count: 6
claim_boundary_violation_count: 0
guardrail_violation_count: 0
per_profile_rate_computed: false
winner_or_rank_computed: false
```

Profile labels in the matrix:

```text
L0_current_masked
L1_one_step
L3_online_gru
L3_reset_control_corrected
```

Support coverage summary:

```text
L0_current_masked: 3/6 panel units, 2 intents, 3 source kinds
L1_one_step: 5/6 panel units, 3 intents, 5 source kinds
L3_online_gru: 6/6 panel units, 3 intents, 6 source kinds
L3_reset_control_corrected: 6/6 panel units, 3 intents, 6 source kinds
```

These are support-coverage counts only. They are not a profile ranking because
M2134 does not provide per-profile denominators or a controlled comparison
execution.

## Claim Boundary

Allowed by M2138:

```text
comparison protocol materialization;
support-matrix coverage over M2134 controlled panel units;
metric contract and claim boundary are machine-readable.
```

Blocked by M2138:

```text
controller-family ranking;
per-profile success/collision/offtrack rates;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Decision

M2138 passes and routes to materialization result audit.

The audit should check whether the materialized support matrix remains a clean
support artifact and whether the next route should be a controlled comparison
execution design, scenario redesign, or synthesis. It should not interpret the
coverage counts as ranking.

## Next

Next milestone:

```text
m2139-paper-route-outcome-supported-decisive-comparison-support-comparison-protocol-materialization-audit
```
