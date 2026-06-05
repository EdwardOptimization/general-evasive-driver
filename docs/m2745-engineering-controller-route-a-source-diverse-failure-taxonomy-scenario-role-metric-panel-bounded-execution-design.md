# M2745 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Bounded Execution Design

## Metadata

- status: completed
- decision: `admit_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight`
- manifest: `experiments/manifests/m2745-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-design.json`
- design doc: `docs/m2745-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-design.md`
- parent audit: `docs/m2744-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-materialization-result-audit.md`
- parent summary: `runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight.json`
- next: `m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight`

## Design Premise

M2744 accepts M2743 as a complete and claim-safe Route A scenario-role metric
panel. The accepted panel contains:

```text
scenario role rows: 6
metric contract rows: 6
target panel rows: 18
guardrail context rows: 5
actor-contract guard rows: 16
claim-boundary rows: 31
gate rows: 22
offtrack target rows: 14
collision caution rows: 1
diagnostic success context rows: 3
negative-context guard rows: 31
blocked same-surface guard rows: 1
protected/HF3 exclusion guard rows: 11
```

M2745 is design-only. It does not reset, step, run policy actions, rollout,
replay, validate, train, run PPO, build source, probe adapters, start external
simulation, tune profiles, rank rows, select winners, promote checkpoints,
compute success-rate verdicts, or claim repair success, driver performance,
paper evidence, current-sim validation, high-fidelity validation, full ideal
driver completion, or level3 self-identification.

The design purpose is to admit a bounded M2746 diagnostic execution preflight
over only the audited offtrack target rows while keeping collision, diagnostic
success, negative-context, blocked, protected, and HF3 rows as guardrails.

## Candidate Execution Surface

M2746 may consume only these M2743 artifacts as candidate inputs:

```text
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/summary.json
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/scenario_role_rows.csv
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/metric_contract_rows.csv
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/target_panel_rows.csv
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/guardrail_context_rows.csv
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/actor_contract_guard_rows.csv
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/claim_boundary_rows.csv
runs/m2743_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel/gate_matrix.csv
```

The candidate input set is exactly:

```text
14 M2743 target-panel rows
scenario_role: offtrack_containment_target
target_panel_admitted: true
guardrail_only: false
execution_scheduled in M2743: false
ranking_allowed: false
ordinary_success_denominator_allowed: false
actor_visible_allowed: false
profile_name: L3_online_gru
task families: T4 and T5
source milestones: M2693 and M2716
```

M2746 must reject any candidate row that is not
`scenario_role=offtrack_containment_target`, has `target_panel_admitted` other
than true, has `guardrail_only` true, requires hidden/oracle actor input,
changes actor inputs, or needs profile-specific tuning or active config
overwrites.

The execution candidate schema must preserve at least:

```text
target_panel_id
source_taxonomy_id
scenario_role_id
scenario_role
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
```

Those fields remain row identity and diagnostic context. They are not actor
input, reward oracle input, policy-switching signals, source-family rankings,
task-family rankings, profile rankings, progress labels, or verdict labels.

## Candidate Resolution

M2746 must write `execution_candidate_rows.csv` and
`execution_candidate_resolution_rows.csv` before any reset or step. Resolution
turns the 14 M2743 target rows into executable current-M1690 diagnostic rows
without selecting a winner or changing the driver contract.

Resolution rules:

```text
M2693 source rows:
  use the preserved M2743 source fields as the primary identity
  preserve source_key, task_family, workload_id, task_source_id, and profile_name
  resolve only the preserved L3_online_gru workload/checkpoint/config identity
  do not substitute another source row, task row, profile, or repair target

M2716 source rows:
  use the preserved task_source_id and workload_id as the executable anchor
  keep the fixed L3_online_gru row as the canonical recurrent policy under test
  do not compare or rank L0, L1, L2, L3_reset, or other profiles
  do not substitute another profile if the fixed row is missing
```

If a row lacks an executable workload, checkpoint path, runner configuration,
or actor-safe reset/step path, M2746 must write a failure row and continue
artifact accounting. It must not hide the row, replace it with a nearby row, or
weaken the candidate definition.

Expected resolution:

```text
candidate rows accounted: 14
candidate rows resolved or failed: 14
M2693 candidate rows accounted: 7
M2716 candidate rows accounted: 7
resolved policy profile: L3_online_gru for all resolved rows
profile ranking: false
winner selection: false
```

