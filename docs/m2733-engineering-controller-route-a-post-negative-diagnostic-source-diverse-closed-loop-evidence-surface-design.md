# M2733 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Closed-Loop Evidence Surface Design

## Metadata

- status: completed
- decision: `admit_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_materialization`
- manifest: `experiments/manifests/m2733-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-design.json`
- parent audit: `docs/m2732-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-result-audit.md`
- parent index: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/summary.json`
- follow-up manifest: `experiments/manifests/m2734-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-preflight.json`
- next: `m2734-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-preflight`

## Design Objective

M2733 moves Route A out of the same-surface exact-executable offtrack repair
loop. The next useful evidence surface should combine existing closed-loop
diagnostic sources without interpreting them as repair success, ranking,
validation, paper evidence, current-sim verdict, high-fidelity validation, full
ideal driver completion, or self-ID evidence.

The design admits M2734 as materialization-only. M2734 may write source rows,
candidate rows, blocked rows, actor-contract guards, claim-boundary rows, and
gate rows. It must not reset, step, execute policy actions, roll out, replay,
validate, train, run PPO, source build, adapter probe, import or run external
simulation, rank controllers, select a winner, promote a checkpoint, or
compute success-rate verdicts.

## Source Pools

M2734 should consume these source families:

```text
M2691 source-diverse target panel:
  target_panel_rows: 19
  offtrack_targets: 9
  protected_targets: 10
  source_families: current_sim_offtrack, protected_mitigation

M2693 source-diverse bounded execution:
  executed offtrack rows: 9
  protected failure rows: 10
  diagnostic success: 0/9
  off_track: 7/9
  speed_too_low: 2/9

M2714/M2716 exact-executable reentry baseline:
  exact candidate rows: 36
  executed rows: 36
  diagnostic success: 3/36
  obstacle collision: 2/36
  off_track: 31/36

M2728 negative repair diagnostic:
  repair execution rows: 31
  diagnostic success: 1/31
  collision: 3/31
  off_track: 27/31

M2667 protected readiness blocker:
  known failure boundary rows: 10
  protected blocker preserved: true
  protected rows in success denominator: false

M2638 HF3 source dependency blocker:
  selected-platform execution remains paused until source dependency is supplied
```

M2728 rows are context and exclusion evidence. They must not become a direct
same-surface repair target list.

## Evidence Surface Classes

M2734 should materialize rows into four classes:

```text
source_diverse_closed_loop_candidate:
  candidate rows backed by M2693 and/or M2716 closed-loop execution sources
  with source diversity beyond the M2728 repair-target surface

negative_repair_context:
  M2728 negative repair diagnostic rows retained as non-ranking context

protected_blocked_surface:
  M2667/M2691 protected mitigation rows kept visible but outside denominators

hf3_dependency_blocked_surface:
  M2638 selected-platform HF3 route kept blocked until dependency is supplied
```

Only the first class may be a future materialized closed-loop evidence surface.
The other three classes are boundary and blocker rows.

## Admission Rules

M2734 may mark a row as materialization-admitted only if all conditions hold:

```text
source-backed:
  row traces to an existing M2693 or M2716 closed-loop execution source

non-same-surface:
  row is not a direct M2728 repair target, overlay repair replay, or another
  candidate from the same M2725/M2728 repair surface

source-diverse:
  materialized panel contains at least two source buckets across M2693/M2716
  or source-family/edge combinations, not one profile-specific local repair

actor-safe:
  P0 observation shape 72 and action shape 3 remain unchanged
  no hidden/oracle actor input is introduced
  taxonomy, target, protected, blocker, route, success, progress, and verdict
  labels remain actor-invisible

claim-safe:
  row is diagnostic-only and cannot be used for ranking, success-rate verdict,
  validation readiness, performance, paper, current-sim, high-fidelity,
  full-driver, or self-ID claims
```

## Rejection Rules

M2734 must reject or block rows when any condition holds:

```text
same_surface_repair_loop:
  row is only an M2728/M2725 repair-target continuation

protected_not_executable:
  protected mitigation target lacks current executable support or would enter
  ordinary success denominators

hf3_dependency_unavailable:
  selected-platform HF3 source dependency remains unresolved

actor_contract_risk:
  row would require hidden dynamics, oracle labels, route decisions, target
  labels, blocker labels, success/progress labels, or verdict labels as actor
  input

claim_boundary_risk:
  row would be interpreted as ranking, validation, performance, paper,
  current-sim, high-fidelity, full-driver, or self-ID evidence
```

## Required M2734 Artifacts

M2734 should produce:

```text
summary.json
input_source_rows.csv
evidence_surface_candidate_rows.csv
source_diversity_bucket_rows.csv
blocked_surface_rows.csv
negative_diagnostic_context_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
docs/m2734-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-preflight.md
```

The summary must include:

```text
source_artifacts_reanalyzed_only: true
environment_reset_run: false
environment_step_run: false
policy_action_run: false
policy_rollout_run: false
training_run: false
ranking_run: false
success_rate_computed: false
m2728_negative_diagnostic_preserved: true
same_surface_repair_execution_admitted: false
protected_rows_in_success_denominator: false
hf3_source_dependency_paused: true
actor_contract_shape_72_action_3: true
hidden_oracle_actor_input_detected: false
```

## Follow-Up Route

M2733 admits:

```text
m2734-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-preflight
```

M2734 is not a performance experiment. It is the artifact step required before
any future execution design can be considered. If M2734 cannot produce a
source-diverse materialized panel without collapsing into the M2728 repair
surface, the branch should route to synthesis or stop rather than another
same-surface repair loop.

## Claim Boundary

M2733 is design-only process progress. It does not change driver capability
evidence and does not support repair success, driver performance, validation
readiness/result, ranking, winner selection, promotion, success-rate verdict,
paper-level evidence, finite-window-vs-GRU conclusion, current-sim verdict,
high-fidelity validation, full ideal driver completion, or level3 self-ID.
