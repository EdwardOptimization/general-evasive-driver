# M2054 Paper-Route Controlled Routing Smoke Task-Quality Repair Reset Validator Normalization Result Audit

- status: completed
- decision: `controlled_routing_smoke_task_quality_repair_synthesis_promote_to_measured_execution_command_design`
- synthesis decision: `promote_to_next_branch`
- audited summary: `runs/m2053_paper_route_controlled_routing_smoke_task_quality_repair_reset_validation_preflight/summary.json`
- synthesis window: `M2044-M2053`
- reset/rollout/measured execution in M2054: `false`
- policy actions executed in M2054: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

The task-quality repair branch started from M2043's no-rerun localization:

```text
comparison-ready candidates: 0
candidate-support candidates: 0
offtrack dominance slices: 138
raw M2039 outcomes: success 20 / collision 13 / offtrack 399
```

M2044-M2045 created a deterministic no-rollout repair wave:

```text
repair candidates: 192
repair-axis quotas: 64 / 48 / 40 / 24 / 16
split: public_debug 112 / public_gate 80
generated proxy paper claims: 0
guardrail: 0
```

M2047-M2048 materialized the repaired panel:

```text
repaired specs: 192 / 192
planned workload rows: 2304 / 2304
profiles: 12 / 12
unresolved parents: 0
materialization failures: 0
duplicate specs/workload: 0
contract violations: 0
forbidden/claim guards: 0
guardrail: 0
```

M2051 reset execution found a validator aggregate-key artifact, not a reset
failure:

```text
reset success: 192 / 192
contract violations: 0
metadata missing: 0
guardrail: 0
failing gate: generated_proxy_quota_pass=false
cause: paper_claim=False vs paper_claim=false key mismatch
```

M2053 repaired that validator metric artifact and reran reset validation:

```text
result_class: controlled_routing_smoke_reset_validation_preflight_pass
reset attempts: 192
reset successes: 192
reset failures: 0
finite observations: 192
observation-dimension failures: 0
obstacles initialized: 192
contract violations: 0
metadata missing: 0
forbidden key violations: 0
family/source-kind/proxy-template/generated-proxy quotas: true
guardrail: 0
```

## Supported Claims

Supported:

```text
The repaired routing-smoke panel is materialized as 192 specs and 2304 workload rows.
The repaired panel is reset-valid under the current simulator and human-view actor-contract checks.
The M2051 failure was a validator metric artifact, repaired in M2053.
The branch is ready for measured-execution command design.
```

## Falsified Or Unsupported Claims

Falsified:

```text
The M2051 fail indicated real reset invalidity.
```

Unsupported:

```text
measured rollout success;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
paper-valid generated task semantics;
level3 self-identification.
```

Reset validity is not rollout validity. It only admits the next measured
execution design step.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  M2043/M2044 branch root. Original panel was offtrack-dominated and not ranking-ready.

metric_artifact:
  M2051 generated-proxy aggregate-key case mismatch. Repaired by M2053.

none:
  M2045 templates, M2048 materialization, and M2053 repaired reset validation pass their registered guards.
```

## Public Gate Overfit Risk

Risk remains medium:

```text
The repaired 192-spec panel is still a smoke-proxy diagnostic panel.
Generated rows remain paper_validity_claim=false.
No measured rollout distribution has been observed after repair.
No controller-family ranking or private holdout evidence exists yet.
```

The branch did not tune controller profiles or actor inputs, and it did not use
private holdout evidence. The next measured execution must preserve the same
claim boundary: execution completeness first, interpretation only in a later
audit.

## Next Branch Decision

Selected:

```text
promote_to_next_branch:
  paper_route_controlled_routing_smoke_task_quality_repaired_measured_execution
```

M2055 should design the measured-execution command for the repaired panel:

```text
input specs: runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/executable_task_specs.json
input workload: runs/m2048_paper_route_controlled_routing_smoke_task_quality_repair_materialization_preflight/planned_workload.csv
target episodes: 2304
target specs: 192
target profiles: 12
```

The existing focused runner
`autodrift.paper_route_controlled_routing_smoke_measured_runner` is the first
candidate because it already owns the controlled-routing-smoke metadata schema,
but M2055 must still audit whether its pass gates and metadata preservation are
compatible with the repaired 192-spec workload before execution.

Rejected:

```text
another reset validator repair:
  rejected because M2053 reset validation now passes.

direct measured execution:
  rejected because the exact command and target gates must be frozen first.

controller-family ranking:
  rejected because no repaired measured execution exists.

paper-level claim:
  rejected because the repaired panel remains smoke-proxy until measured and audited.
```

Measured execution, ranking, paper claims, and level3 self-ID claims remain
blocked until the next branch produces and audits measured rollout artifacts.
