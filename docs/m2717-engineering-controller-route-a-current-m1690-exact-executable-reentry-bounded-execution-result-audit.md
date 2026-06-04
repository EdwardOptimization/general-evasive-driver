# M2717 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Bounded Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2716_route_to_current_m1690_exact_executable_reentry_branch_synthesis`
- manifest: `experiments/manifests/m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit.json`
- audit artifact: `docs/m2717-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-result-audit.md`
- parent summary: `runs/m2716_engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight/summary.json`
- parent doc: `docs/m2716-engineering-controller-route-a-current-m1690-exact-executable-reentry-bounded-execution-preflight.md`
- follow-up manifest: `experiments/manifests/m2718-engineering-controller-route-a-current-m1690-exact-executable-reentry-branch-synthesis.json`
- next: `m2718-engineering-controller-route-a-current-m1690-exact-executable-reentry-branch-synthesis`

## Audit Summary

M2717 accepts M2716 as a complete and claim-safe bounded diagnostic execution
pack. M2716 executed the M2714 exact existing current-M1690 candidate panel and
kept M2710 protected proposal rows excluded from execution and ordinary success
denominators.

Accepted M2716 state:

```text
status_pass: true
result_class: engineering_controller_route_a_current_m1690_exact_executable_reentry_bounded_execution_preflight_pass
candidate rows: 36
exact execution rows: 36
failure rows: 0
accounted candidates: 36/36
profile aggregate rows: 4
anchor aggregate rows: 9
protected proposal exclusion audit rows: 12
actor-contract join rows: 12
claim-boundary rows: 33
gate rows: 20
gate_matrix_pass: true
all selected metrics finite: true
```

The behavior snapshot remains diagnostic:

```text
diagnostic success: 3/36
collision: 2/36
termination reasons: none, obstacle_collision, off_track
```

M2717 does not interpret the 3/36 success rows as repair success, profile
ranking, validation, performance, paper, current-sim, high-fidelity,
full-ideal-driver, or self-ID evidence.

## Artifact Audit

M2716 wrote the required artifacts:

```text
summary.json: present
exact_execution_rows.csv: 36 rows
profile_aggregate.csv: 4 rows
anchor_aggregate.csv: 9 rows
protected_proposal_exclusion_audit_rows.csv: 12 rows
actor_contract_join_rows.csv: 12 rows
claim_boundary_rows.csv: 33 rows
gate_matrix.csv: 20 rows
failure_rows.csv: 0 rows
run_state.json: present
doc: present
```

All 20 gate rows pass. The gate matrix verifies source artifacts, M2715 audit
lineage, M2714 status, 36 candidate rows, 36 accounted execution rows, finite
selected metrics, profile and anchor aggregate shape, protected proposal
exclusion count, protected rows outside denominators, actor-contract
preservation, label invisibility, no hidden/oracle actor input, no forbidden
execution, claim-boundary blocking, and required artifact presence.

## Execution And Aggregate Audit

M2716 executed only the exact executable current-M1690 reentry panel:

```text
M2714 exact executable candidate rows: 36
M2716 exact execution rows: 36
M2716 failure rows: 0
executed profiles: 4
anchor task_source_ids: 9
protected proposal execution rows: 0
```

Profile aggregate rows are diagnostic non-ranking rows:

```text
L0_current_masked:
  episodes: 9
  diagnostic_success_rate: 0.0
  collision_rate: 0.1111111111111111
  offtrack_rate: 0.8888888888888888

L2_window_50_current_tiled:
  episodes: 9
  diagnostic_success_rate: 0.0
  collision_rate: 0.0
  offtrack_rate: 1.0

L3_online_gru:
  episodes: 9
  diagnostic_success_rate: 0.0
  collision_rate: 0.0
  offtrack_rate: 1.0

L3_reset_control_corrected:
  episodes: 9
  diagnostic_success_rate: 0.3333333333333333
  collision_rate: 0.1111111111111111
  offtrack_rate: 0.5555555555555556
```

These aggregates are useful for branch synthesis, but they are not fair
controller-family comparison evidence. The panel was selected as a bounded
Route A reentry diagnostic after protected rows were excluded, not as a
pre-registered ranking benchmark.

