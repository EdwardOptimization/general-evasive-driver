# M2094 Paper-Route Outcome-Supported Decisive Public-Gate Core Panel Extraction Implementation

- status: completed
- decision: `public_gate_core_panel_extraction_pass_route_to_result_audit`
- run artifact: `runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/summary.json`
- focused tests: `1 passed`
- reset/rollout/measured execution in M2094: `false`
- policy actions executed in M2094: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2094 adds a no-reset public-gate core panel selector:

```text
src/autodrift/paper_route_outcome_supported_decisive_public_gate_core_panel_extraction.py
tests/test_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction.py
```

It loads the M2088 reset-valid core specs and the M2091 reset rows, then
includes only rows satisfying:

```text
source_split == public_gate
M2091 reset_success == true
```

It excludes all public-debug rows. It does not change obstacle filters, does
not resample tasks, and does not start environment reset.

## Run Result

```text
result_class: outcome_supported_decisive_public_gate_core_panel_extraction_pass
input_executable_spec_count: 238
input_reset_row_count: 238
reset_success_row_count: 236
reset_failure_row_count: 2
public_gate_core_executable_spec_count: 96
excluded_spec_count: 142
public_gate_total_count: 96
public_gate_included_count: 96
public_gate_excluded_count: 0
public_debug_included_count: 0
public_debug_excluded_count: 142
planned_sentinel_workload_count: 480
env_config_changed_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
profile_missing_count: 0
guardrail_violation_count: 0
```

Coverage in the selected panel:

```text
family counts:
  T3_active_diagnostic_warmup: 24
  T4_variable_diagnostic_delay: 36
  T5_terminal_boundary_near_constraint: 36

dynamics counts:
  actuator_delay: 24
  low_mu: 24
  mixed_mu: 24
  nominal_mu: 24

difficulty axes:
  axis_count_min: 8
  axis_count_max: 8
```

## Interpretation

M2094 successfully materializes the public-gate-only core panel defined by
M2093. This is a panel-definition step, not a fresh reset validation and not a
controller-family comparison.

The useful outcome is:

```text
The project now has a concrete 96-row public-gate core panel with a 480-cell
planned sentinel workload.
```

The remaining limitation is:

```text
The panel intentionally drops T1/T2 and all public-debug rows, so it is a
bounded smoke/research panel rather than full task-distribution coverage.
```

## Supported Claims

Supported:

```text
A 96-row public-gate core panel was materialized from M2091 reset-success rows.
All public-gate rows from the 238-row reduced panel are included.
All public-debug rows are excluded.
No env_config mutation or claim-guard violation occurred.
```

Unsupported:

```text
fresh reset validity beyond M2091 evidence;
measured execution readiness before audit;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2095-paper-route-outcome-supported-decisive-public-gate-core-panel-extraction-result-audit
```
