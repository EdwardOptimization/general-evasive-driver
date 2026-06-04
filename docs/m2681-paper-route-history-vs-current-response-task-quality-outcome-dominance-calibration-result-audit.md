# M2681 Paper Route History Vs Current Response Task Quality Outcome Dominance Calibration Result Audit

## Metadata

- status: completed
- decision: `accept_m2680_pivot_to_task_quality_role_semantics_repair_materialization_preflight`
- manifest: `experiments/manifests/m2681-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-result-audit.json`
- audit artifact: `docs/m2681-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-result-audit.md`
- parent doc: `docs/m2680-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-materialization-preflight.md`
- parent summary: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/summary.json`
- governing plans: `docs/post-m2470-route-plan.md`, `docs/self-id-go-no-go-paper-route-plan.md`, and `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2682-paper-route-history-vs-current-response-task-quality-role-semantics-repair-materialization-preflight.json`
- next: `m2682-paper-route-history-vs-current-response-task-quality-role-semantics-repair-materialization-preflight`

## Audit Summary

M2681 accepts M2680 as a complete, claim-safe, no-rollout calibration
materialization. M2680 does not make the Route B M2677 public comparison
interpretable as ranking, paper evidence, finite-window-vs-GRU evidence,
current-response sufficiency, current-sim verdict, driver-performance evidence,
full ideal driver evidence, or level3 self-identification evidence.

Accepted M2680 state:

```text
status_pass: true
result_class: paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration_pass
episode rows consumed: 864/864
profiles covered: 12/12
specs covered: 72/72
spec outcome-dominance rows: 72
profile outcome-dominance rows: 12
task-family rows: 2
comparison interpretability rows: 11
calibration gap rows: 9
claim-boundary rows: 29
gate rows: 17
gate_matrix_pass: true
required_artifacts_present: true
```

M2680 consumed existing M2677 artifacts only. It did not execute reset, step,
rollout, replay, measured validation, training, PPO, source build, adapter
probe, external simulation, policy action, ranking, winner selection,
promotion, success-rate verdict computation, comparison-delta verdict
computation, paper verdict computation, current-sim verdict computation,
high-fidelity validation, full ideal driver gates, or self-ID verdicts.

## Artifact Audit

M2680 wrote the required calibration artifacts:

```text
summary.json: present
spec_outcome_dominance_rows.csv: 72 rows
profile_outcome_dominance_rows.csv: 12 rows
task_family_outcome_dominance_rows.csv: 2 rows
comparison_interpretability_rows.csv: 11 rows
calibration_gap_rows.csv: 9 rows
claim_boundary_rows.csv: 29 rows
gate_matrix.csv: 17 rows
run_state.json: present
doc: present
```

All gate rows pass. The gate matrix verifies M2677 source artifacts are present,
M2677 `status_pass` is true, M2677 row counts are complete, selected metrics
are finite, calibration rows cover the expected slices, blocker rows are
materialized, comparison rows remain diagnostic-only, and no environment
execution or policy action occurred in M2680.

The claim boundary is clean:

```text
allowed claims: 10/10 pass
blocked claims: 19/19 not made
```

## Calibration Findings

M2680 materially changes the Route B branch state by making the interpretation
blocker explicit:

```text
success_obstacle_pass: 35/864
collision_failure: 35/864
off_track_noncollision_noncompletion: 793/864
speed_too_low_noncollision_noncompletion: 1/864
off_track termination: 794/864
```

Outcome-dominance spread:

```text
specs blocked: 68/72
profiles blocked: 9/12
task families blocked: 2/2
spec rows interpretable for history comparison: 0/72
profile rows interpretable for history comparison: 0/12
task-family rows interpretable for history comparison: 0/2
comparison rows interpretable for ranking: 0/11
comparison rows allowed for synthesis only: 11/11
```

The 9 calibration gaps are accepted as blocker evidence:

- `global_offtrack_dominance`
- `success_support_thin`
- `hidden_dynamics_bucket_missing`
- `reset_control_ambiguity`
- `l2_current_tiled_zero_success_delta`
- `role_semantics_missing`
- `private_holdout_absent`
- `paper_verdict_missing`
- `slice_outcome_dominance_spread`

## Interpretation Decision

M2681 rejects direct Route B interpretation planning from M2680 because there is
no interpretable history-comparison slice and no comparison row suitable for
ranking.

The audit also rejects another same public full rollout as the immediate next
step. The post-M2470 route plan warns against turning scenario/readiness
blockers into repeated public-gate infrastructure. M2680 shows the blocker is
not missing data volume; it is task quality, role semantics, off-track
dominance, empty hidden-dynamics buckets, and mixed reset/current-response
diagnostics.

The next admissible Route B step is therefore a repair-materialization preflight
that produces a candidate task-quality/role-semantics panel before any new
rollout:

```text
m2682-paper-route-history-vs-current-response-task-quality-role-semantics-repair-materialization-preflight
```

M2682 should materialize:

- role/task-quality blocker rows from M2677/M2680;
- candidate repair rows grouped by task family, source edge, outcome blocker,
  and required role semantics;
- excluded rows that remain unsuitable for comparison;
- a proposed measured-execution subset that could later test Route B without
  off-track dominance, hidden-dynamics ambiguity, or role-label absence;
- claim-boundary and gate rows that keep the output non-verdict.

M2682 must not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or paper/self-ID verdicts.

## Failure Taxonomy

- `contract_violation`: not observed. M2680 only reads artifacts and preserves
  P0 observation/action boundaries; no hidden/oracle actor input or actor
  contract change is present.
- `lineage_invalid`: not observed. All M2680 required artifacts and M2677
  source artifacts are present.
- `metric_artifact`: active for interpretation. M2680 records finite metrics
  but shows aggregate metrics are dominated by off-track and missing bucket
  semantics.
- `scenario_sampling_failure`: active. Public M2677/M2680 evidence is dominated
  by off-track noncompletion across most specs, profiles, and both task
  families.
- `behavior_regression`: not decided. M2681 does not rank controllers or select
  winners.
- `objective_overfit`: controlled by pivoting away from another same public full
  rollout; still a risk if the branch keeps repairing only this public panel.
- `proof_washout`: controlled by claim boundary. Diagnostic comparison rows and
  calibration blockers are explicitly blocked from becoming paper or self-ID
  claims.

## Claim Boundary

Allowed M2681 claim:

```text
M2680 calibration artifacts are complete and claim-safe, and they show the
current M2677 public Route B comparison branch must pivot to task-quality and
role-semantics repair materialization before interpretation or new execution.
```

Rejected claims:

```text
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
comparison-delta verdict
driver performance
validation readiness or result
finite-window superiority
GRU superiority
current-response sufficiency
recurrent-belief advantage
level3 self-identification
paper verdict
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
```

M2681 did not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or verdict computation.
