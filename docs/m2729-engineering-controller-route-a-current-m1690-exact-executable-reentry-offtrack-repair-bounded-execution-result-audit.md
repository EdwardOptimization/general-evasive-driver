# M2729 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Bounded Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2728_route_to_current_m1690_exact_executable_reentry_offtrack_repair_result_synthesis`
- manifest: `experiments/manifests/m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-result-audit.json`
- audit doc: `docs/m2729-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-result-audit.md`
- parent summary: `runs/m2728_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight/summary.json`
- parent doc: `docs/m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight.md`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2730-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-result-synthesis.json`
- next: `m2730-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-result-synthesis`

## Audit Decision

M2729 accepts M2728 as a complete and claim-safe bounded repair execution
preflight. M2728 executed only the 31 M2725 candidate target rows under
temporary run-dir overlay snapshots, wrote all required audit artifacts, and
preserved the actor/action, guardrail, protected-row, and claim boundaries.

The audit decision is:

```text
accept_m2728_route_to_current_m1690_exact_executable_reentry_offtrack_repair_result_synthesis
```

This admits only a branch synthesis step. It does not admit another immediate
same-surface repair execution, active config overwrite, ranking, validation,
driver-performance interpretation, paper evidence, current-sim verdict,
high-fidelity validation, full-driver completion, or self-ID evidence.

## Parent Artifact Audit

M2728 status:

```text
status_pass: true
result_class: engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight_pass
required_artifacts_present: true
gate_matrix_pass: true
```

M2728 wrote the required artifacts:

```text
repair execution rows: 31
candidate execution failure rows: 0
accounted candidates: 31/31
repair overlay application rows: 465
guardrail audit rows: 17
profile aggregate rows: 4
anchor aggregate rows: 9
actor contract rows: 12
claim-boundary rows: 38
gate rows: 21
failed gate rows: 0
```

Required artifacts are present:

```text
summary.json
repair_execution_rows.csv
candidate_execution_failure_rows.csv
profile_aggregate.csv
anchor_aggregate.csv
repair_overlay_application_rows.csv
guardrail_audit_rows.csv
actor_contract_join_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2728-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-bounded-execution-preflight.md
```

## Execution Outcome Audit

M2728 accounts for every admitted repair candidate:

```text
candidate rows: 31
repair execution rows: 31
candidate execution failure rows: 0
task families: T4=19, T5=12
profiles:
  L0_current_masked: 8
  L2_window_50_current_tiled: 9
  L3_online_gru: 9
  L3_reset_control_corrected: 5
