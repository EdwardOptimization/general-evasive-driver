# M2058 Paper-Route Controlled Routing Smoke Task-Quality Repaired Measured Execution Synthesis

- status: completed
- decision: `controlled_routing_smoke_repaired_measured_synthesis_pivot_to_outcome_supported_task_distribution`
- synthesis decision: `pivot`
- synthesis window: `M2054-M2057`
- primary failure taxonomy: `scenario_sampling_failure`
- reset/rollout/measured execution in M2058: `false`
- policy actions executed in M2058: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2054 promoted the repaired routing-smoke panel to measured execution only after
the branch produced clean materialization and reset-validity evidence:

```text
repaired specs: 192
planned workload rows: 2304
reset success: 192 / 192
contract/metadata/guardrail failures: 0
```

M2056 executed the repaired panel completely:

```text
result_class: controlled_routing_smoke_measured_execution_pass
episode_count: 2304 / 2304
failure_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

M2057 audited the measured outcomes:

```text
success_obstacle_pass: 45 / 2304
collision_failure: 14 / 2304
off_track_noncollision_noncompletion: 2245 / 2304
```

The best-looking aggregate signal is still sparse:

```text
L3_online_gru: 26 / 192 success
L3_reset_control_corrected: 17 / 192 success
L0_current_masked: 1 / 192 success
L1_one_step: 1 / 192 success
all L2 finite-window and tiled profiles: 0 success
```

This is not a fair comparison table. It is evidence that the smoke panel remains
too dominated by road-departure failure to support controller-family ranking.

## Supported Claims

Supported:

```text
The repaired routing-smoke panel can be materialized, reset, and executed end-to-end.
The current focused measured runner and metadata harness are sufficient for complete execution artifacts.
The repaired panel gives weak diagnostic signal that L3 profiles find more successes than L0/L1/L2 on this smoke distribution.
```

## Falsified Claims

Falsified for this branch:

```text
The M2044-M2053 task-quality repair made the routing-smoke panel ranking-ready.
The repaired 192-spec panel has enough outcome support for finite-window-vs-GRU paper comparison.
Another local repair of the same panel is the highest-leverage next step.
```

Still unsupported:

```text
paper-level benchmark result;
finite-window-vs-GRU conclusion;
strong recurrent-belief advantage;
level3 self-identification;
paper-valid generated task semantics.
```

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  The dominant failure mode is still offtrack noncompletion after repair.

metric_artifact:
  The M2051 generated-proxy key mismatch was real but repaired by M2053.

none:
  Materialization, reset validation, and measured-execution plumbing now pass.
```

The active blocker is no longer infrastructure. It is scenario/task-distribution
quality.

## Public Gate Overfit Risk

Risk is high if the project keeps repairing this panel:

```text
The same offtrack-dominated blocker recurred after a full repair branch.
The repaired panel is public and has already shaped multiple milestones.
The available successes are sparse enough that local tuning could overfit a few rows.
The panel still contains smoke-proxy generated rows with paper_validity_claim=false.
```

The right move is to pivot to an outcome-supported task distribution rather
than make another repair wave on the same public panel.

## Next Branch Decision

Selected:

```text
pivot:
  paper_route_outcome_supported_decisive_task_distribution
```

The new branch should design a distribution-generation route with outcome
support as a first-class precondition before full controller-family comparison.
It should not start from the premise that GRU must win. It should produce task
families that can fairly test the paper route:

```text
T1: reactive emergency avoidance;
T2: delayed or ambiguous command-response evidence;
T3: diagnostic warmup then obstacle reveal;
T4: same-current / different-older-history;
T5: terminal-boundary near-constraint avoidance.
```

Required design principles:

```text
1. Calibrate difficulty before full 12-profile execution.
2. Keep actor input/output contract unchanged.
3. Keep generated rows smoke_proxy until separately validated.
4. Require source diversity and role-specific support.
5. Use measured smoke gates to reject panels with broad offtrack dominance.
6. Treat finite-window/current-response success as valid engineering evidence.
```

Rejected routes:

```text
another local repair of M2048:
  rejected because repeated offtrack dominance indicates local-search drift.

direct controller ranking from M2056:
  rejected because outcome support is too sparse.

direct self-ID claim:
  rejected because no history-necessity intervention is tested.

high-fidelity simulator migration:
  rejected for now because current-sim task-distribution quality is unresolved.
```

## Next

Next milestone:

```text
m2059-paper-route-outcome-supported-decisive-task-distribution-design
```
