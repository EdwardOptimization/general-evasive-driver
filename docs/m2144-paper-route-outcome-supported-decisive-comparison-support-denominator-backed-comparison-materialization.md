# M2144 Paper-Route Outcome-Supported Decisive Comparison-Support Denominator-Backed Comparison Materialization

- status: completed
- decision: `denominator_backed_diagnostic_comparison_pass_route_to_audit`
- result class: `comparison_support_denominator_backed_diagnostic_comparison_pass`
- implementation: `src/autodrift/paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison.py`
- tests: `tests/test_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison.py`
- run artifact: `runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/summary.json`
- reset/rollout/measured execution in M2144: `false`
- policy actions executed in M2144: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M2144 adds a no-rerun denominator-backed diagnostic comparison materializer. It
reads M2141 denominator rows and writes descriptive profile/source-kind rates
plus pre-registered diagnostic deltas.

Implementation:

```text
src/autodrift/paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison.py
```

The materializer writes:

```text
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/summary.json
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/comparison_protocol.json
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/profile_outcome_summary.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/source_kind_profile_matrix.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/diagnostic_contrast_rows.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/metric_contract.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/claim_boundary.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/run_state.json
```

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison.py
```

Result:

```text
2 passed
```

Materialization:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison \
  --inventory-summary runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/summary.json \
  --denominator-rows runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/denominator_inventory_rows.csv \
  --inventory-claim-boundary runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/claim_boundary.csv \
  --output-dir runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison \
  --next-blocker m2145-paper-route-outcome-supported-decisive-comparison-support-denominator-backed-comparison-result-audit
```

Result:

```text
result_class: comparison_support_denominator_backed_diagnostic_comparison_pass
profile_count: 5
source_kind_count: 6
denominator_row_count: 30
diagnostic_contrast_row_count: 6
guardrail_violation_count: 0
```

## Descriptive Profile Diagnostics

The generated-proxy diagnostic profile totals are:

```text
L0_current_masked: success 0.0500, collision 0.2500, offtrack 0.7000
L1_one_step: success 0.0833, collision 0.3000, offtrack 0.6167
L2_window_50: success 0.0000, collision 0.0000, offtrack 1.0000
L3_online_gru: success 0.3667, collision 0.1333, offtrack 0.5000
L3_reset_control_corrected: success 0.4333, collision 0.1667, offtrack 0.4000
```

These are descriptive rates over the M2138/M2141 generated-proxy panel only.
They are not a ranking or paper-level benchmark result.

## Diagnostic Contrasts

Pre-registered diagnostic deltas were materialized with:

```text
verdict_allowed: false
ranking_allowed: false
paper_claim_allowed: false
self_id_claim_allowed: false
```

Selected descriptive deltas:

```text
L3_online_gru - L1_one_step: success +0.2833, collision -0.1667, offtrack -0.1167
L3_online_gru - L2_window_50: success +0.3667, collision +0.1333, offtrack -0.5000
L3_reset_control_corrected - L3_online_gru: success +0.0667, collision +0.0333, offtrack -0.1000
```

These numbers are routing diagnostics. They do not prove recurrent-belief
advantage or self-identification. In particular, `L3_reset_control_corrected`
being descriptively strong on this generated-proxy panel blocks any naive
GRU-memory claim.

## Claim Boundary

Allowed by M2144:

```text
denominator-backed descriptive diagnostic rates;
pre-registered diagnostic deltas for audit routing.
```

Blocked by M2144:

```text
controller-family ranking;
winner selection;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

## Decision

M2144 passes and routes to result audit.

The audit should decide whether the generated-proxy diagnostic comparison is
useful enough to route to branch synthesis or scenario redesign. It should not
promote the descriptive rates into ranking or paper claims.

## Next

Next milestone:

```text
m2145-paper-route-outcome-supported-decisive-comparison-support-denominator-backed-comparison-result-audit
```
