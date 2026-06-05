# M2742 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Design

## Metadata

- status: completed
- decision: `admit_source_diverse_failure_taxonomy_scenario_role_metric_panel_materialization`
- manifest: `experiments/manifests/m2742-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-design.json`
- design doc: `docs/m2742-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-design.md`
- parent audit: `docs/m2741-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-result-audit.md`
- parent summary: `runs/m2740_engineering_controller_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy/summary.json`
- follow-up manifest: `experiments/manifests/m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight.json`
- next: `m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight`

## Design Premise

M2741 accepts M2740 as a complete and claim-safe Route A taxonomy surface.
Route A in `docs/post-m2470-route-plan.md` calls for a scenario-role metric
report as a near-term artifact, while explicitly forbidding hidden dynamics,
oracle labels, slip/tire-force shortcuts, TTC, reference trajectory, and
precomputed success/progress signals in actor input.

Accepted M2740 evidence:

```text
taxonomy rows: 61
execution taxonomy rows: 18
negative-context taxonomy rows: 31
blocked-guard taxonomy rows: 12
diagnostic success context rows: 3
collision failure rows: 1
off_track rows: 14
protected-or-HF3 blocker rows: 11
source-family context rows: 2
task-family context rows: 2
guardrail context rows: 3
actor-contract join rows: 11
claim-boundary rows: 33
gate rows: 23
```

M2742 is design-only. It does not reset, step, run policy actions, rollout,
replay, validate, train, run PPO, build source, probe adapters, start external
simulation, rank families, select winners, promote checkpoints, compute
success-rate verdicts, or claim driver performance.

## Scenario Roles

M2743 should materialize six actor-invisible scenario roles from M2740:

```text
offtrack_containment_target
  source taxonomy family: off_track
  row count: 14 execution rows
  admission: target-panel admitted for later planning only
  use: road-containment and post-avoidance recovery targets
  not allowed: execution scheduling, success-rate denominator, ranking

collision_caution_guard
  source taxonomy family: collision_failure
  row count: 1 execution row
  admission: caution guardrail, not a winner/loser verdict
  use: keep collision avoidance visible while designing containment metrics
  not allowed: single-row performance interpretation

diagnostic_success_context
  source taxonomy family: diagnostic_success_context
  row count: 3 execution rows
  admission: regression context, not winner evidence
  use: future target panels must preserve these rows as context guards
  not allowed: source-family ranking or promotion

negative_context_guardrail
  source taxonomy family: negative_context_guard
  row count: 31 non-executed guard rows
  admission: guardrail only
  use: preserve M2728 negative context and prevent same-surface loop erasure
  not allowed: execution, target admission, ordinary success denominator

blocked_same_surface_guard
  source taxonomy family: blocked_guard
  row count: 1 non-executed blocked row
  admission: blocked guardrail only
  use: reject direct same-surface repair continuation
  not allowed: execution or target admission

protected_hf3_exclusion_guard
  source taxonomy family: protected_or_hf3_blocker
  row count: 11 non-executed blocked rows
  admission: protected/HF3 exclusion guardrail only
  use: keep protected mitigation and HF3 source dependency blockers outside denominators
  not allowed: execution, ordinary denominator use, actor visibility
```

All role labels remain artifact labels only. They must not become actor input,
reward inputs, controller mode labels, policy-switching signals, route-decision
labels, success/progress labels, or validation verdicts.

## Metric Contracts

M2743 should write one metric-contract row per scenario role plus row-level
bindings where the source taxonomy row is executable context. Metric contracts
must be descriptive and admission-focused, not verdict-focused.

Minimum `metric_contract_rows.csv` schema:

```text
metric_contract_id
scenario_role_id
source_taxonomy_family
source_row_count
metric_family
metric_names
metric_source
row_level_binding_required
target_panel_admission_policy
guardrail_only
actor_visible_allowed
ranking_allowed
success_rate_verdict_allowed
ordinary_success_denominator_allowed
claim_scope
```

Metric-family design:

