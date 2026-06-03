# M2525 Engineering Controller Bounded Measured Behavior Panel Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- decision: `promote_to_engineering_controller_failure_surface_intervention`
- manifest: `experiments/manifests/m2525-engineering-controller-bounded-measured-behavior-panel-branch-synthesis.json`
- synthesis artifact: `docs/m2525-engineering-controller-bounded-measured-behavior-panel-branch-synthesis.md`
- parent evidence window: `m2521` through `m2524`
- next milestone: `m2526-engineering-controller-failure-surface-intervention-design`
- external high-fidelity simulation installed/imported/executed in M2525: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2525: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2525: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Evidence Summary

The bounded measured behavior panel branch has enough accepted source-only
diagnostic evidence to stop adding more panels and route to an intervention
design:

```text
M2521-M2522:
  fixed-seed bounded source-only measured behavior panel materialized and
  audited
  telemetry rows: 900
  measured behavior rows: 9
  measured event rows: 9
  metric completeness rows: 40
  subjects: m1154_policy_actor, coast_open_loop, straight_full_brake_open_loop
  roles: stable_aes, drift_required_recovery, unavoidable_mitigation
  actor/action contract: P0 observation 72 / action 3
  all attempted subject-role rows retained: true
  all registered metrics supported: true
  ranking/winner/success-rate/verdict claims: false

M2523-M2524:
  fresh-seed source-only measured behavior panel materialized and audited
  seed panel rows: 15
  fresh seeds per role: 5
  telemetry rows: 4500
  measured behavior rows: 45
  measured event rows: 45
  metric completeness rows: 40
  denominator gaps: 0
  all attempted subject-role-seed rows retained: true
  actor/action contract: P0 observation 72 / action 3
  all registered metrics supported: true
  ranking/winner/success-rate/verdict claims: false
```

The fresh-seed panel repeats the same diagnostic failure surface rather than
revealing a denominator artifact:

```text
m1154_policy_actor stable_aes:
  rows: 5
  collision_event true: 0
  road_departure_event true: 5
  obstacle_passed_event true: 0

m1154_policy_actor drift_required_recovery:
  rows: 5
  collision_event true: 0
  road_departure_event true: 5
  obstacle_passed_event true: 2

m1154_policy_actor unavoidable_mitigation:
  rows: 5
  collision_event true: 5
  road_departure_event true: 5
  obstacle_passed_event true: 5

m1154_policy_actor command diagnostics:
  simultaneous_throttle_brake_fraction: 1.0 in all fresh-seed rows
  steering/throttle/brake saturation fraction: 0.0 in all fresh-seed rows
```

Open-loop references remain diagnostic anchors, not controller rankings:

```text
straight_full_brake_open_loop stable_aes:
  rows: 5
  collision_event true: 0
  road_departure_event true: 0

coast_open_loop all audited roles:
  collision_event true: 5 / 5 per role
```

This evidence improves Route A by identifying a repair target under the
accepted behavior/outcome protocol. It does not prove driver performance,
validation readiness, controller ranking, or paper-level self-identification.

## Supported Claims

Supported within source-only diagnostic scope:

```text
The M2521-M2524 branch produced a complete measured-behavior denominator for
the admitted actor and two reference actions on the accepted source-only role
fixtures.

The P0 deployed actor/action contract remained observation 72, action 3,
human_view_online_gru, horizon 1.

The behavior/outcome protocol can now measure collision, obstacle passage,
road departure, road margin, clearance, actuator smoothness, command conflict,
and mitigation-reference deltas without changing actor input.

The admitted M1154 actor has a repeatable source-only road-departure failure
surface in stable_aes and drift_required_recovery and a combined collision plus
road-departure failure surface in unavoidable_mitigation.

The next useful Route A branch is not another source-only panel. It is a
bounded intervention design that targets road-boundary preservation, mitigation
behavior, and command-conflict reduction while preserving the no-oracle actor
contract.
```

## Falsified Or Unsupported Claims

Falsified within the bounded source-only diagnostic branch:

```text
The admitted M1154 actor is ready to freeze as a usable engineering-controller
baseline without repair.

The fixed-seed M2521 failure surface was only a one-seed artifact.

Another measured behavior panel with the same subjects and source-only role
fixtures is the highest-leverage immediate next step.
```

Unsupported or explicitly rejected:

```text
driver performance
behavior improvement verdict
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

M2525 does not run a simulator, execute policy actions, train, rank
controllers, compute success rates, or measure fresh behavior.

## Failure Taxonomy Summary

Controlled:

```text
contract_violation:
  controlled by repeated 72/3 actor/action gates, actor_input_contract_changed
  false, no hidden/oracle actor inputs, and finite bounded action checks.

lineage_invalid:
  controlled by committed manifests, milestone docs, summaries, measured rows,
  review artifacts, queue/status rows, and scoreboard entries from M2521-M2524.

metric_artifact:
  controlled by all 40 protocol metric completeness rows being supported, with
  missing row count 0 in the fresh-seed panel.

scenario_sampling_failure:
  reduced but not resolved. M2523 expands the source-only denominator to five
  fresh seeds per admitted role, but still uses source-only diagnostic fixtures
  rather than high-fidelity or fresh current-sim distributions.
```

Still unresolved:

```text
behavior_regression:
  unresolved as a positive capability claim. The branch identifies a failure
  surface but does not train or compare a repaired controller.

objective_overfit:
  medium if the project keeps extending the same source-only panels. The
  mitigation is to close this branch and route to a targeted intervention.

validation_boundary:
  unresolved. Source-only measured behavior cannot support high-fidelity
  validation readiness or current-sim verdict claims.

controller_intervention:
  unresolved. The next branch must design a repair path before running another
  behavior panel or any promotion gate.
```

## Public Gate Overfit Risk

Risk entering M2525: `medium`.

Reason:

```text
M2521-M2524 are evidence-producing compared with the prior protocol branch,
but they are still source-only and use a small admitted fixture family. Another
same-surface panel would mostly improve local denominator optics without
changing the controller.
```

Risk reduction:

```text
Close the bounded measured behavior panel branch.

Do not register another source-only measured behavior panel as the immediate
next task.

Promote to a failure-surface intervention design that must preserve deployed
actor inputs and action shape, explicitly block rule-switching/oracle
shortcuts, and identify the next measurable repair artifact.
```

## Next Branch Decision

Decision:

```text
promote_to_engineering_controller_failure_surface_intervention
```

Rationale:

```text
The limiting Route A gap is no longer missing behavior/outcome protocol or
missing measured rows. The limiting gap is that the admitted actor's behavior
is not usable enough even on bounded source-only diagnostic surfaces.

The fresh-seed panel gives a concrete intervention target:
  road-boundary preservation failure in stable_aes and drift_required_recovery
  unavoidable_mitigation collision plus road-departure failure
  simultaneous throttle/brake command conflict in the actor rows

The next route should design a bounded repair or intervention recipe before
any implementation, training, promotion, ranking, or validation gate.
```

Required next route:

```text
m2526-engineering-controller-failure-surface-intervention-design
```

M2526 must design a repair path that can later be tested without changing the
P0 actor input/action contract. It may specify reward/curriculum, evaluation
gates, protected regression rows, and config/artifact changes, but it must not
run simulation, execute policy actions, train, rank controllers, select a
winner, compute success-rate verdicts, promote a checkpoint, claim driver
performance, or claim high-fidelity validation.
