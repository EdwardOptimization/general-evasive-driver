# M2328 Paper-Route Current-Sim R4 Mitigation Metric Instrumentation Result Audit

- status: completed
- result_class: `r4_mitigation_metric_instrumentation_result_accepted_route_to_r4_diagnostic_rerun_design`
- manifest: `experiments/manifests/m2328-paper-route-current-sim-r4-mitigation-metric-instrumentation-result-audit.json`
- parent implementation: `docs/m2327-paper-route-current-sim-r4-mitigation-metric-instrumentation-implementation.md`
- reset/rollout/policy action in M2328: `false`
- measured execution in M2328: `false`
- training/replay/PPO in M2328: `false`
- actor input changed: `false`
- reward/training objective changed: `false`
- collision termination behavior changed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2327 is accepted as a bounded logging/export implementation:

```text
focused tests: 9 passed
actor input changed: false
reward/training objective changed: false
collision termination behavior changed: false
measured execution run: false
ranking claim: false
```

M2327 fixes the immediate export problem:

```text
existing outcome_metric_instrumentation fields are preserved in scenario task-family CSV headers;
canonical R4 aliases and availability flags are produced;
unavailable true delta-v and post-collision fields are explicitly marked unavailable.
```

The old M2318/M2321/M2324 artifacts remain stale with respect to the new fields.
They should not be reinterpreted as containing mitigation metrics.

## Accepted Claim

Allowed claim:

```text
M2327 makes future scenario task-family measured/support artifacts capable of
preserving R4 mitigation metric aliases and availability flags.
```

Blocked claims:

```text
R4 mitigation performance measured;
post-collision recovery measured;
R4 solved;
support-policy/controller ranking;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Next Route

M2328 selects a non-ranking design milestone:

```text
m2329-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-design
```

The design should freeze a small R4-only support diagnostic rerun:

```text
12 R4 scenarios
3 diagnostic support policies
5 seed repeats
expected episodes: 180
```

Purpose:

```text
produce fresh R4 support-policy artifacts with exported mitigation metric fields;
audit field completeness and support semantics;
do not rank support policies;
do not claim mitigation performance until result audit.
```

## Follow-Up Manifest

```text
experiments/manifests/m2329-paper-route-current-sim-r4-metric-instrumented-support-diagnostic-rerun-design.json
```
