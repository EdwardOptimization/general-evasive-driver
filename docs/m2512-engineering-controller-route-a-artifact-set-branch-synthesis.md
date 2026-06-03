# M2512 Engineering Controller Route A Artifact-Set Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- decision: `promote_to_engineering_controller_behavior_outcome_protocol`
- manifest: `experiments/manifests/m2512-engineering-controller-route-a-artifact-set-branch-synthesis.json`
- synthesis artifact: `docs/m2512-engineering-controller-route-a-artifact-set-branch-synthesis.md`
- parent evidence window: `m2493` through `m2511`
- next milestone: `m2513-engineering-controller-behavior-outcome-protocol-design`
- external high-fidelity simulation installed/imported/executed in M2512: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2512: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2512: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation/driver-performance verdict claims: `false`

## Evidence Summary

Route A now has a coherent engineering-controller artifact set, assembled from
source-only diagnostics and process audits rather than from a performance
benchmark:

```text
M2493-M2503:
  built and synthesized the source-only engineering-controller role metric and
  baseline-comparison diagnostics
  checkpoint contract: observation 72 / action 3 / human_view_online_gru / horizon 1
  M2493 first panel: 300 telemetry rows / 3 role rows, but identical role metrics
  M2496-M2499 fixed the source-only fixture-differentiation blocker at reset
  time and reran differentiated role diagnostics
  M2501 baseline comparison: 3 subjects, 3 roles, 900 telemetry rows, 9
  role-subject panel rows
  M2503 synthesis closed the metric-panel branch and rejected performance,
  ranking, validation, paper, finite-window-vs-GRU, and self-ID interpretations

M2504-M2507:
  designed, materialized, audited, and synthesized the public source-only
  diagnostic benchmark pack
  pack directory: public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505
  required files: present
  artifact manifest rows: 14
  source artifacts: present
  actor contract: 72/3
  claim flags: false for performance, success-rate, ranking, winner,
  validation, paper, finite-window-vs-GRU, and self-ID interpretations

M2508-M2509:
  added and audited a bounded runtime/inference-cost report
  timed path: recurrent_features_tensor_plus_actor_mean_tanh
  measurement rows: 300
  batch sizes: 1, 8, 32
  p50 forward time: batch1 42.13us, batch8 76.355us, batch32 124.291us
  model parameter count: 164679
  measurement scope: local CPU actor-only forward timing on seeded synthetic
  shape-only 72-observation tensors

M2510-M2511:
  materialized and audited a structured known failure taxonomy
  taxonomy rows: 10
  failure categories: 9
  severity counts: high 4 / medium 5 / low 1
  source artifacts: present
  actor contract: 72/3
  accepted scope: known limitations and route implications only
```

The route plan in `docs/post-m2470-route-plan.md` identifies Route A as the
engineering-controller mainline:

```text
freeze a usable actuator-level active-safety controller baseline
```

M2493-M2511 filled the near-term Route A engineering artifact list: actor
contract, public benchmark pack, known failure taxonomy, runtime/inference-cost
report, scenario-role metric report, and baseline comparison diagnostics.

## Supported Claims

Supported:

```text
The Route A engineering artifact set is coherent and claim-bounded.

The source-only diagnostic pack can support later export/release review if the
same claim boundary is preserved.

The admitted M1154 recurrent actor checkpoint is consistently tracked under the
P0 observation 72 / action 3 deployed contract.

The runtime report provides local actor-only inference-cost evidence for the
admitted checkpoint, not simulator throughput or behavior quality.

The known failure taxonomy gives Route A a structured limitation artifact with
source references and forbidden interpretations.
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

M2512 did not run a simulator, execute policy actions, train, rank controllers,
compute outcomes, or measure behavior. Route A artifacts are engineering
diagnostic, packaging, deployability-cost, and limitation artifacts only.

## Failure Taxonomy Summary

Controlled:

```text
contract_violation:
  controlled by repeated checkpoint admission and 72/3 actor/action gates.

lineage_invalid:
  controlled by committed manifests, docs, run summaries, source references,
  review artifacts, queue/status rows, and scoreboard entries.

metric_artifact:
  controlled by explicit claim boundaries. Role metrics, open-loop baselines,
  runtime rows, and taxonomy rows are not treated as outcome semantics.

objective_overfit:
  partly controlled by stopping Route A static artifact accumulation at M2512
  and routing to a behavior/outcome protocol instead of another fixed public
  artifact.
```

Unresolved:

```text
behavior_regression:
  unresolved. Route A does not yet define or execute audited outcome semantics.

scenario_sampling_failure:
  unresolved. Current-sim readiness remains diagnostic/mining context, and
  source-only fixtures remain fixed public diagnostic surfaces.

high_fidelity_validation:
  unresolved. No external high-fidelity backend was installed, imported, or
  run, and no validation verdict was made.
```

## Public Gate Overfit Risk

Risk entering M2512: `medium`.

Reason:

```text
The artifact set is useful and internally consistent, but another static
export, packaging, runtime, or taxonomy task would mostly optimize fixed public
surfaces and documentation gates.
```

Risk reduction:

```text
Do not add another static Route A artifact as the immediate next milestone.

Move to a behavior/outcome protocol design that defines how future evidence can
measure behavior quality without oracle actor inputs, hidden dynamics, ranking
shortcuts, success-rate overclaims, or high-fidelity validation overclaims.
```

## Next Branch Decision

Decision:

```text
promote_to_engineering_controller_behavior_outcome_protocol
```

Rationale:

```text
Public export preparation is now possible only as a bounded review activity,
but it is not the highest-leverage next research step.

The known failure taxonomy identifies the more important unresolved gap:
behavior regression and outcome semantics are unmeasured.

The project should define a non-oracle behavior/outcome protocol before any
future measured rollout, controller ranking, success-rate interpretation, or
validation claim.

This is still not a simulation or rollout milestone. The next milestone should
be design-only and should preserve the actor input/action contract.
```

Required next route:

```text
m2513-engineering-controller-behavior-outcome-protocol-design
```

M2513 must define admissible outcome metrics, forbidden metrics/oracle signals,
row schema, audit gates, source-only versus future high-fidelity validation
layers, and claim boundaries. It must not run simulation, execute policy
actions, train, rank controllers, select a winner, compute a success-rate
verdict, or claim driver performance.
