# M2069 Paper-Route Outcome-Supported Decisive Task Distribution Synthesis

- status: completed
- decision: `outcome_supported_decisive_task_distribution_synthesis_continue_to_bounded_repair`
- synthesis decision: `continue`
- synthesis window: `M2059-M2068`
- primary failure taxonomy: `scenario_sampling_failure`
- reset/rollout/measured execution in M2069: `false`
- policy actions executed in M2069: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2059 started this branch because the previous routing-smoke panel remained
offtrack-dominated after repair. The branch objective was to build an
outcome-supported decisive task distribution before any full controller-family
comparison.

M2060 generated a no-rollout candidate panel:

```text
candidates: 240
families: T1 48, T2 60, T3 60, T4 36, T5 36
split: public_debug 144, public_gate 96, private_holdout 0
source kinds per family: 6
max single source-kind share: 0.1667
actor forbidden-key violations: 0
guardrail violations: 0
```

M2063 materialized those candidates into smoke-proxy executable specs:

```text
executable specs: 240
planned sentinel workload rows: 1200
sentinel profiles: 5
family/split/difficulty quotas: pass
contract violations: 0
forbidden-key violations: 0
guardrail violations: 0
```

M2066 then supplied the first real reset-validity evidence and failed closed:

```text
reset attempts/success/failure: 240 / 0 / 240
metadata/contract/forbidden-key/guardrail failures: 0 / 0 / 0 / 0
zero-step warmup-gate schema invalid: 117
obstacle-filter unsampleable: 123
```

M2067 localized the reset failure as executable task validity before rollout,
not controller evidence. M2068 designed a bounded combined repair: normalize
zero-step warmup gates and make obstacle filters scenario-feasible through a
deterministic no-reset scan.

## Supported Claims

Supported:

```text
The branch created a quota-complete and provenance-preserving generated task panel.
The current M2063 executable specs are not reset-valid.
The failure is localized before rollout and before policy action.
The next useful step is bounded task-validity repair, not controller ranking.
```

## Falsified Claims

Falsified for this branch state:

```text
The M2063 smoke-proxy panel is ready for measured execution.
No-reset materialization success is enough to admit reset validation as a formality.
Single-axis repair is enough for M2066 failures.
```

Still unsupported:

```text
reset-valid outcome-supported decisive panel;
measured execution readiness;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
paper-valid generated task semantics;
level3 self-identification.
```

## Failure Taxonomy Summary

Registered failure taxonomy:

```text
scenario_sampling_failure
```

Operational subtypes:

```text
zero_step_warmup_gate_schema_invalid:
  117 specs serialized invalid warmup gate values.

obstacle_filter_unsampleable:
  123 specs cannot sample an obstacle scenario under current filters.
```

No evidence points to actor-input contract leakage, metadata loss, PPO washout,
training instability, or driver behavior regression.

## Public Gate Overfit Risk

Risk is medium if the branch continues narrowly:

```text
The panel is generated smoke_proxy and not paper-valid.
The branch has already spent several milestones on materialization and reset gates.
The current failure happens before rollout, so controller-family conclusions are still far away.
```

Risk is bounded if the next step remains:

```text
no-reset;
fully audited;
provenance-preserving;
claim-boundary preserving;
followed by reset validation before measured execution.
```

The branch should not add another design-only hop. It should either implement the
combined repair or stop/pivot if the repair cannot preserve task semantics.

## Next Branch Decision

Selected:

```text
continue:
  paper_route_outcome_supported_decisive_task_distribution
```

The continuation is narrow and conditional:

```text
M2070 may implement only the no-reset combined repair preflight defined by M2068.
M2070 must not run reset, rollout, policy actions, measured execution, ranking,
or paper/self-ID interpretation.
M2071 must audit the repair result before any reset-validation rerun.
```

Rejected routes:

```text
direct measured execution:
  rejected because reset success is 0/240.

direct reset rerun without repair:
  rejected because the same M2066 failure classes would recur.

another design-only milestone:
  rejected because synthesis cadence has fired and M2068 already fixed the repair design.

paper-level or self-ID interpretation:
  rejected because the branch has not reached reset-valid task evidence.
```

## Next

Next milestone:

```text
m2070-paper-route-outcome-supported-decisive-reset-materialization-repair-preflight-implementation
```
