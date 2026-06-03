# M2535 Engineering Controller Failure-Surface Mitigation-Preserving Repair Design

- status: completed
- decision: `route_to_mitigation_preserving_repair_branch_synthesis`
- manifest: `experiments/manifests/m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design.json`
- design artifact: `docs/m2535-engineering-controller-failure-surface-mitigation-preserving-repair-design.md`
- parent localization: `runs/m2534_engineering_controller_failure_surface_mitigation_regression_localization/summary.json`
- next milestone: `m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis`
- external high-fidelity simulation installed/imported/executed in M2535: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2535: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2535: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Decision

M2535 converts the M2534 localization into a bounded repair objective, but the
next milestone must be branch synthesis before any execution because the
failure-surface intervention branch has reached its synthesis cadence. The
design target is not seed `254302` as an isolated row; that row is a sentinel
showing that the M2532 command-conflict projection can improve road margin and
remove simultaneous throttle-brake while washing out mitigation severity on a
low-baseline unavoidable-mitigation case.

M2535 recommends a bounded mitigation-preserving execution route because M2534
found:

```text
mitigation rows: 5
improved rows: 4
regressed rows: 1
regressed seed: 254302
regressed severity delta: +0.674427724901157
regressed road margin delta: +4.456761035401987
regressed command conflict delta: -1.0
all mitigation rows road-margin improved: true
all mitigation rows command-conflict improved: true
metric artifact detected: false
```

Interpretation:

```text
M2532 solved too much of the command-conflict surface with a coarse actor-head
bias projection, but it did not encode mitigation severity as a retained proof
constraint. The next repair must retain the M2532 road-boundary and command-
conflict gains while adding an all-mitigation-row severity non-regression gate.
```

## Actor And Claim Boundary

The repair design preserves the deployed P0 actor contract:

```text
observation shape: 72
action shape: 3
actor encoder: human_view_online_gru
action horizon: 1
single actor: true
rule-switching controller modes: forbidden
hidden/oracle actor inputs: forbidden
```

Allowed actor inputs remain only deployed human-view signals:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space boundary geometry
ego-frame obstacle geometry and relative motion
online recurrent state
```

Evaluator-side metrics may drive repair scoring and proof gates, but they must
not enter the actor input:

```text
minimum_road_margin_m
road_departure_event
collision_event
minimum_obstacle_clearance_m
severity_proxy
simultaneous_throttle_brake_fraction
mitigation_delta_against_reference
```

M2535 is a design milestone only. It does not train, execute policy actions,
rank controllers, select a winner, promote a checkpoint, compute success-rate,
or claim driver performance.

## Repair Objective

The synthesis-approved follow-up execution should replace the single coarse
M2532 projection criterion with a mitigation-preserving constrained objective
over all protected primary rows.

Candidate repair scoring:

```text
primary objective:
  pass mitigation severity non-regression across all mitigation_primary rows

retained proof constraints:
  retain road_boundary_proof from M2532
  retain command_conflict_proof from M2532

contract constraints:
  preserve observation shape 72
  preserve action shape 3
  do not add hidden/oracle actor input
  do not add controller mode or rule-switch state

rollback constraints:
  keep M2532 repaired checkpoint immutable
  keep M2528 candidate config immutable
  do not overwrite active configs
  write new checkpoint only under the follow-up execution run directory
```

The objective must operate at the protected-group level, not at one seed:

```text
mitigation_primary:
  every row must have severity_delta <= 0 within numeric tolerance
  every row must have road_margin_delta_m > 0
  collision_regressed must remain false
  seed 254302 is a sentinel and must pass, but it is not the sole target

road_boundary_primary:
  every row that passed M2532 road_boundary_proof must retain positive
  road_margin_delta_m and no collision regression

command_conflict_primary:
  every primary protected row must retain command_conflict_delta <= 0 and
  simultaneous_throttle_brake_fraction should remain at or near zero
```

Preferred follow-up execution implementation shape:

```text
bounded actor-head repair candidate sweep
  start from M2532 repaired checkpoint as the retained-gain baseline
  evaluate bounded throttle/brake bias or small actor-head deltas
  score candidates on all 15 primary protected rows and 30 reference rows
  select a candidate only if retained gates and mitigation non-regression pass
  write the full candidate sweep so rejected rows remain auditable
```

The sweep is allowed to run bounded source-only policy actions only in a later
execution preflight approved by synthesis. It is not allowed to import an
external simulator, change actor input fields, rank controller families,
compute success-rate, or promote a checkpoint.

## Proof Gates Before Generalization

The follow-up execution must evaluate proof gates before any fresh/generalization route:

```text
contract_p0_72_3:
  observation_shape == 72
  action_shape == 3
  actor_input_contract_changed == false

no_oracle_actor_inputs:
  actor_input_leak_flags == none
  hidden/oracle input flags false
  controller_mode and mu absent from actor input

retained_road_boundary_proof:
  road_boundary_primary rows retain M2532 road-margin gains
  road_departure_event does not worsen
  collision_event does not regress

mitigation_preserving_proof:
  mitigation_primary rows have severity_delta <= 0
  mitigation_primary rows retain positive road_margin_delta_m
  no collision regression

retained_command_conflict_proof:
  primary protected rows retain simultaneous_throttle_brake_fraction
  non-increase relative to M2532, preferably zero

no_ranking_no_success_rate:
  ranking_run, winner_selected, success_rate_computed remain false
```

Fresh/generalization evidence stays deferred until the retained proof gates and
mitigation-preserving proof pass. Passing the follow-up protected proof would
permit a future fresh-seed/generalization design, not a checkpoint promotion.

## Failure Taxonomy

The follow-up execution must classify failures without weakening gates:

```text
contract_violation:
  observation/action shape changes or hidden/oracle inputs enter actor input

training_instability:
  candidate sweep or repair update cannot produce finite actions or checkpoint

proof_washout:
  mitigation improves while road-boundary or command-conflict retained gates
  regress, or retained gates improve while mitigation severity regresses

behavior_regression:
  collision, road-boundary, command-conflict, or severity guardrails worsen on
  protected or reference rows

objective_overfit:
  the selected candidate only fixes seed 254302 or only the public protected
  rows without an objective-level group criterion

scenario_sampling_failure:
  protected rows pass but are too narrow to support the next claim, so the next
  route must be fresh/generalization evidence rather than promotion

lineage_invalid:
  checkpoint, source checkpoint, M2528 config, M2534 localization, or protected
  rows cannot be traced from artifacts

metric_artifact:
  summary claims gate success without row-level candidate and gate evidence
```

## Follow-Up Decision

M2535 registers:

```text
m2536-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis
```

M2536 must synthesize the M2526-M2535 branch and decide whether the
mitigation-preserving repair objective is strong enough to continue to a later
bounded execution preflight. If synthesis approves execution and that execution
cannot find a candidate that passes mitigation-preserving proof without washing
out M2532 road-boundary or command-conflict gains, the next route must be
branch synthesis or pivot rather than a third protected public-gate repair.
