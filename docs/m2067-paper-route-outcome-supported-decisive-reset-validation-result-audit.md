# M2067 Paper-Route Outcome-Supported Decisive Reset Validation Result Audit

- status: completed
- decision: `outcome_supported_decisive_reset_audit_route_to_combined_materialization_repair_design`
- audited summary: `runs/m2066_paper_route_outcome_supported_decisive_reset_validation_preflight/summary.json`
- failure taxonomy: `scenario_sampling_failure`
- reset/rollout/measured execution in M2067: `false`
- policy actions executed in M2067: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result Audit

M2066 ran the focused reset-only validator over all `240` M2063 executable
specs and failed closed:

```text
result_class: outcome_supported_decisive_reset_validation_preflight_fail
reset_attempt_count: 240
reset_success_count: 0
reset_failure_count: 240
observation_finite_count: 0
observation_dimension_failure_count: 0
obstacle_initialized_count: 0
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

Quota and provenance preservation remained clean:

```text
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
registered_family_quota_pass: true
registered_split_quota_pass: true
registered_difficulty_axis_coverage_pass: true
```

Failure distribution:

```text
RuntimeError failed to sample an obstacle scenario matching the configured filters: 123
ValueError warmup_gate max_active_steps must be positive: 117
```

## Failure Localization

The warmup-gate error is a materialization schema issue inside the executable
env config, not an actor-input or metadata-contract violation.

Examples show zero-duration warmup gates serialized as invalid configs:

```text
warmup_gate.enabled: false or true
warmup_gate.max_active_steps: 0
```

`WarmupGateConfig` validates `max_active_steps` as positive regardless of
whether the gate is enabled. Therefore repaired specs must never serialize
`max_active_steps <= 0`. If `warmup_mode == none`, the repair should preserve a
disabled gate with positive default validated fields. If `warmup_mode != none`,
the repair should enforce a positive active duration floor instead of emitting a
zero-step active gate.

The obstacle-filter sampling error is a source/filter feasibility issue. It
appears across all active diagnostic and delayed/terminal families:

```text
T3_active_diagnostic_warmup: 60
T4_variable_diagnostic_delay: 36
T5_terminal_boundary_near_constraint: 27
```

Those failures arise before policy actions and before rollout; they say the
current generated smoke-proxy obstacle filters cannot produce admissible
AEB-infeasible scenarios under the configured distance, width, threshold, and
time-after-step constraints.

Family-level split:

```text
T1_reactive_active_safety:
  warmup_gate invalid: 48

T2_same_current_different_older_history:
  warmup_gate invalid: 60

T3_active_diagnostic_warmup:
  obstacle filter sampling failure: 60

T4_variable_diagnostic_delay:
  obstacle filter sampling failure: 36

T5_terminal_boundary_near_constraint:
  obstacle filter sampling failure: 27
  warmup_gate invalid: 9
```

## Classification

Registered process-v2 failure taxonomy:

```text
scenario_sampling_failure
```

Operational subtypes:

```text
zero_step_warmup_gate_schema_invalid: 117
obstacle_filter_unsampleable: 123
```

This is not a controller, driver, PPO, replay, recurrent-memory, or
self-identification failure.

## Supported Claims

Supported:

```text
M2066 failure is fully localized to executable task validity before rollout.
The focused validator preserves metadata, contract rows, and claim-boundary guards.
The M2063 generated smoke-proxy panel is not reset-valid yet.
```

Unsupported:

```text
reset-validity of the M2063 panel;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Route Decision

Selected:

```text
combined_materialization_repair_design
```

Reason:

```text
Both failure classes are large and structurally distinct. A warmup-only repair
would still leave 123 unsampleable obstacle filters. A source/filter-only repair
would still leave 117 invalid warmup-gate configs.
```

M2068 should design a no-rollout repair route with two explicit repair axes:

```text
1. disabled warmup-gate schema normalization:
   preserve warmup_mode semantics but ensure max_active_steps and other
   validated fields remain valid positive defaults.

2. obstacle source/filter feasibility repair:
   retarget or broaden generated smoke-proxy obstacle filters only enough to
   make reset sampling feasible, while preserving family/source provenance and
   keeping paper_validity_claim=false.
```

Rejected:

```text
direct measured execution:
  rejected because reset success is 0/240.

single warmup-gate repair:
  rejected because obstacle-filter failures are 123/240.

single source/filter repair:
  rejected because warmup-gate invalid configs are 117/240.

accepting generated rows as paper-valid:
  rejected because these remain smoke_proxy generated tasks.

driver capability interpretation:
  rejected because no policy action or rollout was executed.
```

## Next

Next milestone:

```text
m2068-paper-route-outcome-supported-decisive-reset-materialization-repair-design
```
