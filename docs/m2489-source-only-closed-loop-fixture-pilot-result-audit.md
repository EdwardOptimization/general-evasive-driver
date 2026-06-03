# M2489 Source-Only Closed-Loop Fixture Pilot Result Audit

- status: completed
- decision: `accept_source_only_policy_action_path_smoke_route_to_extended_execution`
- manifest: `experiments/manifests/m2489-source-only-closed-loop-fixture-pilot-result-audit.json`
- audited summary: `runs/m2488_source_only_closed_loop_fixture_pilot_preflight/summary.json`
- audited rows: `runs/m2488_source_only_closed_loop_fixture_pilot_preflight/pilot_rollout_rows.csv`
- next milestone: `m2490-source-only-closed-loop-fixture-pilot-extended-execution`
- external high-fidelity simulation installed/imported/executed in M2489: `false`
- new policy action/measured validation/training/replay/PPO/ranking/winner selection in M2489: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Audit Decision

M2489 accepts M2488 as a complete bounded source-only same-contract
policy-action path smoke.

Accepted summary:

```text
result_class: source_only_closed_loop_fixture_pilot_pass
status_pass: true
backend_id: source_only_four_wheel_hf0
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
fixture_count: 3
reset_count: 3
step_count: 60
expected_step_count: 60
horizon_steps_per_fixture: 20
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

CSV row audit:

```text
row_count: 60
role_counts:
  stable_aes: 20
  drift_required_recovery: 20
  unavoidable_mitigation: 20
observation_shape counts:
  72: 60
action_shape counts:
  3: 60
action_finite:
  true: 60
action_within_bounds:
  true: 60
backend_status:
  running: 60
terminated_by_backend:
  false: 60
truncated_by_backend:
  false: 60
diagnostic_wheel_force_count:
  4: 60
policy_action:
  true: 60
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
M2488 proves the repository can load an admitted same-contract actor checkpoint
and run deterministic policy actions through the three admitted source-only HF0
fixtures for a bounded 20-step horizon without actor-input leakage.
```

This is real closed-loop policy-action evidence at the path-smoke level.

## Rejected Interpretations

M2488/M2489 do not support:

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

The pilot used the source-only `FourWheelHF0Backend`. It did not run an
external high-fidelity simulator and did not compute success or performance
metrics.

## Failure Taxonomy

Observed:

```text
none for the M2488 path-smoke gates
```

Controlled:

```text
contract_violation:
  controlled. Checkpoint admission and all reset/step observations/actions pass
  72/3 shape gates.

lineage_invalid:
  controlled. M2488 artifacts cite M2487/M2486 parent evidence and the selected
  checkpoint path.

metric_artifact:
  controlled for this milestone. The audit keeps M2488 as path-smoke evidence
  and rejects success-rate or driver-performance interpretation.

scenario_sampling_failure:
  not addressed. The pilot covers the three admitted source-only fixtures only
  and does not repair current-sim stable-AES readiness.

behavior_regression:
  not assessed. No baseline comparison or regression gate is run.

objective_overfit:
  lower than the HF0 interface loop because M2488 produced closed-loop policy
  action rows, but follow-up must remain bounded and avoid verdict overclaim.
```

## Route Decision

M2489 routes to a bounded extended source-only pilot execution:

```text
m2490-source-only-closed-loop-fixture-pilot-extended-execution
```

Rationale:

```text
M2488 is accepted as a path-smoke milestone, but it is only 20 steps per
fixture. The next useful evidence is a longer bounded execution over the same
three source-only fixtures using the same actor admission and leak gates.

The next step should still avoid success-rate, ranking, winner, promotion,
high-fidelity validation, paper, finite-window-vs-GRU, and self-ID claims.
```

M2490 should use the existing M2488 implementation with a longer registered
horizon, write new summary/row artifacts, and remain evaluation-only.
