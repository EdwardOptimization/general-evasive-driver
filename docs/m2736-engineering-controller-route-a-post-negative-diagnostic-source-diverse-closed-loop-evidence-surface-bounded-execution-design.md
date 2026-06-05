# M2736 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Closed-Loop Evidence Surface Bounded Execution Design

## Metadata

- status: completed
- decision: `admit_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight`
- manifest: `experiments/manifests/m2736-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-design.json`
- parent audit: `docs/m2735-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-result-audit.md`
- parent summary: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/summary.json`
- follow-up manifest: `experiments/manifests/m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight.json`
- next: `m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight`

## Design Premise

M2735 accepts M2734 as a complete and claim-safe evidence-surface
materialization. The accepted surface contains:

```text
input source rows: 6
evidence-surface candidate rows: 18
source-diversity bucket rows: 2
blocked surface rows: 12
negative diagnostic context rows: 31
actor-contract guard rows: 10
claim-boundary rows: 22
gate rows: 26
```

M2736 is design-only. It does not reset, step, run policy actions, rollout,
replay, validate, train, run PPO, build source, probe adapters, start external
simulation, rank rows, select winners, promote checkpoints, compute
success-rate verdicts, or claim driver performance.

The design purpose is to define a bounded M2737 execution preflight that can
produce new closed-loop diagnostic data from the M2734 source-diverse surface
without returning to the M2728 same-surface repair loop.

## Execution Input Surface

M2737 may consume only these M2734 artifacts as candidate inputs:

```text
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/summary.json
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/evidence_surface_candidate_rows.csv
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/source_diversity_bucket_rows.csv
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/blocked_surface_rows.csv
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/negative_diagnostic_context_rows.csv
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/actor_contract_guard_rows.csv
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/claim_boundary_rows.csv
runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/gate_matrix.csv
```

The candidate input set is exactly:

```text
18 M2734 candidate rows
9 M2693 source-diverse current-sim offtrack rows
9 M2716 exact-executable task-source aggregate rows
task families: T4, T5
same_surface_m2728_repair: false for all candidates
protected_or_hf3_blocked: false for all candidates
hidden_oracle_actor_input_detected: false for all candidates
diagnostic_only_no_verdict: true for all candidates
```

M2737 must reject any candidate row that is not `materialization_admitted=true`,
has `same_surface_m2728_repair=true`, has `protected_or_hf3_blocked=true`, or
requires hidden/oracle actor input.

## Candidate Resolution

M2737 must write `execution_candidate_resolution_rows.csv` before any execution.
The resolution stage maps each M2734 candidate to an executable current-M1690
workload without ranking source families or profile families.

Resolution rules:

```text
M2693 candidate rows:
  join source_row_id to M2693 target_execution_rows.csv target_id
  preserve source_key, task_family, source_edge, workload_id, profile_config_path, and checkpoint_path
  admit one execution row per M2734 M2693 candidate

M2716 candidate rows:
  join source_row_id to M2716 exact_execution_rows.csv task_source_id
  select the fixed L3_online_gru row only as the canonical recurrent policy-under-test
  do not compare or rank L0/L2/L3_reset rows
  admit one execution row per M2734 M2716 task-source candidate
```

The M2716 aggregate rows are not themselves executable specs. They are anchors.
The fixed `L3_online_gru` resolution is a protocol choice for one diagnostic
driver under test, not a profile winner selection. If any M2716 task-source
candidate lacks an exact `L3_online_gru` workload row, M2737 must write a
failure row and not substitute another profile.

Expected resolution:

```text
candidate rows resolved: 18
M2693 resolved rows: 9
M2716 resolved rows: 9
resolved policy profile: L3_online_gru for all rows
profile ranking: false
winner selection: false
```

## Exclusion And Guardrail Surface

M2737 must carry these rows as guardrails, not execution candidates:

```text
negative diagnostic context rows: 31
same-surface M2728 repair blocker rows: 1
protected mitigation blocker rows: 10
HF3 source dependency blocker rows: 1
```

Guardrail rules:

```text
M2728 negative context remains non-ranking non-verdict context
direct same-surface M2728 repair execution remains rejected
protected rows remain not executed and outside success denominators
HF3 execution remains paused until the source dependency blocker is separately resolved
guardrail labels remain actor-invisible
guardrail outcomes are not ordinary success denominators
```

Any candidate resolution that overlaps a blocked row or an M2728 repair target
row must be rejected into `candidate_execution_failure_rows.csv`.

## Execution Protocol

M2737 may execute reset, step, policy action, and rollout only for the resolved
18 candidate rows. It must not execute replay, measured validation, training,
PPO, source build, adapter probe, external simulation, private holdout, ranking,
winner selection, checkpoint promotion, or success-rate verdict computation.

Execution rules:

```text
one diagnostic rollout per resolved candidate row
fixed policy checkpoint from the resolved row, expected M2655 checkpoint for M2693 rows
fixed L3_online_gru profile for M2716 rows
no profile-specific tuning
no active config overwrite
no repair overlay from M2728
no new actor input features
no hidden/oracle labels
```

If the runner cannot resolve a row or execute it without changing actor inputs,
profile-specific tuning, or active configs, it must write a failure row and keep
the run artifact-complete.

## Output Artifacts

M2737 should write:

```text
runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/summary.json
execution_candidate_resolution_rows.csv
candidate_execution_rows.csv
candidate_execution_failure_rows.csv
source_family_aggregate.csv
task_family_aggregate.csv
negative_context_guard_rows.csv
blocked_surface_guard_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
run_state.json
docs/m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight.md
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

These are diagnostic fields only. They must not become ranking, validation,
success-rate verdict, repair-success, driver-performance, paper, current-sim,
high-fidelity, full-driver, or self-ID claims.

## Gate Matrix

M2737 passes as an execution preflight only if all of these hold:

```text
M2734 summary status_pass true
18 candidate rows loaded
18 candidate rows resolved or accounted by failure rows
9 M2693 candidates accounted
9 M2716 candidates accounted
31 M2728 negative context rows carried as guardrails
12 blocked surface rows carried as guardrails
same-surface M2728 repair execution admitted false
protected rows executed false
protected rows in success denominator false
HF3 execution started false
actor 72/action 3 preserved
hidden_oracle_actor_input_detected false
actor input changed false
profile_specific_tuning false
active_config_overwritten false
ranking_run false
winner_selected false
checkpoint_promoted false
success_rate_verdict_claim_made false
driver_performance_claim_made false
all required artifacts present
one result-audit follow-up manifest registered
```

Behavioral failure rows may still pass the artifact gate if every candidate is
accounted for and all claim/actor/blocker boundaries are clean. A pass does not
mean the driver succeeded.

## Follow-Up

M2736 admits:

```text
m2737-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-preflight
```

M2737 must register a separate M2738 result audit before any interpretation.

## Claim Boundary

Allowed M2736 claim:

```text
M2736 defines an actor-safe bounded execution protocol for the audited M2734
source-diverse evidence surface and admits one separately pre-registered
execution preflight.
```

Rejected claims:

```text
execution result
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
profile ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
