# M2540 Engineering Controller Route A Baseline And Interface Pivot Design

- status: completed
- decision: `route_to_route_a_baseline_and_interface_materialization_preflight`
- manifest: `experiments/manifests/m2540-engineering-controller-route-a-baseline-and-interface-pivot-design.json`
- design artifact: `docs/m2540-engineering-controller-route-a-baseline-and-interface-pivot-design.md`
- parent synthesis: `docs/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md`
- next milestone: `m2541-engineering-controller-route-a-baseline-and-interface-materialization-preflight`
- external high-fidelity simulation installed/imported/executed in M2540: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2540: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2540: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2539 closed the failure-surface protected-row repair loop. M2540 opens a new
post-pivot Route A branch that prepares two things before any new training,
benchmark, or repair execution:

```text
1. Route A engineering baseline evidence map.
2. HF0 interface preparation map.
```

The design does not promote M2532 or M2537, and it does not claim driver
performance. Their repaired checkpoints are diagnostic baseline candidates only
because they are behavior-changing artifacts with known protected proof
limitations.

## Route Boundary

Allowed engineering claim after later materialization:

```text
deployable actuator-level RL diagnostics can be organized around a preserved
human-view actor contract, known failure taxonomy, runtime-cost evidence,
scenario-role diagnostics, and a reusable HF0 backend boundary
```

Forbidden claims:

```text
driver performance
deployment readiness
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
fresh/generalization result
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
current-sim or high-fidelity validation verdict
```

## Actor Input And Output Contract

The pivot keeps the canonical P0 contract:

```text
observation_shape: 72
action_shape: 3
actor_encoder: human_view_online_gru
action contract: [steer_command, throttle_command, brake_command]
```

Actor-visible inputs remain:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent/history state
```

Actor-forbidden inputs remain:

```text
mu
mass
tire stiffness
brake scale
actuator tau
slip or tire force
oracle feasibility
AEB/AES/drift labels
controller mode
speed_ref
beta_target
path error
heading error
path curvature
TTC
required clearance
oracle stopping distance
reward terms
collision/success/progress labels
```

Diagnostics may contain hidden values for analysis, but they must stay outside
`ActorView`, `P0ObservationExtractor`, and actor checkpoint inputs.

## Baseline Checkpoint List

M2541 should materialize a `baseline_checkpoint_list.csv` with these rows:

```text
m1154_original:
  checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
  role: original Route A diagnostic baseline
  promotion_status: historical promoted checkpoint, not re-promoted by this branch
  known_limit: public protected failure surfaces exposed by M2529-M2539

m2532_guarded_repair:
  checkpoint: runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt
  role: behavior-changing guarded repair diagnostic candidate
  promotion_status: not promoted
  known_limit: mitigation_proof failed 4/5 improved 1/5 regressed

m2537_mitigation_preserving_repair:
  checkpoint: runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt
  role: behavior-changing retained-gate diagnostic candidate
  promotion_status: not promoted
  known_limit: retained road-boundary and command-conflict proof pass, mitigation_proof still fails
