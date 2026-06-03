# M2490 Source-Only Closed-Loop Fixture Pilot Extended Execution

- status: completed
- result_class: `source_only_closed_loop_fixture_pilot_pass`
- manifest: `experiments/manifests/m2490-source-only-closed-loop-fixture-pilot-extended-execution.json`
- implementation: `src/autodrift/hf0_source_only_closed_loop_fixture_pilot.py`
- focused tests: `tests/test_hf0_source_only_closed_loop_fixture_pilot.py`
- summary: `runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/summary.json`
- rollout rows: `runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/pilot_rollout_rows.csv`
- next milestone: `m2491-source-only-closed-loop-fixture-pilot-extended-result-audit`
- external high-fidelity simulation installed/imported/executed in M2490: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2490: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.hf0_source_only_closed_loop_fixture_pilot --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --output-dir runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution --horizon-steps 100 --milestone m2490-source-only-closed-loop-fixture-pilot-extended-execution --next-blocker m2491-source-only-closed-loop-fixture-pilot-extended-result-audit
```

## Result

M2490 extends the accepted M2488 path-smoke from 20 to 100 deterministic
policy-action steps per admitted source-only fixture.

Accepted result:

```text
result_class: source_only_closed_loop_fixture_pilot_pass
status_pass: true
milestone: m2490-source-only-closed-loop-fixture-pilot-extended-execution
backend_id: source_only_four_wheel_hf0
checkpoint_path: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
checkpoint_admitted: true
checkpoint_admission_reason: admitted
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
fixture_count: 3
reset_count: 3
step_count: 300
expected_step_count: 300
horizon_steps_per_fixture: 100
observation_shape: 72
action_shape: 3
all_reset_observations_shape_72: true
all_step_observations_shape_72: true
all_action_shapes_3: true
all_actions_finite: true
all_actions_within_bounds: true
all_backend_statuses_running: true
all_diagnostic_wheel_force_counts_4: true
policy_action: true
policy_rollout_run: true
```

Fixture coverage:

```text
stable_aes: 100 policy-action steps
drift_required_recovery: 100 policy-action steps
unavoidable_mitigation: 100 policy-action steps
```

CSV row audit snapshot:

```text
rows: 300
observation_shape 72: 300
action_shape 3: 300
action_within_bounds true: 300
backend_status running: 300
diagnostic_wheel_force_count 4: 300
```

Actor-input leak flags:

```text
fixture_labels_enter_actor_input: false
scenario_labels_enter_actor_input: false
feasibility_classes_enter_actor_input: false
hidden_values_enter_actor_input: false
oracle_labels_enter_actor_input: false
diagnostics_available_to_actor: false
reward_terms_enter_actor_input: false
success_labels_enter_actor_input: false
ttc_enter_actor_input: false
required_clearance_enter_actor_input: false
```

Blocked execution/claim flags:

```text
external_high_fidelity_imported: false
high_fidelity_simulation_run: false
measured_validation_run: false
training_run: false
replay_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
verdict_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
```

## Supported Claim

Supported:

```text
The same admitted 72-observation / 3-action recurrent actor can execute bounded
deterministic policy actions through the three admitted source-only HF0 fixtures
for 100 steps per fixture without actor-input leakage or backend path failure.
```

This expands source-only closed-loop evidence beyond path smoke while staying
within source-only evaluation scope.

## Rejected Interpretations

M2490 does not support:

```text
driver performance
success-rate improvement
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

M2490 intentionally does not compute success rate or a controller-family
verdict. It uses the source-only `FourWheelHF0Backend`, not an external
high-fidelity simulator.

## Route Decision

M2490 routes to result audit:

```text
m2491-source-only-closed-loop-fixture-pilot-extended-result-audit
```

The audit should verify the 300-row artifact and decide whether the next route
is repair, another bounded source-only extension, or synthesis before reconnecting
to engineering/paper/high-fidelity routes.
