# M2496 Engineering Controller Source-Only Role Fixture Parameterization Implementation Preflight

- status: completed
- result_class: `source_only_role_fixture_parameterization_preflight_pass`
- manifest: `experiments/manifests/m2496-engineering-controller-source-only-role-fixture-parameterization-implementation-preflight.json`
- implementation: `src/autodrift/hf0_source_only_role_fixture_parameterization.py`
- backend update: `src/autodrift/four_wheel_hf0_adapter.py`
- tests: `tests/test_hf0_source_only_role_fixture_parameterization.py`
- summary: `runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/summary.json`
- fixture parameterization rows: `runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/fixture_parameterization_rows.csv`
- reset differentiation rows: `runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight/reset_differentiation_rows.csv`
- next milestone: `m2497-engineering-controller-source-only-role-fixture-parameterization-result-audit`
- external high-fidelity simulation installed/imported/executed in M2496: `false`
- policy action/measured validation/training/replay/PPO/ranking/winner selection in M2496: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Implementation

M2496 implements the M2495 reset-only parameterization design.

The backend now supports an opt-in source-only fixture spec:

```text
SourceOnlyRoleFixtureDynamicsSpec
  fixture_id
  role_family
  initial_state
  fault_scales
  road
  obstacles
  diagnostic_tags
```

`FourWheelHF0Backend()` without a fixture spec keeps the default behavior. When
a fixture spec is supplied, only reset-time source-only dynamics change:

```text
initial_state
fault_scales
road geometry
obstacle slots
diagnostic tags
```

The deployed actor contract remains unchanged:

```text
P0 observation shape: 72
action shape: 3
policy action executed: false
```

## Run Result

Command:

```text
PYTHONPATH=src python -m autodrift.hf0_source_only_role_fixture_parameterization --output-dir runs/m2496_engineering_controller_source_only_role_fixture_parameterization_preflight
```

Summary:

```text
result_class: source_only_role_fixture_parameterization_preflight_pass
status_pass: true
backend_id: source_only_four_wheel_hf0
spec_count: 3
reset_count: 3
roles:
  stable_aes
  drift_required_recovery
  unavoidable_mitigation
all_reset_observations_shape_72: true
action_shape: 3
default_backend_behavior_checked: true
default_backend_reset_observation_shape: 72
default_backend_spec_present: false
```

Differentiation gates:

```text
unique_initial_state_digest_count: 3
unique_fault_scale_digest_count: 3
unique_obstacle_digest_count: 3
unique_road_digest_count: 3
unique_reset_observation_digest_count: 3
pairwise_reset_observation_l2_min: 0.3037872612476349
pairwise_state_digest_unique: true
pairwise_obstacle_digest_unique: true
```

Pairwise reset observation L2:

```text
stable_aes vs drift_required_recovery: 0.3110630512237549
stable_aes vs unavoidable_mitigation: 0.3037872612476349
drift_required_recovery vs unavoidable_mitigation: 0.5192615389823914
```

Actor-input leak flags:

```text
actor_input_contract_changed: false
role_labels_enter_actor_input: false
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
policy_action: false
policy_rollout_run: false
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
controller_family_verdict_computed: false
driver_performance_claim_made: false
verdict_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
```

## Fixture Specs

M2496 creates exactly three role fixture specs matching the admitted source-only
fixture catalog:

```text
hf0_four_wheel_stable_aes_fixture:
  role: stable_aes
  initial_state_digest: 785a0dfcb9bb6d23
  fault_scale_digest: 321d07846568573b
  road_digest: 216c8ec06a91f959
  obstacle_digest: bbf739d1ebe582b6
  reset_observation_digest: be74fec0227f041e

hf0_four_wheel_drift_required_recovery_fixture:
  role: drift_required_recovery
  initial_state_digest: a32a70e5e3a7dc6b
  fault_scale_digest: 762061b6cba41b96
  road_digest: c51cd137f2088eb1
  obstacle_digest: b3f871b4116a5906
  reset_observation_digest: ca4fed8c6285ef14

hf0_four_wheel_unavoidable_mitigation_fixture:
  role: unavoidable_mitigation
  initial_state_digest: bdf554a2e1501e2c
  fault_scale_digest: cab0440c28455383
  road_digest: 4c64cf1e827f7834
  obstacle_digest: fee6847f13252525
  reset_observation_digest: eff1d7f164d537cb
```

## Supported Claim

Supported:

```text
The source-only HF0 backend now has reset-only differentiated role fixtures for
stable_aes, drift_required_recovery, and unavoidable_mitigation.

The differentiated reset observations preserve the deployed 72-observation /
3-action contract and keep role labels, fixture labels, hidden diagnostics, and
oracle-like fields out of actor input.
```

This repairs the M2494 source-only fixture differentiation blocker at the
reset-preflight level.

## Rejected Interpretations

M2496 does not support:

```text
driver performance
role-specific recovery quality
success rate
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

No policy action was executed. The milestone proves fixture differentiation
infrastructure only.

## Failure Taxonomy

Resolved at reset-preflight level:

```text
scenario_sampling_failure / source_only_role_fixture_differentiation_blocker:
  resolved for reset-only source-only fixtures. Role reset observations, state
  digests, fault-scale digests, road digests, and obstacle digests are
  differentiated.
```

Controlled:

```text
contract_violation:
  controlled. P0 observation shape 72 and action shape 3 are preserved.

metric_artifact:
  controlled. M2496 does not compute success rate or role performance.

lineage_invalid:
  controlled. Summary, parameterization rows, reset differentiation rows, tests,
  and milestone docs are present.
```

Unresolved:

```text
behavior_regression:
  not assessed. No policy action or baseline comparison was run.

objective_overfit:
  medium-low. The milestone repairs a concrete blocker, but a result audit must
  decide the next route before rerunning role metric panels or claiming
  capability.
```

## Next Route

M2496 routes to:

```text
m2497-engineering-controller-source-only-role-fixture-parameterization-result-audit
```

The audit should verify the reset-only artifacts and decide whether the next
bounded step is a differentiated source-only nonverdict role metric panel rerun.
It must not claim driver performance or validation from reset-only evidence.
