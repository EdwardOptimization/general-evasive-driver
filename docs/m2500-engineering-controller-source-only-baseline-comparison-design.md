# M2500 Engineering Controller Source-Only Baseline Comparison Design

- status: completed
- decision: `source_only_baseline_comparison_design_route_to_implementation_preflight`
- manifest: `experiments/manifests/m2500-engineering-controller-source-only-baseline-comparison-design.json`
- parent audit: `docs/m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit.md`
- route constraint: `docs/post-m2470-route-plan.md`
- next milestone: `m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight`
- external high-fidelity simulation installed/imported/executed in M2500: `false`
- policy action/measured validation/training/replay/PPO/ranking/winner selection in M2500: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Design Problem

M2499 accepts M2498 as diagnostic source-only role telemetry, not as driver
performance. The next useful engineering artifact is a comparison protocol that
can put the admitted checkpoint telemetry beside simple action baselines without
turning the result into a success rate, ranking, winner selection, validation
claim, or paper claim.

M2500 designs that protocol before implementation:

```text
compare bounded source-only trajectory and actuator envelopes across the
parameterized role fixtures under identical reset specs, while preserving the
P0 actor/action contract and keeping the result diagnostic-only.
```

## Comparison Subjects

M2501 should compare exactly three subjects:

```text
m1154_policy_actor:
  source: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
  action source: recurrent actor policy
  actor observation: P0 72-vector only
  action shape: 3
  policy_action: true

coast_open_loop:
  source: fixed deployed action vector
  normalized action: [0.0, -1.0, -1.0]
  physical control: steer 0.0, throttle 0.0, brake 0.0
  actor observation: not used for action selection
  action shape: 3
  policy_action: false

straight_full_brake_open_loop:
  source: fixed deployed action vector
  normalized action: [0.0, -1.0, 1.0]
  physical control: steer 0.0, throttle 0.0, brake 1.0
  actor observation: not used for action selection
  action shape: 3
  policy_action: false
```

The open-loop baselines use the same deployed normalized action interface as
the actor. They are engineering references, not controller-family competitors.
M2501 must not select a winner.

## Fixture And Horizon Contract

M2501 should reuse the M2496 parameterized source-only role fixture specs:

```text
stable_aes
drift_required_recovery
unavoidable_mitigation
```

Protocol:

```text
fixtures: 3
comparison subjects: 3
horizon_steps_per_fixture_subject: 100
expected telemetry rows: 900
expected role-controller panel rows: 9
external high-fidelity simulation: false
measured validation: false
training/replay/PPO: false
ranking/winner/success-rate: false
```

Each subject must reset the same role fixture spec independently. Reset
observation digests should satisfy both checks:

```text
within each role:
  reset_observation_digest is identical across comparison subjects

across roles:
  reset_observation_digest is differentiated across stable_aes,
  drift_required_recovery, and unavoidable_mitigation
```

## Telemetry Fields

M2501 should extend the M2498 role telemetry shape with comparison subject
identity:

```text
comparison_subject
comparison_subject_family
fixture_id
surface_id
role_family
step_index
observation_shape
action_shape
action_steer
action_throttle
action_brake
action_finite
action_within_bounds
action_saturated
backend_status
terminated_by_backend
truncated_by_backend
diagnostic_wheel_force_count
state_x
state_y
state_psi
state_vx
state_vy
state_speed
state_yaw_rate
physical_steer
physical_throttle
physical_brake
parameterized_fixture
reset_observation_digest
policy_action
diagnostic_only
```

No field may contain success labels, reward terms, TTC, required clearance,
feasibility labels, hidden fault scales, oracle labels, or controller ranking.

## Panel Metrics

Allowed nonverdict per-role/per-subject panel metrics:

```text
fixture_count
step_count
backend_alive_fraction
finite_action_fraction
bounded_action_fraction
saturated_action_fraction
observation_shape_72_fraction
action_shape_3_fraction
wheel_count_4_fraction
terminated_fraction
truncated_fraction
speed_min
speed_max
speed_mean
y_min
y_max
abs_y_max
yaw_rate_min
yaw_rate_max
abs_yaw_rate_max
steer_min
steer_max
throttle_min
throttle_max
brake_min
brake_max
diagnostic_only
success_rate_computed
verdict_claim_made
```

Allowed aggregate summary fields:

```text
comparison_subject_count
role_count
telemetry_row_count
role_subject_panel_row_count
all_reset_observations_shape_72
all_step_observations_shape_72
all_action_shapes_3
all_actions_finite
all_actions_within_bounds
all_backend_statuses_running
all_diagnostic_wheel_force_counts_4
role_reset_digests_differentiated
role_reset_digests_match_across_subjects
panel_rows_are_diagnostic_only
success_rate_computed: false
controller_family_verdict_computed: false
ranking_run: false
winner_selected: false
```

Forbidden fields:

```text
success
collision success/failure
clearance pass/fail
required clearance
TTC
reward
score
rank
winner
promotion decision
driver performance verdict
controller-family verdict
paper verdict
finite-window-vs-GRU verdict
self-ID verdict
high-fidelity validation verdict
```

## Implementation Preflight

M2501 should add a bounded implementation preflight with artifacts:

```text
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv
docs/m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight.md
```

Expected command shape:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.hf0_source_only_baseline_comparison_panel --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --output-dir runs/m2501_engineering_controller_source_only_baseline_comparison_preflight --horizon-steps 100 --milestone m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight --next-blocker m2502-engineering-controller-source-only-baseline-comparison-result-audit
```

Implementation tests should cover:

```text
comparison subject definitions and physical-control mapping
three role fixtures times three subjects
900 telemetry rows for horizon 100
9 panel rows
reset digest match within role across subjects
reset digest differentiation across roles
observation shape 72 and action shape 3
finite and bounded actions
diagnostic-only rows
no success-rate verdict ranking winner or promotion fields
```

## Supported Claim

Supported:

```text
M2500 defines a bounded source-only baseline comparison protocol that can be
implemented without changing actor inputs, training, ranking controllers,
selecting a winner, computing success rates, or claiming driver performance.
```

## Rejected Interpretations

M2500 does not support:

```text
driver performance
role-specific success or recovery quality
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

## Route Decision

M2500 routes to:

```text
m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight
```

M2501 may execute bounded source-only actions only to write diagnostic
comparison telemetry and panel artifacts under the protocol above. It must not
train, rank controllers, select a winner, compute success rates, promote a
checkpoint, or claim driver performance.
