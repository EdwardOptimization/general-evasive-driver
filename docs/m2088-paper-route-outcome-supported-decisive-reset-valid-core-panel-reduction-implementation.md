# M2088 Paper-Route Outcome-Supported Decisive Reset-Valid Core Panel Reduction Implementation

- status: completed
- decision: `reset_valid_core_panel_reduction_pass_route_to_result_audit`
- run artifact: `runs/m2088_paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction/summary.json`
- focused tests: `1 passed`
- reset/rollout/measured execution in M2088: `false`
- policy actions executed in M2088: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2088 adds a no-reset reduced-panel selector:

```text
src/autodrift/paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction.py
tests/test_paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction.py
```

It loads the M2082 density-aware repaired specs and the M2085 reset rows, then
selects only rows with `reset_success == true`. It does not change obstacle
filters and does not start environment reset.

## Run Result

```text
result_class: outcome_supported_decisive_reset_valid_core_panel_reduction_pass
input_executable_spec_count: 240
input_reset_row_count: 240
reset_success_row_count: 238
reset_failure_row_count: 2
reduced_executable_spec_count: 238
excluded_spec_count: 2
public_gate_total_count: 96
public_gate_preserved_count: 96
public_gate_excluded_count: 0
public_debug_excluded_count: 2
planned_sentinel_workload_count: 1190
env_config_changed_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
profile_missing_count: 0
guardrail_violation_count: 0
```

Coverage after reduction:

```text
family counts:
  T1_reactive_active_safety: 47
  T2_same_current_different_older_history: 59
  T3_active_diagnostic_warmup: 60
  T4_variable_diagnostic_delay: 36
  T5_terminal_boundary_near_constraint: 36

split counts:
  public_debug: 142
  public_gate: 96

dynamics counts:
  actuator_delay: 60
  low_mu: 58
  mixed_mu: 60
  nominal_mu: 60

axis loss:
  late|generous|moderate|low_mu|low: 20 -> 18
```

## Interpretation

M2088 successfully materializes the reset-valid core panel defined by M2087.
The materialization is a panel-definition step, not a new reset validation.

The useful outcome is:

```text
The project now has a concrete 238-row reduced panel with all public-gate rows preserved.
```

The remaining limitation is:

```text
The panel is reset-valid under M2085 evidence, not yet under a fresh reduced-panel reset run.
```

## Supported Claims

Supported:

```text
A 238-row reset-valid core panel was materialized from M2085 reset-success rows.
All 96 public-gate rows are preserved.
The two excluded rows are public-debug reset failures.
No env_config mutation or claim-guard violation occurred.
```

Unsupported:

```text
fresh reset validity of the reduced panel;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2089-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-result-audit
```
