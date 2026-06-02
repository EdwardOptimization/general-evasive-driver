# M2414 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Measured Validation Result Audit

- status: completed
- decision: `source_linked_measured_validation_complete_offtrack_dominated_route_to_outcome_localization`
- manifest: `experiments/manifests/m2414-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-result-audit.json`
- parent implementation: `docs/m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation.md`
- parent summary: `runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json`
- rerun/measured validation/repair/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2414 accepts M2413 as a complete measured-validation artifact:

```text
result_class: current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass
episode_count: 5250
source_reset_target_count: 350
selected_checkpoint_count: 15
family_membership_row_count: 18300
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected: false
```

The measured outcome is still a driver-performance blocker:

```text
global role_success_rate: 0.06685714285714285
global collision_rate: 0.1761904761904762
global offtrack_rate: 0.7424761904761905
dominant_failure_mode: offtrack_dominated_failure
```

Outcome buckets:

```text
success_obstacle_pass: 342
collision_failure: 925
off_track_noncollision_noncompletion: 3898
max_steps_noncompletion: 46
speed_too_low_noncollision_noncompletion: 39
```

M2414 therefore accepts the artifact but does not accept a driver-success,
repair-success, paper-level, current-sim, finite-window-vs-GRU, or self-ID
claim.

## Diagnostic Slices

Profile slices are diagnostic only:

```text
L0_current_masked:
  success_rate: 0.05714285714285714
  offtrack_rate: 0.7876190476190477

L1_one_step:
  success_rate: 0.05714285714285714
  offtrack_rate: 0.7942857142857143

L2_window_25:
  success_rate: 0.05714285714285714
  offtrack_rate: 0.741904761904762

L2_window_50:
  success_rate: 0.05714285714285714
  offtrack_rate: 0.7304761904761905

L3_online_gru:
  success_rate: 0.10571428571428572
  offtrack_rate: 0.6580952380952381
```

These numbers do not rank controller families. M2413 is not the fair
finite-window-vs-GRU protocol, and the selected checkpoint set is
diagnostic-only.

Role-family slices:

```text
R0_stable_avoidable:
  success_rate: 0.057777777777777775
  offtrack_rate: 0.9344444444444444

R1_aeb_infeasible_stable_aes:
  success_rate: 0.3322222222222222
  offtrack_rate: 0.6633333333333333

R2_handling_limit_drift_capable_avoidance:
  success_rate: 0.0
  offtrack_rate: 0.83

R3_recovery_after_limit:
  success_rate: 0.0
  offtrack_rate: 0.8366666666666667

R4_unavoidable_mitigation:
  success_rate: 0.0
  collision_rate: 0.6973333333333334
  offtrack_rate: 0.3

R5_hidden_dynamics_robustness:
  success_rate: 0.0
  offtrack_rate: 0.8166666666666667
```

Family-membership slices are overlapping:

```text
c01_geometry_timing_containment:
  episode_count: 4350
  success_rate: 0.06689655172413793
  offtrack_rate: 0.7583908045977011

c02_hidden_dynamics_response_containment:
  episode_count: 4200
  success_rate: 0.06
  offtrack_rate: 0.8269047619047619

c03_general_offtrack_boundary_containment:
  episode_count: 5250
  success_rate: 0.06685714285714285
  offtrack_rate: 0.7424761904761905

c04_role_conditioned_containment:
  episode_count: 4500
  success_rate: 0.078
  offtrack_rate: 0.8162222222222222
```

They can localize source-linked failure structure, but cannot rank candidate
families or imply a family-specific repair succeeded.

## Boundary Checks

M2414 did not rerun or mutate the measured artifact:

```text
measured rerun: false
repair_execution_started: false
training_started: false
replay_started: false
ppo_used: false
active_config_overwrite_count: 0
actor_input_contract_changed: false
hidden_oracle_feature_injection: false
```

Claim-boundary checks:

```text
candidate_family_ranking_claim_made: false
controller_family_ranking_claim_made: false
support_policy_ranking_claim_made: false
winner_selected: false
paper_level_claim_made: false
finite_window_vs_gru_conclusion_made: false
level3_self_id_claim_made: false
scenario_redesign_executed_claim_made: false
training_repair_success_claim_made: false
current_sim_verdict_claim_made: false
```

## Route Decision

Decision:

```text
source_linked_measured_validation_complete_offtrack_dominated_route_to_outcome_localization
```

Next milestone:

```text
m2415-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-implementation
```

M2415 should be artifact-only. It should read the M2413 episode and
membership rows, then materialize localization slices for:

```text
reset target
role family
family membership
profile
hidden dynamics bucket
obstacle timing and lateral buckets
outcome bucket
```

It should identify high-support offtrack, collision, max-step, speed-too-low,
and R4 mitigation slices, while keeping family/profile/controller axes
diagnostic-only. It must not rerun measured validation, execute repair, train,
rank, select a winner, or make current-sim/paper/self-ID verdict claims.

## Failure Taxonomy

Observed:

```text
behavior_regression: measured outcome is offtrack-dominated
```

Not observed:

```text
scenario_sampling_failure
lineage_invalid
contract_violation
metric_artifact
objective_overfit
private_holdout_contamination
promotion_gate_failure
seed_fragility
training_instability
repair execution
training repair success
candidate/profile/controller ranking
winner selection
```

## Claim Boundary

Supported:

```text
M2413 is a complete source-linked measured-validation artifact.

The measured artifact is offtrack-dominated and should route to artifact-only
outcome localization.
```

Blocked:

```text
measured driver success
repair execution
scenario redesign executed
training repair success
candidate family ranking
support/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```
