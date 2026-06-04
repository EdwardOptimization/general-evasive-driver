# M2660 Engineering Controller Route A Baseline Evidence Index After Target/Protected Report Refresh Materialization Result Audit

- status: completed
- decision: `accept_m2659_route_to_post_index_branch_synthesis`
- manifest: `experiments/manifests/m2660-engineering-controller-route-a-baseline-evidence-index-after-target-protected-report-refresh-materialization-result-audit.json`
- parent summary: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/summary.json`
- parent evidence index: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/evidence_index.csv`
- parent gap matrix: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/gap_matrix.csv`
- parent claim boundary rows: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/claim_boundary_rows.csv`
- parent next-action admission: `runs/m2659_engineering_controller_route_a_baseline_evidence_index_after_target_protected_report_refresh/next_action_admission.csv`
- follow-up manifest: `experiments/manifests/m2661-engineering-controller-route-a-post-index-target-protected-evidence-branch-synthesis.json`
- next: `m2661-engineering-controller-route-a-post-index-target-protected-evidence-branch-synthesis`

## Audit Result

M2660 accepts M2659 as a refreshed Route A baseline evidence index after the
M2657 target/protected report and M2658 audit. The refreshed index is accepted
as process evidence for a branch synthesis only. It is not admitted as repair
success, checkpoint promotion, validation, ranking, success-rate,
driver-performance, paper, current-sim, high-fidelity validation,
finite-window-vs-GRU, full ideal driver, or self-ID evidence.

Accepted M2659 summary:

```text
status_pass: true
source_artifacts_present: true
source_artifacts_reanalyzed_only: true
new_repair_training_or_rollout_run: false
evidence_index_row_count: 12
gap_matrix_row_count: 6
claim_boundary_row_count: 16
next_action_admission_row_count: 5
required_artifacts_present: true
M2657 report indexed: true
M2658 audit indexed: true
target_protected_split_preserved: true
protected_failure_blocking: true
actor_contract_shape_72_action_3: true
hidden_oracle_actor_input_detected: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
driver_performance_claim_made: false
```

Required artifacts are present:

```text
summary.json
evidence_index.csv
gap_matrix.csv
claim_boundary_rows.csv
next_action_admission.csv
milestone doc
```

## Evidence Index Audit

M2659 indexes the relevant Route A chain:

```text
m2639 previous Route A evidence index: stale but traceable
m2641 source-only fresh generalization panel: source baseline evidence
m2644 behavior-gap taxonomy: target map plus protected mitigation reference
m2648 gap-targeted repair evidence: target pass, protected fail, not promoted
m2655 mitigation-preserving repair evidence: target pass, protected fail, not promoted
m2656 repair-branch pivot synthesis: same-row repair loop closed
m2657 target/protected report summary and scenario-role report
m2657 target tradeoff rows: target improvement evidence, not success denominator
m2657 protected tradeoff rows: protected failure blocker
m2657 protected regression focus rows: row-level blocker
m2658 target/protected report result audit
```

The index explicitly separates target improvement evidence from protected
mitigation blocker evidence:

```text
target_evidence_index_row_count: 5
protected_blocking_evidence_index_row_count: 9
target_role_count: 3
protected_role_count: 1
protected_role_excluded_from_target_success_denominator: true
```

## Protected Failure Audit

The protected mitigation blocker remains active:

```text
M2655 target preservation gates all passed: true
M2655 protected component gates all passed: false
M2655 target and protected gates all passed: false
failed protected gates:
  severity_proxy_non_regression
  obstacle_penetration_non_regression
  minimum_obstacle_clearance_preservation
```

M2659 correctly keeps the selected M2655 candidate as diagnostic trace only:

```text
selected candidate: m2655_softened_gap_bias
selected candidate treated as winner: false
checkpoint promoted: false
```

M2660 therefore rejects any route that treats target improvement evidence as
repair success or driver-performance evidence. The protected blocker must be
handled by synthesis or a new evidence axis, not by another same-row public
repair sweep.

## Claim Boundary Audit

M2659 claim-boundary rows pass. The allowed M2659 claims are only:

```text
baseline_evidence_index_refreshed
target_protected_report_indexed
protected_failure_blocker_indexed
follow_up_result_audit_registered
```

M2659 correctly rejects:

```text
repair_success
controller_family_ranking
winner_selection
checkpoint_promotion
success_rate_verdict
driver_performance
validation_result
high_fidelity_validation_result
paper_level_evidence
finite_window_vs_gru
current_sim_verdict
level3_self_identification
```

## Actor Boundary

M2660 accepts the actor/action boundary:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
localization_labels_actor_visible: false
objective_gate_labels_actor_visible: false
route_decision_labels_actor_visible: false
```

Labels, gate outcomes, route decisions, and localization fields remain artifact
metadata only. They must not become actor inputs in later training or repair
work.

## Supported Claims

M2660 supports these bounded claims:

```text
M2659 refreshed the Route A baseline evidence index after M2657/M2658.
The refreshed index includes the current target/protected report and audit.
Target improvements and protected mitigation failures are indexed separately.
Protected mitigation failure remains blocking.
The refreshed index is ready for branch synthesis.
```

## Rejected Claims

M2660 rejects these interpretations:

```text
M2659 proves repair success.
M2659 admits another same-row source-only repair.
M2659 may promote m2655_softened_gap_bias or any checkpoint.
M2659 ranks controller families or selects a winner.
M2659 computes a success-rate verdict.
M2659 is a validation result.
M2659 is driver-performance or paper-level evidence.
M2659 is finite-window-vs-GRU or self-ID evidence.
M2659 is a current-sim or high-fidelity validation verdict.
```

No reset, step, rollout, replay, validation, training, PPO, source build,
adapter probe, external high-fidelity simulation, ranking, winner selection,
promotion, or success-rate computation was executed in M2660.

## Decision

Route to M2661 post-index target/protected evidence branch synthesis.

M2661 should answer the six required synthesis questions and decide whether
Route A should pivot to a new evidence route, stop the current repair/index
branch, or continue under a clearly new evidence axis. It must not open another
same-row public repair loop, weaken protected mitigation gates, rank or promote
controllers, or claim driver performance.
