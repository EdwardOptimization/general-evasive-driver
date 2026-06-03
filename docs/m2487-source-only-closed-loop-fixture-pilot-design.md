# M2487 Source-Only Closed-Loop Fixture Pilot Design

- status: completed
- decision: `source_only_closed_loop_fixture_pilot_design_route_to_implementation_preflight`
- manifest: `experiments/manifests/m2487-source-only-closed-loop-fixture-pilot-design.json`
- design artifact: `docs/m2487-source-only-closed-loop-fixture-pilot-design.md`
- parent synthesis: `docs/m2486-high-fidelity-interface-preparation-post-smoke-branch-synthesis.md`
- next milestone: `m2488-source-only-closed-loop-fixture-pilot-implementation-preflight`
- external high-fidelity simulation installed/imported/executed in M2487: `false`
- measured validation/policy action/policy rollout/training/replay/PPO/ranking/winner selection in M2487: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2486 closed the HF0 interface preparation branch as ready-enough
infrastructure. M2487 defines the first bounded step back toward closed-loop
policy-action evidence without weakening the actor/action contract.

M2487 is design only. It does not load a checkpoint, execute policy action,
step a rollout, train, rank, select a winner, or make a performance verdict.

## Pilot Scope

The implementation preflight should cover exactly the three source-only
fixtures admitted by M2482 and smoked by M2484:

```text
hf0_four_wheel_stable_aes_fixture
hf0_four_wheel_drift_required_recovery_fixture
hf0_four_wheel_unavoidable_mitigation_fixture
```

Surface:

```text
source_only_four_wheel_hf0
```

Backend:

```text
autodrift.four_wheel_hf0_adapter.FourWheelHF0Backend
```

Observation extraction:

```text
autodrift.high_fidelity_interface.P0ObservationExtractor
```

Required actor-visible contract:

```text
observation shape: 72
action shape: 3
action meaning: [steer_command, throttle_command, brake_command]
```

## Actor Source

Default admission candidate for M2488:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

M2487 only records this as an admission candidate. M2488 must verify it before
executing any policy action.

M2488 admission rule:

```text
load function:
  autodrift.checkpoints.load_actor_critic_checkpoint

device:
  cpu

required model contract:
  model.obs_dim == 72
  model.act_dim == 3
  actor_encoder in {human_view_online_gru, response_critical_online_gru}
  action_sequence_horizon == 1

action rule:
  deterministic actor action only
  use tanh-squashed action returned by the model
  validate through validate_actor_action before backend.step

hidden-state rule:
  reset recurrent hidden state once per fixture episode
  carry hidden state across steps inside that fixture episode
  do not reset hidden state every step unless a separate ablation is
  pre-registered
```

If the checkpoint cannot load or fails the contract, M2488 must stop as a
contract/admission blocker and route to actor-source inventory. It must not
change actor inputs or substitute hidden diagnostics to make the pilot run.

## Closed-Loop Protocol

For each admitted fixture:

```text
1. create a fresh FourWheelHF0Backend
2. reset with BackendResetRequest:
     seed: 2488 + fixture_index
     scenario_spec_id: fixture_id
     role_family: role_family
3. extract P0 observation from reset actor_view
4. reset policy hidden state for this fixture
5. for horizon_steps = 20:
     action = deterministic actor action(observation, hidden)
     action = validate_actor_action(action)
     step_result = backend.step(action)
     next_observation = P0ObservationExtractor.extract(step_result.actor_view)
     carry next hidden state
     record one row
6. close backend
```

M2488 should run only this bounded pilot. It should not train, replay, tune,
rank controller families, select a winner, promote a checkpoint, or compare
against other controller families.

## Leak Checks

The implementation summary must report these flags, all expected `false`:

```text
fixture_labels_enter_actor_input
scenario_labels_enter_actor_input
feasibility_classes_enter_actor_input
hidden_values_enter_actor_input
oracle_labels_enter_actor_input
diagnostics_available_to_actor
reward_terms_enter_actor_input
success_labels_enter_actor_input
ttc_enter_actor_input
required_clearance_enter_actor_input
```

Allowed diagnostics in output rows:

```text
backend_id
fixture_id
role_family
backend_status
terminated_by_backend
truncated_by_backend
diagnostic_wheel_force_count
physical_control
state summary fields
```

Those diagnostics are never actor inputs.

## Metrics

M2488 summary should report:

```text
result_class
status_pass
checkpoint_path
checkpoint_admitted
fixture_count
reset_count
step_count
horizon_steps_per_fixture
policy_action: true
policy_rollout_run: true
training_run: false
ranking_run: false
winner_selected: false
verdict_claim_made: false
observation_shape
action_shape
all_reset_observations_shape_72
all_step_observations_shape_72
all_action_shapes_3
all_actions_finite
all_actions_within_bounds
all_backend_statuses_running
diagnostic_wheel_force_counts
leak flags
```

Per-step rows should include:

```text
fixture_id
role_family
step_index
observation_shape
action_steer
action_throttle
action_brake
action_finite
action_within_bounds
backend_status
terminated_by_backend
truncated_by_backend
diagnostic_wheel_force_count
```

Do not compute success rate, rank score, paper metric, finite-window-vs-GRU
metric, or self-ID metric in M2488.

## Pass/Fail Rule

M2488 passes only if:

```text
the checkpoint loads and satisfies the 72/3 same-contract admission rule
all three admitted source-only fixtures reset
each fixture completes 20 deterministic policy-action steps
all reset and step observations have shape 72
all actions have shape 3, are finite, and are within [-1, 1]
wheel-force diagnostics are present in output only and count 4 when available
all actor-input leak flags are false
no external high-fidelity simulator is installed, imported, or run
no training, replay, PPO, ranking, winner selection, promotion, or verdict claim occurs
```

Failure routes:

```text
checkpoint admission failure:
  route to actor-source inventory

actor/action contract violation:
  route to pilot implementation repair

nonfinite or out-of-bound action:
  route to policy-action adapter repair

backend reset/step failure:
  route to source-only fixture/backend repair

leak flag true:
  stop and repair actor-input boundary before any further pilot work
```

## Claim Boundary

Allowed claim after a passing M2488:

```text
A same-contract deployable actor can execute bounded deterministic policy
actions through the source-only HF0 fixture pilot without actor-input leakage.
```

Forbidden claims after M2488:

```text
driver performance
controller-family ranking
winner selection
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

M2488 is the first policy-action path smoke on this source-only branch, not a
validation or performance benchmark.
