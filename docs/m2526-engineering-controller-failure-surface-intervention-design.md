# M2526 Engineering Controller Failure-Surface Intervention Design

- status: completed
- decision: `route_to_failure_surface_intervention_materialization_preflight`
- manifest: `experiments/manifests/m2526-engineering-controller-failure-surface-intervention-design.json`
- design artifact: `docs/m2526-engineering-controller-failure-surface-intervention-design.md`
- parent synthesis: `docs/m2525-engineering-controller-bounded-measured-behavior-panel-branch-synthesis.md`
- next milestone: `m2527-engineering-controller-failure-surface-intervention-materialization-preflight`
- external high-fidelity simulation installed/imported/executed in M2526: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2526: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2526: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Decision

M2526 defines the first Route A intervention contract after the bounded
measured-behavior branch. The design target is narrow and operational:

```text
road-boundary preservation:
  M1154 leaves the road in all stable_aes and drift_required_recovery
  fresh-seed source-only diagnostic rows.

unavoidable-mitigation behavior:
  M1154 collides and leaves the road in all unavoidable_mitigation fresh-seed
  source-only diagnostic rows.

command conflict:
  M1154 has simultaneous_throttle_brake_fraction 1.0 in all fresh-seed
  source-only diagnostic rows.
```

The design routes to a materialization preflight that writes intervention-plan
artifacts before any training or policy action. It does not rank controllers,
select a winner, promote a checkpoint, compute success-rate, or claim driver
performance.

## Contract Boundary

The intervention must preserve the deployed P0 actor contract:

```text
observation shape: 72
action shape: 3
actor encoder: human_view_online_gru
action horizon: 1
single actor: true
rule-switching controller modes: forbidden
```

Allowed actor signals are only the signals already admitted by
`docs/observation-contract.md`:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space boundary geometry
ego-frame obstacle geometry and relative motion
online GRU recurrent state
```

Forbidden actor inputs remain forbidden even if they are useful for reward,
logging, candidate mining, or evaluator gates:

```text
mu, mass, tire stiffness, brake scale, actuator tau, hidden dynamics
scenario role labels, feasibility classes, oracle outcome labels
slip, tire force, TTC, required clearance, oracle stopping distance
speed_ref, beta_target, path error, heading error, path curvature
reward terms, progress counters, collision labels, success labels
controller mode or hand-written rule switch state
```

Evaluator-side metrics may use road margin, collision, obstacle passage,
severity, and command-conflict fields because those are not actor inputs. The
future implementation must keep this separation explicit in artifact schemas.

## Intervention Targets

Target 1: road-boundary preservation.

```text
protected diagnostic rows:
  m1154_policy_actor / stable_aes / seeds 252300-252304
  m1154_policy_actor / drift_required_recovery / seeds 253300-253304

current failure:
  road_departure_event true: 5/5 stable_aes
  road_departure_event true: 5/5 drift_required_recovery
  minimum_road_margin_m mean: -6.624060 stable_aes
  minimum_road_margin_m mean: -6.423963 drift_required_recovery

design requirement:
  future repair must target nonnegative road margin on protected source-only
  rows while preserving collision avoidance as a guardrail.
```

Target 2: unavoidable mitigation.

```text
protected diagnostic rows:
  m1154_policy_actor / unavoidable_mitigation / seeds 254300-254304

current failure:
  collision_event true: 5/5
  road_departure_event true: 5/5
  minimum_road_margin_m mean: -2.438611

design requirement:
  future repair must reduce severity and road-boundary loss without treating
  unavoidable rows as success/failure labels or driver-performance verdicts.
  The straight_full_brake_open_loop reference remains a mitigation anchor, not
  a winner.
```

Target 3: command conflict.

```text
protected diagnostic rows:
  all 15 M1154 fresh-seed rows from M2523

current failure:
  simultaneous_throttle_brake_fraction mean: 1.0
  steering/throttle/brake saturation fraction mean: 0.0

design requirement:
  future repair should penalize simultaneous physical throttle and brake while
  preserving the three-action output contract. A permitted implementation is an
  evaluator/reward/action-regularization term based on the actor output or
  physical actuator state, not an additional actor input or rule switch.
```

## Protected Regression Rows

M2527 must materialize the following protected-row groups:

```text
road_boundary_primary:
  stable_aes seeds: 252300 252301 252302 252303 252304
  drift_required_recovery seeds: 253300 253301 253302 253303 253304
  subject: m1154_policy_actor
  guardrails: collision_event must not regress, actor contract 72/3, no hidden
  actor inputs, all attempted rows retained

mitigation_primary:
  unavoidable_mitigation seeds: 254300 254301 254302 254303 254304
  subject: m1154_policy_actor
  guardrails: severity_proxy and road margin tracked separately, no success
  verdict field, no winner selection

reference_context:
  straight_full_brake_open_loop stable_aes seeds: 252300-252304
  straight_full_brake_open_loop unavoidable_mitigation seeds: 254300-254304
  coast_open_loop all roles: diagnostic collision/road-boundary anchor only
```

These rows are proof/regression surfaces for the next repair. They are not
private holdout and are not sufficient for promotion. Later generalization
must use fresh seeds or a broader source distribution.

## Materialization Plan

M2527 should write a structured plan directory:

```text
runs/m2527_engineering_controller_failure_surface_intervention_plan/summary.json
runs/m2527_engineering_controller_failure_surface_intervention_plan/intervention_spec.json
runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv
runs/m2527_engineering_controller_failure_surface_intervention_plan/implementation_gate_matrix.csv
runs/m2527_engineering_controller_failure_surface_intervention_plan/candidate_config_patch_plan.json
```

Required contents:

```text
intervention_spec.json:
  actor_contract_id
  forbidden_actor_input_fields
  road_boundary_objective
  mitigation_objective
  command_conflict_objective
  allowed_reward_or_evaluator_fields
  no_rule_switching_assertions

protected_regression_rows.csv:
  role
  seed
  subject
  source_row_id
  failure_surface
  protected_metric
  guardrail_metric
  source_artifact

implementation_gate_matrix.csv:
  proof gates on protected rows
  generalization gates on fresh source-only seeds
  no-contract-change gate
  no-ranking/no-success-rate/no-validation-claim gate

candidate_config_patch_plan.json:
  proposed reward or evaluator knobs
  proposed action-conflict regularizer
  active training config overwrite: false
  training_started: false
```

The materialization preflight may add source code to generate these artifacts,
but it must not train, run a policy, or change the active checkpoint.

## Follow-Up Decision

M2526 routes to:

```text
m2527-engineering-controller-failure-surface-intervention-materialization-preflight
```

Reason:

```text
The project should not jump from source-only failure diagnosis directly to
training or checkpoint promotion. It first needs a concrete intervention spec,
protected regression rows, and gate matrix so any later repair can be judged
without hidden inputs, rule switches, ranking shortcuts, or success-rate
overclaims.
```