## Protected Proposal Boundary Audit

M2716 preserved the protected proposal boundary:

```text
M2710 protected proposal exclusion audit rows: 12
m2716_execution_candidate: false for all 12
m2716_execution_admitted: false for all 12
m2716_execution_run: false for all 12
protected_rows_in_success_denominator: false for all 12
```

The protected-side blocker remains active: M2710 proposal rows still are not
exact existing current-M1690 workload rows and cannot be treated as protected
mitigation behavior evidence.

## Actor And Claim Boundary Audit

M2716 preserves the actor/action contract:

```text
observation_shape: 72
action_shape: 3
deployed action mapping: steer throttle brake
hidden_oracle_actor_input_detected: false
target_labels_actor_visible: false
protected_labels_actor_visible: false
profile_labels_actor_visible: false
blocker_labels_actor_visible: false
route_labels_actor_visible: false
verdict_labels_actor_visible: false
protected_rows_in_success_denominator: false
```

Allowed M2716 execution was bounded to the 36 exact candidate rows:

```text
environment_reset_run: true
environment_step_run: true
policy_action_run: true
policy_rollout_run: true
bounded_exact_executable_reentry_execution: true
```

Forbidden execution and interpretation did not occur:

```text
replay_run: false
measured_validation_run: false
training_run: false
ppo_run: false
private_holdout_used: false
profile_specific_tuning: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_verdict_claim_made: false
repair_success_claim_made: false
driver_performance_claim_made: false
validation_readiness_claim_made: false
validation_result_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
current_response_sufficiency_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
full_ideal_driver_completion_claim_made: false
level3_self_id_claim_made: false
```

## Failure Taxonomy

- `contract_violation`: not observed. Actor 72/action 3, no hidden/oracle
  actor input, actor-invisible labels, and protected rows outside denominators
  are preserved.
- `lineage_invalid`: not observed. M2716 traces through M2715, M2714, M2713,
  M2712, and the Post-M2470 Route A boundary.
- `metric_artifact`: controlled. M2716 records aggregate metrics but blocks
  ranking, success-rate verdict, validation, performance, paper, current-sim,
  high-fidelity, full-driver, and self-ID interpretation.
- `scenario_sampling_failure`: active. The exact executable current-M1690
  reentry panel remains dominated by off-track outcomes, with only 3/36
  diagnostic success rows and 2/36 collision rows.
- `behavior_regression`: unresolved. The protected proposal side remains
  outside execution, and current-M1690 behavior evidence is not yet a repair or
  validation result.
- `objective_overfit`: controlled only if the branch now synthesizes rather
  than repeating the same exact panel execution until a favorable profile
  aggregate appears.
- `proof_washout`: controlled. Claim rows and this audit preserve the fact
  that profile aggregates are diagnostic only.

## Next Route Decision

Decision:

```text
accept_m2716_route_to_current_m1690_exact_executable_reentry_branch_synthesis
```

M2716 is complete enough to close the result audit, but not interpretable as a
repair, ranking, validation, or performance result. The branch has now gone
through design, materialization, audit, bounded execution, and result audit.
The next evidence-changing step should be selected by branch synthesis rather
than by direct profile comparison or another same-panel execution loop.

Next route:

```text
m2718-engineering-controller-route-a-current-m1690-exact-executable-reentry-branch-synthesis
```

M2718 must synthesize M2713-M2717 evidence and choose continue, pivot, stop, or
a targeted bounded repair/design route. It must keep M2716 aggregates
diagnostic, preserve protected proposal exclusions, and avoid validation,
ranking, winner selection, success-rate verdicts, performance, paper,
current-sim, high-fidelity, full ideal driver, or self-ID claims.

## Claim Boundary

Allowed M2717 claim:

```text
M2716 bounded execution artifacts are complete, actor-contract safe, and
claim-safe; they provide diagnostic exact-executable current-M1690 reentry
behavior rows for branch synthesis while preserving protected proposal
exclusions.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-response sufficiency
current-sim verdict
high-fidelity validation readiness or result
protected mitigation preservation result
full ideal driver completion
level3 self-identification
```
