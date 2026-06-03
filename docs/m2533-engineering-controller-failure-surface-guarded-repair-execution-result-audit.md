# M2533 Engineering Controller Failure-Surface Guarded Repair Execution Result Audit

- status: completed
- decision: `accept_partial_guarded_repair_evidence_route_to_mitigation_regression_localization`
- manifest: `experiments/manifests/m2533-engineering-controller-failure-surface-guarded-repair-execution-result-audit.json`
- audited summary: `runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/summary.json`
- audited training trace: `runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repair_training_trace.csv`
- audited checkpoint manifest: `runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/repaired_checkpoint_manifest.json`
- audited post-repair rows: `runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/post_repair_smoke_rows.csv`
- audited protected gate evaluation: `runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/protected_gate_evaluation.csv`
- audited candidate snapshot: `runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/candidate_config_snapshot.json`
- next milestone: `m2534-engineering-controller-failure-surface-mitigation-regression-localization-preflight`
- external high-fidelity simulation installed/imported/executed in M2533: `false`
- new policy action/environment step/training/replay/PPO in M2533: `false`
- ranking/winner/promotion/success-rate/validation/performance/paper/FW-vs-GRU/self-ID/current-sim/high-fidelity verdict claims: `false`

## Audit Decision

M2533 accepts M2532 as valid partial guarded repair evidence:

```text
status_pass: true
result_class: engineering_controller_failure_surface_guarded_repair_execution_pass
post_repair_outcome_class: post_repair_partial_or_negative_proof_recorded
```

`status_pass` means the guarded repair execution ran, wrote traceable artifacts,
and preserved the required boundaries. It does not mean all protected proof
gates passed.

M2532 is not another config-only or no-update artifact. The repaired checkpoint
was written under the M2532 run directory and changed actor behavior:

```text
source checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

repaired checkpoint:
  runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt

checkpoint_behavior_changed: true
repair_training_started: true
repaired_checkpoint_written: true
checkpoint_promoted: false
```

The audit rejects any promotion, generalization, ranking, success-rate, or
driver-performance interpretation because one protected proof gate still fails.

## Gate Findings

M2532 evaluated `7` protected gates over `45` matched post-repair rows.

Passed gates:

```text
contract_p0_72_3
no_oracle_actor_inputs
road_boundary_proof
command_conflict_proof
no_ranking_no_success_rate
```

Failed proof gate:

```text
mitigation_proof
```

Deferred gate:

```text
fresh_seed_generalization
```

Protected proof result:

```text
protected_proof_gate_pass_count: 2
protected_proof_gate_fail_count: 1
protected_proof_gates_all_passed: false
```

The result is partial proof, not failure repetition of the same three proof
gates from M2529. Road-boundary and command-conflict surfaces improved; the
remaining blocker is mitigation severity on one primary protected row.

## Row-Level Mitigation Evidence

Road-boundary primary rows:

```text
bound rows: 10
improved rows: 10
regressed rows: 0
gate_pass: true
```

Command-conflict primary rows:

```text
bound rows: 15
improved rows: 15
regressed rows: 0
gate_pass: true
```

Mitigation primary rows:

```text
bound rows: 5
improved rows: 4
regressed rows: 1
gate_pass: false
failure_type: behavior_regression
```

The regressed row is:

```text
source_row_id: m2523_m1154_policy_actor_unavoidable_mitigation_seed_254302
seed: 254302
scenario_role: unavoidable_mitigation
road_margin_delta_m: +4.456761035401987
severity_delta: +0.674427724901157
current_severity_proxy: 3.591680386980394
post_repair_severity_proxy: 4.266108111881551
collision_regressed: false
```

This row improved road margin but regressed mitigation severity. That is
`proof_washout`: one intervention surface improved while another protected
surface remained unsafe for claim escalation.

## Contract And Lineage Audit

The actor boundary is preserved:

```text
observation_shape: 72
action_shape: 3
actor_contract_shape_72_action_3: true
actor_input_contract_changed: false
hidden_or_oracle_actor_inputs_required: false
rule_switching_controller_modes_allowed: false
```

Lineage and rollback are preserved:

```text
source_checkpoint_hash: 86b665064e9a1d8d37851d04f39ff30b129552d3debcbf3cc55c85a37d90906b
repaired_checkpoint_hash: f176982523c21dd77668d65e5db18948b3f15914d0b11d1db0ed46172c8b7b4b
candidate_config_hash: dc72620e8cd608982ab1445dda034536fd1bb1a029eabd794cd3dcbf6b501dd0
candidate_config_mutated: false
active_config_overwritten: false
checkpoint_promoted: false
promotion_metadata_written: false
```

The repair update was bounded and traceable:

```text
update_method: deterministic_guarded_actor_head_bias_projection
training_observation_count: 15
trainable_parameter_names: actor_mean.bias[1];actor_mean.bias[2]
source_conflict_proxy: 0.023159563541412354
repaired_conflict_proxy: 0.0
mean_action_delta_l1: 0.544653058052063
finite_update: true
```

This supports the narrow claim that M2532 produced behavior-changing
source-only guarded repair evidence. It does not support validation,
deployment, or professional-driver capability claims.

## Failure Classification

Accepted failure classes:

```text
behavior_regression
proof_washout
```

Rejected failure classes for M2532:

```text
contract_violation
lineage_invalid
metric_artifact
training_instability
```

`scenario_sampling_failure` remains a risk rather than a confirmed failure
because fresh/generalization evidence is deferred until all protected proof
gates pass.

## Route Decision

M2533 routes to:

```text
m2534-engineering-controller-failure-surface-mitigation-regression-localization-preflight
```

M2534 must localize the remaining mitigation regression before another repair
attempt. It should use M2532 artifacts to identify whether the regression is a
single-seed severity tradeoff, an overly aggressive command-conflict repair, a
metric coupling artifact, or a broader mitigation objective weakness.

M2534 must not:

```text
run new policy action
train
rank controllers
select a winner
promote a checkpoint
compute success rates
claim validation or driver performance
```

Fresh/generalization remains deferred. A fresh/generalization route is allowed
only after all protected proof gates pass.
