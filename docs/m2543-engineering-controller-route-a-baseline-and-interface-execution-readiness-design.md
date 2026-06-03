# M2543 Engineering Controller Route A Baseline And Interface Execution Readiness Design

- status: completed
- decision: `route_to_route_a_baseline_source_only_execution_readiness_panel_preflight`
- manifest: `experiments/manifests/m2543-engineering-controller-route-a-baseline-and-interface-execution-readiness-design.json`
- design artifact: `docs/m2543-engineering-controller-route-a-baseline-and-interface-execution-readiness-design.md`
- parent audit: `docs/m2542-engineering-controller-route-a-baseline-and-interface-materialization-result-audit.md`
- next milestone: `m2544-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-preflight`
- external high-fidelity simulation installed/imported/executed in M2543: `false`
- environment rollout/simulator step/policy rollout/new policy action in M2543: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2543: `false`
- success-rate/performance/paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Decision

M2542 accepted the Route A baseline and HF0 interface materialization. M2543
turns that accepted materialization into the first bounded evidence-producing
step in the post-pivot branch:

```text
M2544 source-only Route A execution-readiness panel
```

The next step should not be another static materialization or audit. It should
run a bounded source-only panel that exercises the three diagnostic policy
checkpoints from the accepted baseline list, under the already accepted P0
actor/HF0 boundary and fresh-seed measured behavior protocol.

Allowed claim scope for M2544:

```text
source-only Route A baseline execution-readiness panel preflight only
```

Forbidden M2544 interpretations:

```text
driver performance
deployment readiness
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
validation readiness
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
current-sim or high-fidelity validation verdict
```

## Subject Matrix

M2544 should compare five diagnostic subjects:

```text
m1154_original_policy:
  checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
  action source: recurrent actor policy
  allowed use: historical diagnostic baseline
  promotion status: not promoted by M2544

m2532_guarded_repair_policy:
  checkpoint: runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt
  action source: recurrent actor policy
  allowed use: behavior-changing diagnostic repair candidate
  promotion status: not promoted

m2537_mitigation_preserving_policy:
  checkpoint: runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt
  action source: recurrent actor policy
  allowed use: behavior-changing retained-gate diagnostic repair candidate
  promotion status: not promoted

coast_open_loop:
  normalized action: [0.0, -1.0, -1.0]
  physical control: steer 0.0, throttle 0.0, brake 0.0
  actor observation: not used for action selection
  allowed use: actuator-interface reference only

straight_full_brake_open_loop:
  normalized action: [0.0, -1.0, 1.0]
  physical control: steer 0.0, throttle 0.0, brake 1.0
  actor observation: not used for action selection
  allowed use: mitigation reference only
```

The policy checkpoint subjects are diagnostic siblings, not ranked
competitors. M2544 must not choose a winner.

## Role And Seed Denominator

M2544 should reuse the M2523 fresh-seed source-only measured behavior protocol
and the deterministic role fixture perturbation machinery:

```text
role families:
  stable_aes
  drift_required_recovery
  unavoidable_mitigation

seed count per role:
  5

horizon steps per subject-role-seed:
  100
```

Expected denominator:

```text
subjects: 5
roles: 3
seeds per role: 5
expected subject-role-seed rows: 75
expected telemetry rows: 7500
expected seed panel rows: 15
expected metric completeness rows: 40
```

Every attempted subject-role-seed row must be retained, or a denominator gap
must be written explicitly. The panel should fail closed if a checkpoint cannot
be admitted, a row is silently dropped, a metric registry row is unsupported,
or actor contract checks fail.

## Actor And HF0 Contract

M2544 must preserve the accepted P0/HF0 boundary:

```text
actor_contract_id: P0_human_view_72_action_3_no_oracle
observation_shape: 72
action_shape: 3
actor_encoder: human_view_online_gru
action_sequence_horizon: 1
deployed action: [steer_command, throttle_command, brake_command]
```

Allowed actor-visible input families remain:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent/history state
```

Forbidden actor input or policy-side features remain:

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

Diagnostics may contain hidden dynamics and outcome events for evaluator-side
rows only. `ActorView`, `P0ObservationExtractor`, and policy checkpoints must
not consume those fields.

## Required M2544 Artifacts

M2544 must write:

```text
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/summary.json
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/seed_panel_spec.csv
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/subject_registry.csv
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/telemetry_rows.csv
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/measured_behavior_rows.csv
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/measured_event_rows.csv
runs/m2544_engineering_controller_route_a_baseline_source_only_execution_readiness_panel/metric_completeness_rows.csv
docs/m2544-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-preflight.md
```

Implementation should reuse the existing source-only components where
possible:

```text
build_seed_panel_specs from M2523
engineering_controller_behavior_outcome_v0 row schema
M2514 metric registry
FourWheelHF0Backend
P0ObservationExtractor
admit_actor_checkpoint
_event_stats and measured behavior row helpers
```

The only meaningful extension is the subject registry: it must admit three
policy checkpoints instead of the single M1154 checkpoint used by M2523.

## Pass Gates

M2544 `status_pass` should require:

```text
all three policy checkpoints admitted under P0 72/3
all required artifacts present
subject registry row count == 5
seed panel row count == 15
measured behavior row count == 75
measured event row count == 75
metric completeness row count == 40
telemetry row count == 7500
role seed subject matrix complete
all attempted rows retained
denominator_gap_count == 0
all reset/step observations shape 72
all actions shape 3, finite, and within deployed bounds
all backend statuses running
seed lineage explicit
straight_full_brake_open_loop mitigation reference explicit per role and seed
all actor-input leak flags false
all rows diagnostic-only and source-only
ranking/winner/success-rate/promotion/verdict flags false
```

M2544 should record outcome events and metric completeness, but it must not
turn them into a ranking, success-rate, or driver-performance verdict.

## Failure Routes

M2544 should route failures as follows:

```text
checkpoint admission failure -> artifact or checkpoint compatibility repair
actor contract mismatch -> contract repair
hidden/oracle leak -> boundary repair
denominator gap or missing subject-role-seed row -> panel instrumentation repair
metric completeness gap -> metric artifact repair
same public protected-row repair pressure -> branch synthesis
complete diagnostic panel -> M2545 result audit
```

If M2544 cannot be implemented without changing actor inputs or ranking the
subjects, it must fail and route to synthesis rather than weakening the
contract.

## Next Route

M2543 registers:

```text
m2544-engineering-controller-route-a-baseline-source-only-execution-readiness-panel-preflight
```

M2544 should be the first evidence-producing milestone after the M2539/M2540
Route A/HF0 pivot. It is still only source-only execution-readiness evidence,
but it moves the branch from accepted materialization to a concrete
subject-role-seed panel.
