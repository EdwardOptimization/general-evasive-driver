# M2488 Source-Only Closed-Loop Fixture Pilot Implementation Preflight

- status: completed
- result_class: `source_only_closed_loop_fixture_pilot_pass`
- manifest: `experiments/manifests/m2488-source-only-closed-loop-fixture-pilot-implementation-preflight.json`
- implementation: `src/autodrift/hf0_source_only_closed_loop_fixture_pilot.py`
- focused tests: `tests/test_hf0_source_only_closed_loop_fixture_pilot.py`
- summary: `runs/m2488_source_only_closed_loop_fixture_pilot_preflight/summary.json`
- rollout rows: `runs/m2488_source_only_closed_loop_fixture_pilot_preflight/pilot_rollout_rows.csv`
- next milestone: `m2489-source-only-closed-loop-fixture-pilot-result-audit`
- external high-fidelity simulation installed/imported/executed in M2488: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2488: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.hf0_source_only_closed_loop_fixture_pilot --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --output-dir runs/m2488_source_only_closed_loop_fixture_pilot_preflight --horizon-steps 20
```

## Result

M2488 implemented and ran the bounded source-only closed-loop fixture pilot
preflight registered by M2487.

Accepted result:

```text
result_class: source_only_closed_loop_fixture_pilot_pass
status_pass: true
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
step_count: 60
expected_step_count: 60
horizon_steps_per_fixture: 20
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
stable_aes: 20 policy-action steps
drift_required_recovery: 20 policy-action steps
unavoidable_mitigation: 20 policy-action steps
```

Contract/leak flags:

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
A same-contract 72-observation / 3-action deployable actor can execute bounded
deterministic policy actions through the three admitted source-only HF0 fixtures
without actor-input leakage.
```

This is the first source-only policy-action path smoke after the HF0 interface
branch. It is stronger than M2484 because actions come from an admitted actor
checkpoint rather than canned smoke sequences.

## Rejected Interpretations

M2488 does not support:

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

The run used the source-only `FourWheelHF0Backend`, not an external
high-fidelity simulator. The pilot rows are bounded path-smoke evidence, not a
validation benchmark.

## Route Decision

M2488 routes to result audit:

```text
m2489-source-only-closed-loop-fixture-pilot-result-audit
```

The audit should verify the summary and rollout rows before any longer pilot,
repair, measured validation, controller comparison, or paper-route connection.
