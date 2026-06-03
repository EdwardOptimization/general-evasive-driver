# M2491 Source-Only Closed-Loop Fixture Pilot Extended Result Audit

- status: completed
- decision: `accept_extended_source_only_policy_action_execution_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2491-source-only-closed-loop-fixture-pilot-extended-result-audit.json`
- audited summary: `runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/summary.json`
- audited rows: `runs/m2490_source_only_closed_loop_fixture_pilot_extended_execution/pilot_rollout_rows.csv`
- next milestone: `m2492-source-only-closed-loop-fixture-pilot-branch-synthesis`
- external high-fidelity simulation installed/imported/executed in M2491: `false`
- new policy action/measured validation/training/replay/PPO/ranking/winner selection in M2491: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Audit Decision

M2491 accepts M2490 as a complete bounded extended source-only same-contract
policy-action execution.

Accepted summary:

```text
result_class: source_only_closed_loop_fixture_pilot_pass
status_pass: true
milestone: m2490-source-only-closed-loop-fixture-pilot-extended-execution
backend_id: source_only_four_wheel_hf0
checkpoint_admitted: true
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
fixture_count: 3
reset_count: 3
step_count: 300
expected_step_count: 300
horizon_steps_per_fixture: 100
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
row_count: 300
role_counts:
  stable_aes: 100
  drift_required_recovery: 100
  unavoidable_mitigation: 100
observation_shape counts:
  72: 300
action_shape counts:
  3: 300
action_finite:
  true: 300
action_within_bounds:
  true: 300
backend_status:
  running: 300
terminated_by_backend:
  false: 300
truncated_by_backend:
  false: 300
diagnostic_wheel_force_count:
  4: 300
policy_action:
  true: 300
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
M2490 proves the admitted 72-observation / 3-action recurrent actor can execute
bounded deterministic policy actions through the three admitted source-only HF0
fixtures for 100 steps per fixture without actor-input leakage or backend path
failure.
```

This is source-only closed-loop execution evidence. It is stronger than M2488
because it extends the horizon from 20 to 100 steps per fixture.

## Rejected Interpretations

M2490/M2491 do not support:

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
high-fidelity simulator. No success metric or performance verdict was computed.

## Failure Taxonomy

Observed:

```text
none for the M2490 extended execution gates
```

Controlled:

```text
contract_violation:
  controlled. Checkpoint admission and all reset/step observations/actions pass
  72/3 shape gates.

lineage_invalid:
  controlled. M2490 summary has the correct milestone id and cites the accepted
  checkpoint plus M2489 audit route.

metric_artifact:
  controlled for this audit. The audit keeps M2490 as source-only execution
  evidence and rejects success-rate or driver-performance interpretation.

scenario_sampling_failure:
  not addressed. The pilot covers three admitted source-only fixtures and does
  not repair current-sim stable-AES readiness.

behavior_regression:
  not assessed. No baseline comparison or regression gate is run.

objective_overfit:
  medium-low. The branch produced real closed-loop rows, but further source-only
  extension should synthesize before it becomes another local loop.
```

## Route Decision

M2491 routes to branch synthesis:

```text
m2492-source-only-closed-loop-fixture-pilot-branch-synthesis
```

Rationale:

```text
The source-only branch now has design, path-smoke execution, audit, extended
execution, and audit. Continuing directly to another horizon extension risks
turning source-only execution into the new local loop.

The next milestone should synthesize M2487-M2491 and choose whether to continue
source-only execution, pivot to engineering-controller evidence, return to
external high-fidelity backend work, or bridge to paper-route comparisons.
```

M2492 must preserve the claim boundary: source-only execution rows are useful
closed-loop evidence, but they are not high-fidelity validation, paper evidence,
or driver-performance proof.
