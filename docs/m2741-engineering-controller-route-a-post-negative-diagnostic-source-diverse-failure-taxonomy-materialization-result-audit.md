# M2741 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Failure Taxonomy Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2740_route_to_source_diverse_failure_taxonomy_scenario_role_metric_panel_design`
- manifest: `experiments/manifests/m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-result-audit.json`
- audit doc: `docs/m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-result-audit.md`
- parent summary: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/summary.json`
- parent doc: `docs/m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2742-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-design.json`
- next: `m2742-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-design`

## Audit Summary

M2741 accepts M2740 as complete and claim-safe for the no-rollout source-diverse
failure taxonomy scope. M2740 has `status_pass` true, required artifacts present,
and 23 gate rows passing. The materialization accounted for 61 taxonomy rows:
18 rows from M2737 execution evidence, 31 rows from negative-context guard
evidence, and 12 rows from blocked guard evidence.

This audit does not admit repair success, ranking, validation, performance,
paper evidence, current-sim verdicts, high-fidelity readiness, full ideal driver
completion, or level3 self-identification. It treats the taxonomy as a Route A
diagnostic planning surface only.

## Taxonomy Evidence

Accepted M2740 row accounting:

- taxonomy rows: 61 total
- execution taxonomy rows: 18
- negative-context taxonomy rows: 31
- blocked-guard taxonomy rows: 12
- diagnostic success context rows: 3
- collision failure rows: 1
- off_track rows: 14
- protected-or-HF3 blocker rows: 11
- taxonomy aggregate rows: 9
- source-family context rows: 2
- task-family context rows: 2
- guardrail context rows: 3
- actor-contract join rows: 11
- claim-boundary rows: 33
- gate-matrix rows: 23

The source-family context remains diagnostic and non-ranking:

- `m2693/source_diverse_current_sim_offtrack`: 9 rows, 1 diagnostic success
  context row, 1 collision row, 7 off_track rows, dominant label `off_track`
- `m2716/exact_executable_reentry_baseline`: 9 rows, 2 diagnostic success
  context rows, 0 collision rows, 7 off_track rows, dominant label `off_track`

The task-family context remains diagnostic and non-ranking:

- `T4`: 10 rows, 1 diagnostic success context row, 0 collision rows, 9
  off_track rows, dominant label `off_track`
- `T5`: 8 rows, 2 diagnostic success context rows, 1 collision row, 5
  off_track rows, dominant label `off_track`

The guardrail context remains outside execution admission and success
denominators:

- blocked guard: 1 row, not run, not admitted, not actor-visible
- negative-context guard: 31 rows, not run, not admitted, not actor-visible
- protected-or-HF3 blocker: 11 rows, not run, not admitted, not actor-visible

## Guardrail Actor Claim Boundary

M2740 preserved the P0 actor contract: observation shape 72 and action shape 3.
No hidden dynamics, oracle features, slip labels, TTC labels, reference
trajectory labels, precomputed success labels, route-decision labels, taxonomy
labels, source-family labels, task-family labels, profile labels, protected
labels, blocker labels, progress labels, or verdict labels enter actor input.

M2740 did not execute reset, step, policy action, rollout, replay, validation,
training, PPO, source build, adapter probe, external simulation, private
holdout, profile tuning, ranking, winner selection, promotion, repair-success
measurement, current-sim validation, high-fidelity validation, paper evaluation,
full-driver proof, or self-ID tests.

The audit accepts all 11 actor-contract join rows and all 33 claim-boundary rows
as consistent with Route A diagnostic-taxonomy scope. Source-family,
task-family, and profile context rows are not verdict rows. Guardrail rows are
not execution rows and do not enter ordinary success denominators.

## Decision

Route to M2742 scenario-role metric panel design.

The reason is that M2740 changed the evidence surface from raw source-diverse
execution rows into an auditable failure taxonomy, but it is still
artifact-only evidence reanalysis. Route A's near-term plan in
`docs/post-m2470-route-plan.md` calls for a scenario-role metric report and
targetable evidence surface before stronger execution or paper-facing claims.
The next useful step is therefore a design gate that converts the accepted
taxonomy into actor-safe scenario roles, metric contracts, and target-panel
schemas.

M2742 must not repeat M2737 execution, rank source families, claim performance,
or materialize repair candidates directly. It should define the output contracts
needed for a future materialization or synthesis step: scenario-role rows,
metric-contract rows, target-panel rows, guardrail-context rows,
actor-contract guard rows, claim-boundary rows, and gate-matrix rows.

## Rejected Claims

M2741 rejects all of the following claims from M2740:

- controller-family, source-family, task-family, or profile ranking
- winner selection or promotion
- success-rate verdict
- repair success
- driver-performance improvement
- validation readiness or validation result
- current-sim benchmark verdict
- high-fidelity validation readiness or result
- paper-level evidence
- finite-window vs GRU conclusion
- full ideal driver completion
- level3 self-identification
