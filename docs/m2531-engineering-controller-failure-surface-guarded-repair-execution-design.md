# M2531 Engineering Controller Failure-Surface Guarded Repair Execution Design

- status: completed
- decision: `route_to_guarded_repair_execution_preflight`
- manifest: `experiments/manifests/m2531-engineering-controller-failure-surface-guarded-repair-execution-design.json`
- design artifact: `docs/m2531-engineering-controller-failure-surface-guarded-repair-execution-design.md`
- parent audit: `docs/m2530-engineering-controller-failure-surface-intervention-repair-smoke-result-audit.md`
- next milestone: `m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight`
- external high-fidelity simulation installed/imported/executed in M2531: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2531: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2531: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Decision

M2531 closes the no-update path and defines the smallest guarded execution step
that can actually change behavior after the M2529 negative smoke.

The next milestone must not be another config-only or no-update artifact. It
must run a bounded source-only guarded repair execution from the admitted M1154
checkpoint using the M2528 candidate config as the objective boundary, then
rerun protected proof gates on the repaired candidate.

Allowed M2532 claim scope:

```text
guarded source-only repair execution preflight evidence only
```

Forbidden M2532 interpretations:

```text
driver performance
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
validation readiness
paper-level evidence
finite-window-vs-GRU result
level3 self-identification
current-sim or high-fidelity verdict
```

## Repair Execution Contract

M2532 may do a short guarded repair run only inside a pre-registered run
directory:

```text
source checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

candidate objective config:
  runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/candidate_config.json

protected gate bindings:
  runs/m2528_engineering_controller_failure_surface_intervention_config_materialization/protected_gate_bindings.csv

protected rows:
  runs/m2527_engineering_controller_failure_surface_intervention_plan/protected_regression_rows.csv
```

Actor contract remains fixed:

```text
observation shape: 72
action shape: 3
actor encoder: human_view_online_gru
action horizon: 1
single actor: true
rule-switching controller modes: forbidden
hidden/oracle actor inputs: forbidden
```

The actor still may only consume the deployed P0 observation families:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space boundary geometry
ego-frame obstacle geometry and relative motion
online recurrent state
```

The repair objective may use evaluator-side metrics that are not actor inputs:

```text
minimum_road_margin_m
road_departure_event
collision_event
minimum_obstacle_clearance_m
severity_proxy
simultaneous_throttle_brake_fraction
mitigation_delta_against_reference
```

## Bounded Repair Recipe

M2532 should use a short guarded repair run, not an unbounded promotion recipe.

Required guardrails:

```text
max repair updates: small fixed budget
source-only fixtures only
protected seed mix enabled
M2527 primary protected rows always included
reference context rows tracked as guardrails
no private holdout
no active config overwrite
no in-place mutation of M2528 candidate config
checkpoint output under the M2532 run directory only
```

The repair loss/objective should be a weighted candidate objective built from
M2528 coefficients:

```text
road boundary:
  increase minimum_road_margin_m toward nonnegative
  reduce road_departure_event
  do not introduce collision regression

mitigation:
  reduce severity_proxy on unavoidable_mitigation rows
  reduce road-boundary loss separately from collision labels
  do not reinterpret unavoidable rows as success/failure labels

command conflict:
  reduce simultaneous physical throttle and brake
  keep action shape 3
  do not add controller_mode or rule-switch state
```

M2532 may implement the repair with a small guarded RL or differentiable
surrogate update path if it can preserve the actor contract and write the
required traces. If the implementation cannot produce a valid checkpoint and
post-repair protected gate evaluation, the milestone must fail and route to
branch synthesis or implementation repair rather than weakening the gates.

## Required M2532 Artifacts

M2532 must write:

```text
runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json
runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repair_training_trace.csv
runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repaired_checkpoint_manifest.json
runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/post_repair_smoke_rows.csv
runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/protected_gate_evaluation.csv
runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/candidate_config_snapshot.json
```

Summary must separately report:

```text
repair_execution_started
repair_training_started
repaired_checkpoint_written
actor_contract_shape_72_action_3
hidden_or_oracle_actor_inputs_required
candidate_config_mutated
active_config_overwritten
protected_proof_gates_all_passed
protected_proof_gate_fail_count
fresh_generalization_run
ranking_run
winner_selected
success_rate_computed
checkpoint_promoted
driver_performance_claim_made
```

`status_pass` for M2532 should mean the guarded execution and artifacts are
complete. It must not mean proof gates passed unless
`protected_proof_gates_all_passed` is explicitly true.

## Proof Gates Before Generalization

M2532 must evaluate proof gates before any fresh/generalization interpretation:

```text
contract_p0_72_3:
  observation_shape == 72
  action_shape == 3
  actor_input_contract_changed == false

no_oracle_actor_inputs:
  actor_input_leak_flags == none
  hidden/oracle input flags false
  controller_mode and mu absent from actor input

road_boundary_proof:
  road_boundary_primary rows improve minimum_road_margin_m
  road_departure_event does not worsen
  collision_event does not regress

mitigation_proof:
  mitigation_primary rows reduce severity_proxy
  minimum_road_margin_m improves
  no success-rate or winner field is emitted

command_conflict_proof:
  primary protected rows reduce simultaneous_throttle_brake_fraction

no_ranking_no_success_rate:
  ranking_run, winner_selected, success_rate_computed remain false
```

Fresh/generalization evidence is required after proof gates pass and before any
future promotion, but M2532 itself remains a preflight and must not promote.

## Rollback And Failure Taxonomy

Rollback boundary:

```text
source checkpoint remains unchanged
M2528 candidate config remains unchanged
active configs remain unchanged
repaired checkpoint, if written, stays inside the M2532 run directory
no checkpoint promotion metadata is written
```

Failure classification:

```text
contract_violation:
  observation/action shape changes or hidden/oracle inputs enter actor input

training_instability:
  repair update cannot produce finite actions or a readable checkpoint

proof_washout:
  one protected proof surface improves while another protected proof surface
  regresses

behavior_regression:
  collision or road-boundary guardrails worsen on protected/reference rows

objective_overfit:
  only protected public rows improve and fresh/generalization evidence is not
  available for a later route

scenario_sampling_failure:
  source-only protected rows are too narrow to support the next claim

lineage_invalid:
  repaired checkpoint, source checkpoint, candidate config, or protected rows
  cannot be traced from artifacts

metric_artifact:
  summary claims proof success without row-level gate evidence
```

## Follow-Up

M2531 registers:

```text
m2532-engineering-controller-failure-surface-guarded-repair-execution-preflight
```

M2532 must either produce new closed-loop repair behavior evidence under the
contract above or fail explicitly. If it fails the same road-boundary,
mitigation, and command-conflict proof gates again, the branch reaches the
same-failure repeat threshold and must synthesize or pivot before another
repair attempt.