## Exclusion And Guardrail Surface

M2746 must carry these rows as guardrails, not execution candidates:

```text
collision caution rows: 1
diagnostic success context rows: 3
negative diagnostic context rows: 31
blocked same-surface rows: 1
protected/HF3 exclusion rows: 11
```

Guardrail rules:

```text
collision caution remains non-ranking caution context
diagnostic success context remains regression context, not a winner signal
negative context remains non-ranking non-verdict context
direct same-surface repair execution remains rejected
protected rows remain not executed and outside success denominators
HF3 execution remains paused until the source dependency blocker is separately resolved
guardrail labels remain actor-invisible
guardrail outcomes are not ordinary success denominators
```

Any candidate resolution that overlaps a collision caution, diagnostic success
context, negative-context, blocked, protected, or HF3 guard row must be rejected
into `candidate_execution_failure_rows.csv`.

## Execution Protocol

M2746 may execute reset, step, policy action, and rollout only for the resolved
14 offtrack target rows. It must not execute guardrail rows. It must not execute
replay, measured validation, training, PPO, source build, adapter probe,
external simulation, private holdout, ranking, winner selection, checkpoint
promotion, or success-rate verdict computation.

Execution rules:

```text
one diagnostic rollout per resolved candidate row
fixed policy checkpoint from the resolved row
fixed L3_online_gru profile for every resolved row
no profile-specific tuning
no active config overwrite
no repair overlay
no new actor input features
no hidden/oracle labels
no actor-visible scenario-role, metric, target, protected, blocker, route-decision, success, progress, or verdict labels
```

If the runner cannot execute a candidate without changing actor inputs,
profile-specific tuning, active configs, or guardrail admission, it must write a
failure row and keep the run artifact-complete.

## Output Artifacts

M2746 should write:

```text
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/summary.json
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/execution_candidate_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/execution_candidate_resolution_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/candidate_execution_failure_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/guardrail_context_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/actor_contract_guard_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/claim_boundary_rows.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/gate_matrix.csv
runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/run_state.json
docs/m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight.md
```

Execution rows may record diagnostic metrics:

```text
termination_reason
collision
offtrack
obstacle_completed
minimum clearance
episode length
return
finite metric checks
```

These fields are diagnostic only. They must not become ranking, validation,
success-rate verdict, repair-success, driver-performance, paper, current-sim,
high-fidelity, full-driver, or self-ID claims.

## Gate Matrix

M2746 passes as an execution preflight only if all of these hold:

```text
M2743 summary status_pass true
M2744 audit accepts M2743
14 offtrack target rows loaded
14 candidate rows resolved or accounted by failure rows
only offtrack_containment_target rows admitted as execution candidates
1 collision caution row carried as guardrail
3 diagnostic success context rows carried as guardrails
31 negative-context rows carried as guardrails
1 blocked same-surface row carried as guardrail
11 protected/HF3 rows carried as guardrails
guardrail rows executed false
guardrail rows admitted false
guardrail rows in success denominator false
actor 72/action 3 preserved
hidden_oracle_actor_input_detected false
actor input changed false
scenario-role, metric, target, protected, blocker, route-decision, success, progress, and verdict labels actor-visible false
profile_specific_tuning false
active_config_overwritten false
repair_overlay_applied false
ranking_run false
winner_selected false
checkpoint_promoted false
success_rate_verdict_claim_made false
driver_performance_claim_made false
all required artifacts present
one result-audit follow-up manifest registered
```

Behavioral failure rows may still pass the artifact gate if every candidate is
accounted for and all claim, actor, and guardrail boundaries are clean. A pass
does not mean the driver succeeded.

## Follow-Up

M2745 admits:

```text
m2746-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-preflight
```

M2746 must register a separate M2747 result audit before any interpretation.

## Claim Boundary

Allowed M2745 claim:

```text
M2745 defines a bounded Route A diagnostic execution design over the 14 audited
M2743 offtrack target rows and registers M2746 as the next preflight.
```

Rejected M2745 claims:

```text
driver performance
repair success
validation readiness
validation result
controller-family ranking
source-family ranking
task-family ranking
profile ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window vs GRU conclusion
current-sim verdict
high-fidelity validation readiness
high-fidelity validation result
full ideal driver completion
level3 self-identification
```