```text
road_containment
  roles: offtrack_containment_target
  metrics: taxonomy_family, termination_reason, offtrack flag, task_family, source_family
  materialization rule: if margin telemetry is unavailable record unavailable rather than fabricate margin

collision_caution
  roles: collision_caution_guard
  metrics: collision flag, outcome_bucket, task_family, source_family
  materialization rule: visible as guardrail context only

diagnostic_regression_context
  roles: diagnostic_success_context
  metrics: success flag, outcome_bucket, task_family, source_family
  materialization rule: preserve as context not winner evidence

negative_context_exclusion
  roles: negative_context_guardrail
  metrics: execution_run false, execution_admitted false, actor_visible false
  materialization rule: guardrail context only

same_surface_blocker
  roles: blocked_same_surface_guard
  metrics: execution_run false, execution_admitted false, blocker preserved
  materialization rule: direct same-surface route remains blocked

protected_hf3_exclusion
  roles: protected_hf3_exclusion_guard
  metrics: protected denominator false, execution_run false, actor_visible false
  materialization rule: protected/HF3 rows remain outside ordinary denominators
```

## Target Panel Contract

M2743 should write `target_panel_rows.csv` over the 18 M2740 execution taxonomy
rows. It should admit only the 14 offtrack rows as future target rows. The 1
collision row and 3 diagnostic success rows must be carried as caution/context
rows, not targets.

Minimum `target_panel_rows.csv` schema:

```text
target_panel_id
source_taxonomy_id
scenario_role_id
source_row_type
source_milestone
source_family
source_key
workload_id
task_source_id
profile_name
task_family
taxonomy_family
primary_failure_family
repair_signal
target_panel_admitted
execution_scheduled
guardrail_only
actor_visible_allowed
ranking_allowed
ordinary_success_denominator_allowed
claim_scope
```

Admission rules:

```text
off_track rows:
  target_panel_admitted true
  execution_scheduled false
  guardrail_only false
  ordinary_success_denominator_allowed false

collision_failure rows:
  target_panel_admitted false
  execution_scheduled false
  guardrail_only true
  ordinary_success_denominator_allowed false

diagnostic_success_context rows:
  target_panel_admitted false
  execution_scheduled false
  guardrail_only true
  ordinary_success_denominator_allowed false
```

No M2743 target row may overwrite active configs, relax geometry, tune a
profile, schedule execution, or become a repair-success claim.

## Guardrail Actor Claim Gates

M2743 should write these aggregate guardrail artifacts:

```text
scenario_role_rows.csv
metric_contract_rows.csv
target_panel_rows.csv
guardrail_context_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
summary.json
docs/m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight.md
```

Guardrail accounting required:

```text
31 negative-context rows remain not run, not admitted, not actor-visible
1 blocked same-surface row remains not run, not admitted, not actor-visible
11 protected-or-HF3 rows remain not run, not admitted, outside denominators, not actor-visible
```

Actor contract gates:

```text
observation shape: 72
action shape: 3
hidden_oracle_actor_input_detected: false
scenario_role_labels_actor_visible: false
metric_labels_actor_visible: false
target_labels_actor_visible: false
protected_labels_actor_visible: false
blocker_labels_actor_visible: false
route_decision_labels_actor_visible: false
success_progress_verdict_labels_actor_visible: false
```

Claim-boundary gates:

```text
artifact materialization allowed
scenario-role metric panel allowed
target-panel planning surface allowed
execution scheduled false
ranking allowed false
winner selected false
success-rate verdict allowed false
repair success claim made false
driver performance claim made false
validation claim made false
current-sim verdict claim made false
paper claim made false
high-fidelity claim made false
full ideal driver claim made false
self-ID claim made false
```

## Follow-Up

M2742 admits materialization-only follow-up:

```text
m2743-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-preflight
```

M2743 should consume M2740/M2741/M2742 artifacts and write the scenario-role
metric panel artifacts above. It must not execute reset, step, policy action,
rollout, replay, validation, training, PPO, source build, adapter probe,
external simulation, private holdout, profile tuning, ranking, winner
selection, promotion, success-rate verdict computation, or performance
interpretation. It should register a separate M2744 result audit if
materialization succeeds.

## Claim Boundary

Allowed M2742 claim:

```text
M2742 defines actor-invisible scenario roles, metric contracts, target-panel
schemas, guardrails, and follow-up materialization gates from accepted M2740
taxonomy evidence.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
task-family ranking
profile ranking
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
