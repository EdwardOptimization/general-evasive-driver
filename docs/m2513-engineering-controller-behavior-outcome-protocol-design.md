# M2513 Engineering Controller Behavior/Outcome Protocol Design

- status: completed
- decision: `behavior_outcome_protocol_design_admit_no_rollout_materialization_preflight`
- manifest: `experiments/manifests/m2513-engineering-controller-behavior-outcome-protocol-design.json`
- parent synthesis: `docs/m2512-engineering-controller-route-a-artifact-set-branch-synthesis.md`
- no rollout: `true`
- no policy action: `true`
- no external high-fidelity simulation install/import/execution: `true`
- no training/replay/PPO/ranking/winner/success-rate/verdict claim: `true`
- next milestone: `m2514-engineering-controller-behavior-outcome-protocol-materialization-preflight`

## Why This Protocol Exists

M2512 closed the Route A static artifact branch. The remaining engineering gap
is not another export pack, runtime row, or taxonomy row. The limiting gap is
that Route A does not yet define audited behavior or outcome semantics.

M2513 therefore designs the behavior/outcome protocol before any new measured
run. The design has three jobs:

```text
1. define evaluator-side behavior and outcome rows without changing actor input
2. separate diagnostic source-only evidence from future validation evidence
3. prevent outcome rows from being interpreted as driver performance, ranking,
   success-rate, high-fidelity validation, paper, finite-window-vs-GRU, or
   self-identification claims
```

The protocol is an engineering evidence path, not a paper comparison protocol
and not a controller-family ranking protocol.

## Actor Contract Boundary

The deployable actor contract remains:

```text
observation shape: 72
action shape: 3
action: [steering_command, throttle_command, brake_command]
actor encoder: human_view_online_gru
action sequence horizon: 1
```

The actor may use only the human-view P0 inputs documented in
`docs/observation-contract.md`: ego response, actuator state, previous physical
commands, ego-frame road/free-space geometry, obstacle geometry, and recurrent
state.

The behavior/outcome protocol is evaluator-side. It may read logs needed to
compute outcome rows, but it must never feed those labels, derived outcomes, or
oracle diagnostics back into actor input.

## Protocol Layers

Future rows must carry exactly one evidence layer:

| layer | purpose | allowed claim |
| --- | --- | --- |
| `source_only_diagnostic` | use the existing HF0/source-only fixtures and Route A artifacts to debug outcome schema and row completeness | diagnostic behavior instrumentation only |
| `current_sim_diagnostic_mining` | use current-sim as a fast mining/readiness layer when explicitly admitted by a later manifest | diagnostic/mining evidence only |
| `future_high_fidelity_validation` | use an external high-fidelity backend only after interface parity, action mapping, and no-oracle gates are separately passed | validation evidence only after a later validation audit |

Layer rules:

```text
source_only_diagnostic:
  may expose row-schema gaps, behavior envelope gaps, and metric completeness
  issues; must not claim driver performance or scenario generalization.

current_sim_diagnostic_mining:
  may help mine failures and candidate panels; must not claim current-sim
  benchmark readiness while the post-M2470 readiness blockers remain open.

future_high_fidelity_validation:
  cannot be used until a separate external-backend parity/admission milestone
  exists; M2513 does not admit or run that layer.
```

## Scenario Roles

Rows must carry one scenario role as metadata, never as actor input:

```text
stable_avoidable
stable_aes
drift_required_recovery
hidden_dynamics_robustness
unavoidable_mitigation
```

Role semantics:

| role | primary evaluator family | interpretation boundary |
| --- | --- | --- |
| `stable_avoidable` | avoidance outcome | diagnostic until denominators, seeds, and layer gates are complete |
| `stable_aes` | steering/braking avoidance outcome | diagnostic until reset/sampling and outcome gates are audited |
| `drift_required_recovery` | controlled high-response recovery | must allow high yaw/lateral response but require recovery semantics before any quality claim |
| `hidden_dynamics_robustness` | response robustness | must not expose hidden dynamics to actor input |
| `unavoidable_mitigation` | mitigation severity | must not be scored as ordinary success |

## Admissible Metrics

Admissible evaluator-side metrics are split into metric families. A row may
contain many metrics, but a later manifest must explicitly admit which family
can be aggregated.

```text
contract metrics:
  observation_shape
  action_shape
  actor_contract_id
  actor_input_leak_flags
  action_finite
  action_within_bounds

episode status metrics:
  episode_started
  episode_completed
  terminal_status
  step_count
  reset_status
  backend_status

avoidance and boundary metrics:
  collision_event
  obstacle_passed_event
  road_departure_event
  minimum_obstacle_clearance_m
  minimum_road_margin_m
  final_road_margin_m

response and recovery metrics:
  maximum_abs_lateral_velocity
  maximum_abs_yaw_rate
  maximum_abs_lateral_position
  final_abs_lateral_velocity
  final_abs_yaw_rate
  recovery_time_proxy_s

actuator and smoothness metrics:
  steering_saturation_fraction
  throttle_saturation_fraction
  brake_saturation_fraction
  command_delta_l1_mean
  simultaneous_throttle_brake_fraction

mitigation metrics:
  collision_speed_proxy
  impact_angle_proxy
  severity_proxy
  mitigation_delta_against_reference

metadata and completeness metrics:
  evidence_layer
  scenario_role
  subject_id
  fixture_id
  seed
  metric_completeness_flags
  diagnostic_only_no_ranking_claim
```

Metric caveats:

