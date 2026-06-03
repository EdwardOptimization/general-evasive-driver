# M2520 Engineering Controller Behavior/Outcome Protocol Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- decision: `promote_to_bounded_measured_behavior_panel`
- manifest: `experiments/manifests/m2520-engineering-controller-behavior-outcome-protocol-branch-synthesis.json`
- synthesis artifact: `docs/m2520-engineering-controller-behavior-outcome-protocol-branch-synthesis.md`
- parent evidence window: `m2513` through `m2519`
- next milestone: `m2521-engineering-controller-bounded-measured-behavior-panel-preflight`
- external high-fidelity simulation installed/imported/executed in M2520: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2520: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2520: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation/driver-performance verdict claims: `false`

## Evidence Summary

The behavior/outcome protocol branch now has enough source-only machinery to
stop adding static protocol artifacts and start a bounded measured-behavior
panel in the next branch:

```text
M2513:
  designed evaluator-side behavior/outcome semantics
  preserved actor contract 72/3 and no-oracle P0 inputs
  split layers into source_only_diagnostic, current_sim_diagnostic_mining, and
  future_high_fidelity_validation

M2514-M2515:
  materialized and audited protocol artifacts
  row schema fields: 51
  metric registry rows: 40
  audit gates: 15
  layer registry rows: 3
  forbidden registry rows: 39
  accepted scope: no-rollout protocol materialization only

M2516-M2517:
  materialized and audited source-only row completeness
  behavior/outcome rows: 12
  metric gap rows: 40
  unsupported metrics kept explicit: 12
  actor contract: 72/3
  rows: source_only_diagnostic and diagnostic_only_no_ranking

M2518-M2519:
  materialized and audited source-only evaluator-side event instrumentation
  event rows: 12
  metric gap delta rows: 40
  filled M2516 unsupported metrics: 10
  remaining unsupported metrics: mitigation_delta_against_reference, seed
  ranking/winner/success-rate/verdict fields: absent
```

The branch moved from a missing outcome semantics blocker to an audited
source-only protocol and event-instrumentation substrate. It did not yet add
new behavior evidence.

## Supported Claims

Supported:

```text
The engineering-controller behavior/outcome protocol is coherent enough to
admit a bounded source-only measured-behavior panel.

Evaluator-side event metrics can now be computed from existing fixture geometry
and telemetry without changing actor input.

The P0 actor/action contract remains observation 72, action 3, recurrent
human_view_online_gru, horizon 1.

The branch preserves no-ranking, no-winner, no-success-rate-verdict, and
no-driver-performance claim boundaries.
```

## Falsified Or Unsupported Claims

Unsupported or explicitly rejected:

```text
driver performance
behavior improvement or behavior regression verdict
success-rate benchmark
controller-family ranking
winner selection
checkpoint promotion
deployment certification
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

M2520 did not run a simulator, execute policy actions, train, rank controllers,
compute success rates, or measure fresh behavior. The synthesis only decides
that the next branch should produce bounded measured behavior data.

## Failure Taxonomy Summary

Controlled:

```text
contract_violation:
  controlled by repeated 72/3 actor/action gates and no hidden/oracle actor
  input boundaries.

lineage_invalid:
  controlled by committed manifests, docs, summaries, row artifacts, reviews,
  queue/status rows, and scoreboard entries.

metric_artifact:
  controlled by row schema, metric registry, explicit unsupported gaps,
  event-instrumentation deltas, and no-verdict claim flags.
```

Unresolved:

```text
behavior_regression:
  unresolved. The branch defines how to measure behavior but has not yet run
  a measured behavior panel under the accepted protocol.

scenario_sampling_failure:
  unresolved. The accepted source-only fixtures are fixed diagnostic surfaces,
  not fresh scenario distributions.

validation_boundary:
  unresolved. The branch does not admit high-fidelity validation and does not
  install, import, or run an external backend.

objective_overfit:
  medium risk if the project keeps adding source-only diagnostic artifacts.
  The mitigation is to stop the protocol branch here and require new measured
  behavior data before further interpretation.
```

## Public Gate Overfit Risk

Risk entering M2520: `medium`.

Reason:

```text
M2513-M2519 are mostly protocol, audit, and source-only artifact work. That was
necessary to prevent outcome overclaims, but another static source-only artifact
would mostly optimize fixed public rows and workflow gates.
```

Risk reduction:

```text
Close the behavior/outcome protocol branch.

Promote to a bounded measured-behavior panel that executes the admitted actor
and pre-registered open-loop references under the same source-only fixtures,
records all attempted rows, and keeps ranking/verdict claims blocked.
```

## Next Branch Decision

Decision:

```text
promote_to_bounded_measured_behavior_panel
```

Rationale:

```text
The limiting gap is no longer missing row schema or missing event metrics. The
limiting gap is measured behavior data under the accepted protocol.

The next branch should produce a bounded source-only measured behavior panel
using the existing M1154 actor, the existing coast and straight-brake open-loop
references, and the accepted three source-only role fixtures.

The panel should record seed lineage explicitly and pre-register mitigation
reference semantics so the two remaining M2518 gaps can be tested rather than
hand-waved.
```

Required next route:

```text
m2521-engineering-controller-bounded-measured-behavior-panel-preflight
```

M2521 may execute bounded source-only policy actions and open-loop reference
actions as diagnostic behavior data. It must preserve the actor/action contract,
retain all attempted rows, avoid hidden/oracle actor inputs, and must not rank
controllers, select a winner, compute success-rate verdicts, promote a
checkpoint, claim driver performance, or claim high-fidelity validation.
