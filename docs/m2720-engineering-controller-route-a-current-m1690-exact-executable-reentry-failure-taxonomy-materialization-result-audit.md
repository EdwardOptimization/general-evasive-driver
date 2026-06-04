# M2720 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Failure Taxonomy Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2719_route_to_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization`
- manifest: `experiments/manifests/m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-result-audit.json`
- audit artifact: `docs/m2720-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-result-audit.md`
- parent summary: `runs/m2719_engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy/summary.json`
- parent doc: `docs/m2719-engineering-controller-route-a-current-m1690-exact-executable-reentry-failure-taxonomy-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2721-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-preflight.json`
- next: `m2721-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-preflight`

## Audit Summary

M2720 accepts M2719 as a complete and claim-safe no-rollout taxonomy
materialization. M2719 consumed M2716 diagnostic execution rows and M2718
synthesis, wrote the expected taxonomy artifacts, and preserved the diagnostic
non-ranking boundary.

Accepted M2719 state:

```text
status_pass: true
result_class: engineering_controller_route_a_current_m1690_exact_executable_reentry_failure_taxonomy_materialization_pass
exact execution source rows: 36
exact execution taxonomy rows: 36
protected exclusion taxonomy rows: 12
taxonomy rows total: 48
taxonomy aggregate rows: 6
profile taxonomy context rows: 4
anchor taxonomy context rows: 9
actor-contract join rows: 8
claim-boundary rows: 27
gate rows: 19
gate_matrix_pass: true
```

The taxonomy preserves the branch's diagnostic distribution:

```text
off_track rows: 31
obstacle_collision rows: 2
diagnostic_success rows: 3
protected_excluded rows: 12
```

This is useful failure-surface evidence, not repair success, validation,
ranking, performance, paper, current-sim, high-fidelity, full-driver, or
self-ID evidence.

## Artifact Audit

M2719 wrote all required artifacts:

```text
summary.json: present
source_accounting_rows.csv: present
taxonomy_rows.csv: 48 rows
taxonomy_aggregate_rows.csv: 6 rows
profile_taxonomy_context_rows.csv: 4 rows
anchor_taxonomy_context_rows.csv: 9 rows
actor_contract_join_rows.csv: 8 rows
claim_boundary_rows.csv: 27 rows
gate_matrix.csv: 19 rows
doc: present
```

All 19 gate rows pass. The gate matrix verifies source artifacts, M2718 route
decision, M2716 status, exact execution source count, protected exclusion
source count, taxonomy accounting, preserved counts for diagnostic success,
obstacle collision, off_track, non-ranking profile context, anchor context,
aggregate rows, actor contract, actor-invisible taxonomy labels, protected
exclusions outside execution and denominators, no forbidden execution,
claim-boundary blocking, and required artifact presence.

## Taxonomy Boundary Audit

M2719 keeps all taxonomy families separate:

```text
exact execution rows:
  off_track: 31
  obstacle_collision: 2
  diagnostic_success: 3

protected proposal exclusion rows:
  protected_excluded: 12
```

Profile context remains diagnostic and non-ranking:

```text
profile taxonomy context rows: 4
profile_ranking_allowed: false for all rows
winner_selection_allowed: false for all rows
```

Protected rows remain excluded:

```text
protected_excluded: true for all protected proposal taxonomy rows
protected_execution_run: false for all protected proposal taxonomy rows
protected_rows_in_success_denominator: false for all protected proposal taxonomy rows
```

## Actor And Claim Boundary Audit

M2719 preserves the actor/action contract:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
taxonomy_labels_actor_visible: false
profile_ranking_allowed: false
protected_execution_run: false
protected_rows_in_success_denominator: false
```

M2719 did not run:

```text
environment reset
environment step
policy action
policy rollout
replay
validation
training
PPO
private holdout
profile-specific tuning
ranking
winner selection
checkpoint promotion
success-rate verdict computation
```

M2719 did not claim repair success, driver performance, validation readiness,
validation result, paper evidence, finite-window-vs-GRU conclusion,
current-response sufficiency, current-sim verdict, high-fidelity validation,
full ideal driver completion, or level3 self-identification.

## Failure Taxonomy

- `contract_violation`: not observed. Actor 72/action 3, no hidden/oracle actor
  input, actor-invisible taxonomy labels, and protected rows outside
  denominators are preserved.
- `lineage_invalid`: not observed. M2719 traces through M2718, M2717, M2716,
  and the Post-M2470 Route A boundary.
- `metric_artifact`: controlled. M2719 materializes counts and taxonomy only;
  it does not compute verdict metrics or ranking.
- `scenario_sampling_failure`: active. The dominant failure surface is
  off_track with 31/36 exact execution rows.
- `behavior_regression`: active/incomplete. The protected proposal side remains
  outside execution and still lacks behavior evidence.
- `objective_overfit`: controlled if the next step materializes a target panel
  from taxonomy instead of repeating the same execution panel or selecting a
  profile winner.
- `proof_washout`: controlled. Claim rows and this audit preserve the
  diagnostic-only boundary.

## Next Route Decision

Decision:

```text
accept_m2719_route_to_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization
```

M2719 is complete enough to close the result audit. The next evidence-changing
Route A step should materialize an offtrack-dominant repair target panel from
M2719 rows before any repair design or execution extension.

Next route:

```text
m2721-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-preflight
```

M2721 must remain no-rollout. It should materialize offtrack target rows,
retain collision rows as a separate caution slice, retain diagnostic_success
rows as context rather than winner evidence, preserve protected_excluded rows
outside execution and denominators, and register a result audit before any
targeted repair design or execution.

## Claim Boundary

Allowed M2720 claim:

```text
M2719 failure taxonomy artifacts are complete, actor-contract safe, and
claim-safe; they expose an offtrack-dominant diagnostic failure surface that can
be materialized into a repair target panel before repair design.
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
