# M2722 Engineering Controller Route A Current-M1690 Exact-Executable Reentry Offtrack Repair Target Panel Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2721_route_to_current_m1690_exact_executable_reentry_offtrack_repair_branch_synthesis`
- manifest: `experiments/manifests/m2722-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-result-audit.json`
- audit artifact: `docs/m2722-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-result-audit.md`
- parent summary: `runs/m2721_engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel/summary.json`
- parent doc: `docs/m2721-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-target-panel-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2723-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-branch-synthesis.json`
- next: `m2723-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-branch-synthesis`

## Audit Summary

M2722 accepts M2721 as a complete and claim-safe no-rollout target-panel
materialization. M2721 consumed the accepted M2719 taxonomy and M2720 audit,
materialized all offtrack rows into a repair-planning target surface, and kept
collision, diagnostic-success, and protected-exclusion rows separate.

Accepted M2721 state:

```text
status_pass: true
result_class: engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_target_panel_materialization_pass
offtrack target rows: 31
collision caution rows: 2
diagnostic success context rows: 3
protected exclusion rows: 12
target panel aggregate rows: 5
actor-contract join rows: 8
claim-boundary rows: 20
gate rows: 16
gate_matrix_pass: true
```

This is an actionable repair-design surface for Route A, not repair success,
driver performance, validation, ranking, paper, current-sim, high-fidelity,
full-driver, or self-ID evidence.

## Artifact Audit

M2721 wrote the required artifacts:

```text
summary.json: present
source_accounting_rows.csv: present
offtrack_target_rows.csv: 31 rows
collision_caution_rows.csv: 2 rows
diagnostic_success_context_rows.csv: 3 rows
protected_exclusion_rows.csv: 12 rows
target_panel_aggregate_rows.csv: 5 rows
actor_contract_join_rows.csv: 8 rows
claim_boundary_rows.csv: 20 rows
gate_matrix.csv: 16 rows
doc: present
follow-up manifest: present
```

All 16 gate rows pass. The gate matrix verifies source artifact presence, the
M2720 route decision, M2719 status, offtrack/collision/success/protected row
counts, offtrack-only target admission, no execution scheduling, non-ranking
profile context, protected rows outside denominators, actor-invisible target
labels, aggregate presence, actor-contract preservation, claim-boundary
blocking, and required artifact presence.

## Target Panel Boundary Audit

M2721 keeps the panel slices separate:

```text
offtrack target rows: 31
collision caution rows: 2
diagnostic success context rows: 3
protected exclusion rows: 12
```

The offtrack target rows are admitted for later repair planning only:

```text
target_panel_admitted: true for 31/31 offtrack rows
execution_scheduled: false for 31/31 offtrack rows
target_labels_actor_visible: false for 31/31 offtrack rows
```

The non-offtrack rows are not silently dropped or converted into wins:

```text
collision caution rows:
  target_panel_admitted: false
  execution_scheduled: false
  diagnostic_only_no_verdict: true

diagnostic success context rows:
  target_panel_admitted: false
  execution_scheduled: false
  diagnostic_only_no_verdict: true

protected exclusion rows:
  target_panel_admitted: false
  execution_scheduled: false
  protected_rows_in_success_denominator: false
```

Profile context remains diagnostic and non-ranking. No target row selects a
profile winner, computes a success-rate verdict, or schedules execution.

## Actor And Claim Boundary Audit

M2721 preserves the actor/action contract:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
target_labels_actor_visible: false
profile_ranking_allowed: false
execution_scheduled: false
protected_rows_in_success_denominator: false
```

M2721 did not run:

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

M2721 did not claim repair success, driver performance, validation readiness,
validation result, paper evidence, finite-window-vs-GRU conclusion,
current-response sufficiency, current-sim verdict, high-fidelity validation,
full ideal driver completion, or level3 self-identification.

## Post-M2470 Route-Plan Check

M2722 remains within the `docs/post-m2470-route-plan.md` Route A boundary. It
uses the exact-executable diagnostic branch to expose a known failure taxonomy
and target surface, while preserving the rule that hidden dynamics, oracle
labels, TTC, reference trajectories, precomputed progress, and success labels
must not enter actor input.

It also avoids the hard-stop failures called out by the route plan:

```text
no static current-sim verdict is claimed
no controller or profile ranking is introduced
no actor input contract is changed
no driver performance, L0/L1/L2/L3, self-ID, or current-sim verdict is claimed
```

The target panel can change the next admission decision because it narrows the
next Route A synthesis from another diagnostic repeat to a bounded decision:
continue to offtrack repair design only if the synthesis can preserve collision,
protected-row, and actor-contract guards, or stop/pivot otherwise.

## Failure Taxonomy

- `contract_violation`: not observed. Actor 72/action 3, no hidden/oracle actor
  input, actor-invisible target labels, and protected rows outside denominators
  are preserved.
- `lineage_invalid`: not observed. M2721 traces through M2720, M2719, M2718,
  and the Post-M2470 Route A boundary.
- `metric_artifact`: controlled. M2721 materializes target rows and gates only;
  it does not compute ranking, success-rate verdicts, or performance metrics.
- `scenario_sampling_failure`: active. The target panel shows 31 offtrack rows
  from the 36-row exact-executable diagnostic branch.
- `behavior_regression`: active/incomplete. Collision caution rows and
  protected exclusions require guardrails in the next design before any repair
  execution route can be admitted.
- `objective_overfit`: controlled if the next step freezes a bounded repair
  design instead of repeating the same target materialization or ranking
  profiles.
- `proof_washout`: controlled. Claim rows and this audit keep the panel as
  repair-design input only.

## Next Route Decision

Decision:

```text
accept_m2721_route_to_current_m1690_exact_executable_reentry_offtrack_repair_branch_synthesis
```

M2721 is complete enough to close the result audit. Because the Route A branch
has reached the synthesis cadence, the next step must synthesize M2719-M2722
before any repair design, repair execution extension, training, validation,
ranking, performance interpretation, paper claim, current-sim verdict,
high-fidelity validation, full-driver claim, or self-ID claim.

Next route:

```text
m2723-engineering-controller-route-a-current-m1690-exact-executable-reentry-offtrack-repair-branch-synthesis
```

M2723 must remain synthesis-only. It should answer the standard synthesis
questions, preserve the 31 offtrack target rows as repair-design input only,
keep collision caution rows as guardrails, keep diagnostic success rows as
context, keep protected exclusions outside targets and denominators, preserve
the 72/3 actor contract, and select one follow-up route or stop.

## Claim Boundary

Allowed M2722 claim:

```text
M2721 target-panel artifacts are complete, actor-contract safe, and
claim-safe; they expose a 31-row offtrack repair-planning surface that can be
synthesized before admitting any design, execution, or verdict claim.
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
