# M2538 Engineering Controller Failure-Surface Mitigation-Preserving Repair Execution Result Audit

- status: completed
- decision: `accept_partial_mitigation_preserving_repair_evidence_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2538-engineering-controller-failure-surface-mitigation-preserving-repair-execution-result-audit.json`
- audited summary: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/summary.json`
- audited candidate sweep: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/repair_candidate_sweep.csv`
- audited selected trace: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/selected_repair_trace.csv`
- audited checkpoint manifest: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/repaired_checkpoint_manifest.json`
- audited post-repair rows: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/post_repair_smoke_rows.csv`
- audited protected gate evaluation: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/protected_gate_evaluation.csv`
- audited candidate snapshot: `runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/candidate_config_snapshot.json`
- next milestone: `m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis`
- external high-fidelity simulation installed/imported/executed in M2538: `false`
- new policy action/environment step/training/replay/PPO in M2538: `false`
- ranking/winner/promotion/success-rate/validation/performance/paper/FW-vs-GRU/self-ID/current-sim/high-fidelity verdict claims: `false`

## Audit Decision

M2538 accepts M2537 as traceable partial mitigation-preserving repair evidence:

```text
status_pass: true
result_class: engineering_controller_failure_surface_mitigation_preserving_repair_execution_pass
post_repair_outcome_class: mitigation_preserving_repair_retained_gates_passed_mitigation_failed
```

`status_pass` means the bounded execution ran, wrote all required artifacts,
preserved the P0 72/3 no-oracle boundary, and kept the repaired checkpoint
inside the M2537 run directory. It does not mean all protected proof gates
passed.

M2537 used the one bounded repair execution approved by M2536. It should not be
followed by another protected-row repair execution without a synthesis decision:

```text
selected_candidate_id: m2537_relax_m2532_bias_8
selected_relaxation_amount: 8.0
selection_reason:
  behavior_changed_candidate_retains_road_boundary_and_command_conflict_but_mitigation_proof_remains_failed
checkpoint_behavior_changed: true
checkpoint_promoted: false
protected_proof_gates_all_passed: false
```

The selected trace is a repair-evidence trace, not a controller-family ranking,
winner selection, success-rate verdict, or promotion decision.

## Gate Findings

M2537 evaluated `7` protected gates over `45` matched post-repair rows.

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
failed_proof_gate_ids: mitigation_proof
```

The retained gates passed:

```text
retained_road_boundary_proof_pass: true
retained_command_conflict_proof_pass: true
retained_proof_gates_all_passed: true
```

The mitigation-preserving gate failed:

```text
mitigation_preserving_proof_pass: false
mitigation_improved_row_count: 4
mitigation_regressed_row_count: 1
mitigation_primary_evaluated_row_count: 5
all_mitigation_primary_rows_considered: true
```

This is not retained-gate washout for the selected candidate. It is repeated
mitigation severity non-regression failure after the branch's one approved
mitigation-preserving execution.

## Candidate Sweep Audit

M2537 wrote `7` candidate rows:

```text
relaxation_amounts: 0, 1, 2, 4, 8, 12, 16
```

Rows `0`, `1`, `2`, and `4` preserved retained gates but did not change actor
behavior on the protected reset observations. Row `8` changed behavior and
preserved retained gates, but mitigation proof still failed. Rows `12` and `16`
changed behavior but washed out the retained command-conflict proof.

The selected candidate was therefore the least-bad behavior-changing trace
under the M2537 constraints:

```text
candidate_id: m2537_relax_m2532_bias_8
behavior_changed_from_source: true
retained_road_boundary_proof_pass: true
retained_command_conflict_proof_pass: true
mitigation_preserving_proof_pass: false
failed_proof_gate_ids: mitigation_proof
```

This selection does not imply driver quality or controller superiority. It only
records which bounded repair candidate should be audited as the M2537 repaired
checkpoint.

## Row-Level Mitigation Evidence

The repeated mitigation regression is still the same sentinel surface:

```text
m2534_regressed_seed: 254302
m2534_regressed_source_row_id:
  m2523_m1154_policy_actor_unavoidable_mitigation_seed_254302
max_mitigation_severity_delta: +0.6744265506945788
sum_positive_mitigation_severity_delta: +0.6744265506945788
min_mitigation_road_margin_delta_m: +3.0906574974841567
max_command_conflict_delta: 0.0
```

The row still improved road margin and retained command-conflict behavior, but
mitigation severity regressed. The failure class remains:

```text
behavior_regression
proof_washout
```

The audit rejects a metric-artifact explanation because the protected gate rows
trace to M2527/M2528 bindings and directly record the row-level severity
regression.

## Contract And Lineage Audit

The actor boundary remains preserved:

```text
actor_contract_id: P0_human_view_72_action_3_no_oracle
observation_shape: 72
action_shape: 3
actor_contract_shape_72_action_3: true
actor_input_contract_changed: false
hidden_or_oracle_actor_inputs_required: false
rule_switching_controller_modes_allowed: false
```

Lineage and rollback remain preserved:

```text
source_checkpoint:
  runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt
repaired_checkpoint:
  runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt
source_checkpoint_hash:
  f176982523c21dd77668d65e5db18948b3f15914d0b11d1db0ed46172c8b7b4b
repaired_checkpoint_hash:
  27ad15ca074292ac6a8973b70896340998f2826764f87818d25026c1262e3f88
candidate_config_hash:
  dc72620e8cd608982ab1445dda034536fd1bb1a029eabd794cd3dcbf6b501dd0
candidate_config_mutated: false
active_config_overwritten: false
checkpoint_promoted: false
```

M2538 did not run new policy action, train, replay, rank, promote, or compute a
success-rate verdict. It reads and audits the M2537 artifacts only.

## Failure Classification

Accepted failure classes:

```text
behavior_regression
proof_washout
```

Rejected failure classes for M2537:

```text
contract_violation
lineage_invalid
metric_artifact
training_instability
```

`scenario_sampling_failure` remains a risk rather than a direct failure because
the proof panel is public and narrow, and fresh/generalization remains deferred
until protected proof gates pass.

## Route Decision

M2538 routes to:

```text
m2539-engineering-controller-failure-surface-mitigation-preserving-repair-branch-synthesis
```

The synthesis must decide whether to pivot, stop, or route to a broader
evidence-expanding branch. It must not continue directly into another M2537-like
public protected-row repair execution.

M2539 should treat the current evidence as:

```text
1. M2532 and M2537 are real behavior-changing repair executions.
2. M2537 preserved retained road-boundary and command-conflict proof gains.
3. The mitigation proof surface remains unresolved after the one approved
   mitigation-preserving repair execution.
4. Continuing to tune this same public proof panel has elevated overfit risk.
5. The next useful movement toward a driver-like RL policy should come from
   branch synthesis/pivot, not another protected-row patch.
```

M2539 must not:

```text
run new policy action
train
rank controllers
select a winner
promote a checkpoint
compute success rates
claim validation or driver performance
```