```

Required columns:

```text
checkpoint_id
checkpoint_path
source_milestone
source_summary
actor_contract_id
observation_shape
action_shape
actor_encoder
behavior_changed_from_parent
proof_status
promotion_status
allowed_use
forbidden_interpretation
source_exists
```

The list is a lineage artifact, not a ranking. It must not select a winner.

## Actor I/O Contract Snapshot

M2541 should write `actor_io_contract_snapshot.md` and
`actor_io_contract_snapshot.json` from the existing contract sources:

```text
docs/observation-contract.md
src/autodrift/high_fidelity_interface.py
public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/actor_contract.md
```

The snapshot should record:

```text
P0_OBSERVATION_DIM = 72
ACTION_DIM = 3
ActorView fields
ActuatorView fields
RoadView and ObstacleSlotView layout
physical_control_from_action mapping
DIAGNOSTIC_ONLY_KEYS boundary
forbidden actor input list
checkpoint compatibility rule
```

The snapshot must not change the contract. If a mismatch is detected, M2541
must route to artifact repair instead of materialization success.

## Public Benchmark Pack Map

M2541 should write `route_a_artifact_map.csv` covering existing Route A
artifacts:

```text
docs/post-m2470-route-plan.md
docs/observation-contract.md
public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505/*
runs/m2508_engineering_controller_runtime_inference_cost_report/*
runs/m2510_engineering_controller_known_failure_taxonomy/*
runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/*
docs/m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis.md
```

Required columns:

```text
artifact_id
path
artifact_type
source_milestone
route_a_role
included_in_materialization
claim_scope
forbidden_interpretation
source_exists
```

This map should preserve the distinction between:

```text
diagnostic baseline evidence
runtime-cost evidence
failure taxonomy evidence
protected proof evidence
interface-boundary evidence
```

It must not collapse those into a single performance score.

## Known Failure Taxonomy Extension

M2541 should write `known_failure_taxonomy_extension.csv` or include equivalent
rows in the materialized taxonomy map. It should carry forward the existing
M2510 categories and add the post-M2539 failure surface:

```text
repeated_mitigation_proof_failure:
  category: behavior_regression / proof_washout / objective_overfit
  evidence: M2532 and M2537 both leave mitigation_proof failing with one row
  implication: public protected-row repair is saturated; route to broader
    baseline/interface evidence before another repair

public_protected_row_overfit_risk:
  category: objective_overfit
  evidence: M2539 public-gate overfit risk high
  implication: do not continue M2537-like repair without synthesis and broader evidence
```

The taxonomy remains diagnostic. It does not prove driver quality.

## Runtime And Inference-Cost Report Link

M2508 already provides actor-only forward timing for the original M1154
checkpoint:

```text
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
actor_forward_pass_run: true
measurement_row_count: 300
synthetic_observation_source: seeded_normal_shape_only
```

M2541 should not rerun timing yet. It should map this as current available
runtime evidence and mark gaps:

```text
runtime_missing_for_m2532: true
runtime_missing_for_m2537: true
runtime_not_simulator_throughput: true
runtime_not_behavior_quality: true
```

A later materialization or benchmark branch may run comparable runtime reports
for M2532/M2537 if the synthesis deems it useful.

## Scenario-Role Metric Report Plan

M2541 should write `scenario_role_metric_report_plan.csv` for the Route A
diagnostic roles:

```text
stable_avoidable
stable_aes
drift_required_recovery
unavoidable_mitigation
hidden_dynamics_robustness
actuator_delay_noise
unseen_dynamics_range
```

Required columns:

```text
scenario_role
current_source_artifact
available_metrics
missing_metrics
gate_tier
claim_scope
next_materialization_needed
forbidden_interpretation
```

The plan should explicitly separate diagnostic metrics from outcome metrics:

```text
diagnostic metrics:
  finite action
  bounded action
  saturation fraction
  state envelope
  backend status
  observation/action shape

outcome metrics requiring later gated evidence:
  collision
  road departure
  obstacle clearance
  mitigation severity
  recovery quality
  fresh/generalization retention
```

## HF0 Interface Boundary Map

M2541 should write `hf0_interface_boundary_map.csv` and `hf0_interface_contract.md`.

Rows should cover:

```text
DynamicsBackend.reset
DynamicsBackend.step
DynamicsBackend.close
BackendResetRequest
BackendResetResult
BackendStepResult
ActorView
EgoView
ActuatorView
RoadView
ObstacleSlotView
P0ObservationExtractor
physical_control_from_action
validate_actor_action
DIAGNOSTIC_ONLY_KEYS
FourWheelHF0Backend
SourceOnlyRoleFixtureDynamicsSpec
```

Required columns:

```text
interface_component
source_path
actor_visible
diagnostic_only
allowed_for_actor
hidden_or_oracle_risk
materialization_status
next_gate
forbidden_interpretation
```

The HF0 map is interface preparation. It does not install Chrono, import
external high-fidelity packages, or claim high-fidelity validation readiness.

## HF0 Stage Plan

M2541 should preserve the post-M2470 Route C staging:

```text
HF0:
  interface design and source-only boundary mapping

HF1:
  P0 parity smoke

HF2:
  scenario taxonomy mapping

HF3:
  low-cost pilot

HF4:
  discrepancy report
```

The immediate M2541 materialization is HF0 only. It should not run HF1-HF4.

## Materialization Gate Plan

M2541 should write `materialization_gate_plan.md` with pass/fail rules:

```text
Pass only if:
  all required files are written
  baseline checkpoint paths exist
  actor contract snapshot preserves 72/3 no-oracle boundary
  artifact map source paths exist or missing paths are explicitly classified
  HF0 boundary map keeps hidden diagnostics outside actor-visible fields
  no ranking/winner/success-rate/promotion/performance claim is emitted

Fail or route to artifact repair if:
  actor contract mismatch is detected
  checkpoint lineage is missing
  HF0 boundary would expose hidden/oracle fields to ActorView
  materialization tries to continue protected-row repair
  external simulator installation or execution is required
```

## M2541 Required Artifacts

M2541 should create:

```text
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/summary.json
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/baseline_checkpoint_list.csv
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.md
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/route_a_artifact_map.csv
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/known_failure_taxonomy_extension.csv
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/scenario_role_metric_report_plan.csv
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_boundary_map.csv
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_contract.md
runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/materialization_gate_plan.md
```

## Follow-Up Route

M2540 routes to:

```text
m2541-engineering-controller-route-a-baseline-and-interface-materialization-preflight
```

M2541 should be materialization only. It should not run new policy action,
training, replay, PPO, controller ranking, winner selection, checkpoint
promotion, success-rate verdict, validation, or high-fidelity simulation.