```

The diagnostic outcome remains poor:

```text
success: 1/31
collision: 3/31
off_track terminations: 27/31
obstacle_collision terminations: 3/31
diagnostic success rows with empty termination reason: 1/31
```

Profile aggregates are diagnostic only:

```text
L0_current_masked: success 0/8, collision 1/8, offtrack 7/8
L2_window_50_current_tiled: success 0/9, collision 0/9, offtrack 9/9
L3_online_gru: success 0/9, collision 2/9, offtrack 7/9
L3_reset_control_corrected: success 1/5, collision 0/5, offtrack 4/5
```

These aggregates must not be used as ranking, winner selection,
success-rate-verdict, validation, driver-performance, paper, current-sim,
high-fidelity, full-driver, or self-ID evidence.

## Overlay And Guardrail Audit

The temporary overlay boundary passed:

```text
repair overlay application rows: 465
active_config_overwritten: false
profile_specific_tuning: false
temporary run-dir snapshots: true
all selected metrics finite: true
```

M2728 preserved all guardrails:

```text
collision caution guardrails: 2
diagnostic success context guardrails: 3
protected exclusion guardrails: 12
guardrail execution rows: 0
protected rows executed: false
protected rows in success denominator: false
```

Collision caution rows remain visible. Diagnostic success rows remain context,
not profile wins. Protected exclusions remain not executed and outside ordinary
success denominators.

## Actor And Claim Boundary Audit

M2728 preserved the actor/action contract:

```text
observation_shape: 72
action_shape: 3
actor contract rows: 12
actor contract rows passing: 12
actor-visible contract metadata rows: 0
actor input changed: false
hidden/oracle actor input detected: false
target labels actor-visible: false
protected labels actor-visible: false
profile labels actor-visible: false
route labels actor-visible: false
verdict labels actor-visible: false
```

M2728 did run bounded reset, step, rollout, and policy action for the 31
candidate target rows, as admitted by M2727. It did not run replay, measured
validation, training, PPO, private holdout, ranking, winner selection,
checkpoint promotion, or active config overwrite.

The 38 claim-boundary rows all pass. Allowed diagnostic bookkeeping claims are
separate from forbidden interpretation claims. M2728 did not claim repair
success, driver performance, validation readiness, validation result, paper
evidence, finite-window-vs-GRU conclusion, current-response sufficiency,
current-sim verdict, high-fidelity validation, full ideal driver completion, or
level3 self-identification.

## Post-M2470 Route-Plan Check

M2729 remains within Route A from `docs/post-m2470-route-plan.md`: it audits an
actuator-level engineering controller diagnostic branch while preserving the
human-view actor contract and rejecting hidden dynamics, oracle labels, TTC,
reference trajectories, precomputed progress labels, and success labels as
actor inputs.

The post-M2470 hard-stop rule also applies. M2719-M2729 have now produced a
target panel, synthesis, repair design, candidate materialization, execution
design, bounded execution, and result audit for the same offtrack repair
surface. M2728 is complete and claim-safe, but the diagnostic result is still
offtrack-dominated and collision-cautioned. A direct M2730-like narrow repair
execution would risk repeating the same local search loop.

The next step should therefore be branch synthesis, not another immediate
repair execution.

## Failure Taxonomy

- `contract_violation`: not observed. Actor 72/action 3, no hidden/oracle actor
  input, actor-invisible labels, temporary overlay snapshots, and protected rows
  outside denominators are preserved.
- `lineage_invalid`: not observed. M2728 traces to M2727 execution design,
  M2726 audit, M2725 candidate rows, and the M2721 offtrack target panel.
- `metric_artifact`: controlled. M2728 writes diagnostic success, collision,
  offtrack, profile, and anchor aggregates but labels them non-ranking and
  non-verdict.
- `scenario_sampling_failure`: active. The repair execution surface is still
  dominated by the same current-M1690 exact-executable offtrack rows.
- `behavior_regression`: active. Collision caution is visible as 3/31 collision
  outcomes and 17 guardrail rows remain non-target.
- `objective_overfit`: active enough to require synthesis. Another same-surface
  repair loop would not be justified before summarizing what M2719-M2729
  changed and what it failed to change.
- `proof_washout`: controlled. The audit rejects performance, validation,
  paper, current-sim, high-fidelity, full-driver, and self-ID interpretations.

## Rejected Routes

M2729 rejects direct profile ranking from the M2728 profile aggregates. The
single diagnostic success row belongs to a non-ranking aggregate and cannot
select a controller family or winner.

M2729 rejects direct repair-success interpretation. The bounded overlay
execution is artifact-complete, but 30/31 candidate rows remain unsuccessful,
with 27 offtrack terminations and 3 collisions.

M2729 rejects another immediate narrow repair execution over the same surface
without synthesis. The branch has reached the post-M2470 local-search guard:
after one bounded repair execution, the next evidence-expanding step is to
summarize the branch and decide whether to stop, pivot, or define a new
evidence surface.

## Follow-Up Route

The next route is:

```text
m2730-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-result-synthesis
```

M2730 should synthesize M2719-M2729 and answer:

```text
1. Did the repair branch change the offtrack diagnostic surface?
2. Did it only add process-complete repair infrastructure?
3. Is another same-surface repair execution likely to change the Route A
   engineering admission decision?
4. Is the branch overfitting public current-M1690 exact-executable gates?
5. Should Route A stop this repair branch, pivot to a new evidence surface,
   freeze it as diagnostic, or admit one bounded non-same-surface follow-up?
```

Recommended synthesis direction:

```text
freeze_m2728_as_negative_diagnostic_and_pivot_to_new_evidence_surface_or_stop_same_surface_repair
```

## Claim Boundary

Allowed M2729 claim:

```text
M2728 bounded offtrack repair execution artifacts are complete and claim-safe,
but the diagnostic outcome remains offtrack-dominated and does not justify
direct repair-success or performance interpretation.
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