```text
minimum_obstacle_clearance_m:
  may be computed from logged geometry after the fact; it must not be supplied
  to actor input as required clearance or a decision hint.

mitigation_delta_against_reference:
  may compare against a pre-registered diagnostic reference only after a later
  manifest defines the reference denominator; it is not a controller ranking.

recovery_time_proxy_s:
  must be based on logged ego response and road/free-space geometry, not on
  path-error, heading-error, beta-target, or reference-trajectory oracle terms.
```

## Forbidden Metrics And Signals

Forbidden actor inputs remain forbidden:

```text
mu
mass, inertia, CG, tire stiffness, brake scale, drive scale, actuator tau
slip, tire force, tire saturation labels
controller mode or scenario role
speed_ref, beta_target, path error, heading error, path curvature
TTC, required clearance, oracle stopping distance
oracle feasibility labels, AEB/AES/drift labels
reward terms, progress counters, collision labels, success labels
```

Forbidden outcome shortcuts:

```text
single scalar driver score
mixed-role success_rate aggregate
controller ranking or winner selection
scenario-generalization verdict from fixed public fixtures
current-sim benchmark verdict from source-only or reset/static rows
high-fidelity validation readiness from source-only rows
paper-level claim from engineering diagnostic rows
finite-window-vs-GRU or level3 self-ID conclusion
manual rule-switch labels or controller-mode labels as outcome accept criteria
precomputed avoidance/progress labels as success criteria
```

Unsupported metrics must be recorded as explicit gaps. They must not be
silently approximated into a claim.

## Required Row Schema

Future materialization should define these columns:

```text
protocol_version
milestone_id
run_id
row_id
evidence_layer
surface_id
scenario_role
fixture_id
seed
subject_id
checkpoint_path
actor_contract_id
observation_shape
action_shape
actor_encoder
action_horizon
actor_input_leak_flags
reset_status
backend_status
episode_started
episode_completed
step_count
terminal_status
action_finite
action_within_bounds
collision_event
obstacle_passed_event
road_departure_event
minimum_obstacle_clearance_m
minimum_road_margin_m
final_road_margin_m
maximum_abs_lateral_velocity
maximum_abs_yaw_rate
maximum_abs_lateral_position
final_abs_lateral_velocity
final_abs_yaw_rate
recovery_time_proxy_s
steering_saturation_fraction
throttle_saturation_fraction
brake_saturation_fraction
command_delta_l1_mean
simultaneous_throttle_brake_fraction
collision_speed_proxy
impact_angle_proxy
severity_proxy
mitigation_delta_against_reference
metric_completeness_flags
diagnostic_only_no_ranking_claim
claim_scope
forbidden_interpretation
source_artifact
```

Every row must be auditable back to a source artifact. Missing metrics must be
encoded in `metric_completeness_flags`, not dropped from the denominator.

## Aggregation Rules

Allowed immediately after M2513:

```text
no-rollout materialization of protocol schema
no-rollout registry of metric families and forbidden interpretations
row completeness checks against existing source artifacts
diagnostic summaries that preserve diagnostic_only_no_ranking_claim=true
```

Forbidden until later manifests explicitly admit them:

```text
source-only performance score
current-sim benchmark readiness score
controller-family ranking
winner selection
checkpoint promotion
global success-rate verdict
high-fidelity validation verdict
paper-level comparison
self-identification claim
```

Aggregation discipline:

```text
Role-specific denominators must be explicit.
Mixed-role aggregates are diagnostic only unless a later manifest admits them.
Unavoidable mitigation rows must not be counted as ordinary avoidance success.
Diagnostic stress rows must not be mixed into benchmark rows.
Reference comparisons must be pre-registered and denominator-backed.
```

## Audit Gates

Pre-execution gates:

```text
actor contract 72/3 preserved
no hidden/oracle actor inputs
protocol layer present
scenario role present as metadata only
row schema complete
metric registry complete
forbidden metric registry complete
claim boundary present
```

Future execution gates, before any measured behavior claim:

```text
all attempted rows retained, including failures
reset failures separated from behavior failures
metric completeness reported per row
same-case denominators preserved for comparisons
no ranking or winner field emitted
source-only rows marked diagnostic
high-fidelity rows admitted only after external backend parity gates
```

Claim gates:

```text
source_only_diagnostic rows can support schema and behavior-instrumentation
claims only.

current_sim_diagnostic_mining rows can support mining/readiness diagnostics
only.

future_high_fidelity_validation rows can support validation claims only after a
separate high-fidelity validation audit.

No layer can support paper self-ID, finite-window-vs-GRU, or controller-family
ranking without a separate paper-route manifest and comparison protocol.
```

## Failure Taxonomy Mapping

The protocol addresses Route A limitations as follows:

```text
metric_artifact:
  controlled by row schema, metric registry, completeness flags, and forbidden
  interpretations.

behavior_regression:
  not resolved by M2513, but converted into a future measurable protocol gap.

scenario_sampling_failure:
  not resolved by M2513; layer and denominator fields prevent fixed fixtures
  from being treated as scenario generalization.

objective_overfit:
  reduced by moving away from another static Route A artifact toward a future
  behavior evidence path.

validation_boundary:
  preserved by separating source-only diagnostics from future high-fidelity
  validation.
```

## Materialization Plan

M2514 should be a no-rollout materialization preflight. It should create
machine-readable protocol artifacts:

```text
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/summary.json
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/protocol_schema.json
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/audit_gate_registry.csv
runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/layer_registry.csv
```

M2514 must not run simulation, execute policy action, train, rank, compute
success-rate verdicts, select a winner, or claim performance. Its output should
prove only that the protocol can be represented and checked before any measured
behavior run.

## Decision

Admit:

```text
m2514-engineering-controller-behavior-outcome-protocol-materialization-preflight
```

The follow-up should materialize the protocol as schema/registry artifacts and
then route to a result audit before any implementation that executes policy
actions or measured rollouts.
