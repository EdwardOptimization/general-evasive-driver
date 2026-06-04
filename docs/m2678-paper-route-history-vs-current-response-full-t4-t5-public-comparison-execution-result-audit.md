# M2678 Paper Route History Vs Current Response Full T4/T5 Public Comparison Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2677_route_to_route_b_full_t4_t5_public_comparison_branch_synthesis`
- manifest: `experiments/manifests/m2678-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-result-audit.json`
- audit artifact: `docs/m2678-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-result-audit.md`
- parent doc: `docs/m2677-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-preflight.md`
- parent summary: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/summary.json`
- parent full-runner summary: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/full_rollout_execution_summary.json`
- governing plans: `docs/post-m2470-route-plan.md`, `docs/self-id-go-no-go-paper-route-plan.md`, and `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2679-paper-route-history-vs-current-response-full-t4-t5-public-comparison-branch-synthesis.json`
- next: `m2679-paper-route-history-vs-current-response-full-t4-t5-public-comparison-branch-synthesis`

## Audit Summary

M2678 accepts M2677 as a complete and claim-safe full public T4/T5 comparison
execution preflight. It does not interpret the aggregate profile or comparison
metrics as controller-family rankings, success-rate verdicts, finite-window vs
GRU evidence, current-response sufficiency evidence, paper evidence, current-sim
verdict, high-fidelity validation evidence, driver-performance evidence, full
ideal driver evidence, or level3 self-identification evidence.

Accepted M2677 state:

- `status_pass`: true
- result class: `paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight_pass`
- episode rows: 864/864
- executed profiles: 12/12
- public T4/T5 specs: 72/72
- failure rows: 0
- profile aggregate rows: 12
- spec aggregate rows: 72
- stratum aggregate rows: 5
- comparison aggregate rows: 11
- outcome aggregate rows: 4
- termination aggregate rows: 4
- profile-outcome aggregate rows: 25
- hidden-dynamics aggregate rows: 0
- profile hidden-dynamics worst-bucket rows: 0
- runtime-enforcement join rows: 12/12 pass
- claim-boundary rows: 36/36 pass
- gate-matrix rows: 26/26 pass
- selected metrics finite: true
- required artifacts present: true

M2677 did run full public environment rollouts and policy actions for the
pre-registered 864-cell workload. It did not run replay, measured validation,
training, PPO, private holdout, profile-specific tuning, controller-family
ranking, winner selection, checkpoint promotion, success-rate verdict
computation, comparison-delta verdict computation, driver-performance
measurement, paper verdicts, finite-window-vs-GRU verdicts, current-response
verdicts, current-sim verdicts, high-fidelity validation, full ideal driver
gates, or self-ID verdicts.

## Artifact Audit

M2677 wrote the required execution artifacts:

```text
episode_rows.csv: 864 rows
profile_aggregate.csv: 12 rows
spec_aggregate.csv: 72 rows
stratum_aggregate.csv: 5 rows
comparison_aggregate.csv: 11 rows
outcome_aggregate.csv: 4 rows
termination_reason_aggregate.csv: 4 rows
profile_outcome_aggregate.csv: 25 rows
failure_rows.csv: 0 rows
```

The hidden-dynamics diagnostic artifact paths exist, but the rows are empty:

```text
hidden_dynamics_aggregate.csv: 0 rows
profile_hidden_dynamics_worst_bucket.csv: 0 rows
```

This is accepted as an M2677 preflight artifact condition because the episode
rows do not contain a `hidden_dynamics_bucket` field. It blocks any
hidden-dynamics robustness interpretation from M2677. A future
hidden-dynamics-specific result would need explicit bucket materialization or a
separate metric/instrumentation route.

All selected metric fields are finite across the episode, profile aggregate,
and spec aggregate rows. Empty aggregate cells such as recovery-time means for
groups without recovery events are not used as verdict fields.

## Runtime-Control Audit

M2677 joins all executed profiles back to the M2673 runtime-enforcement rows.
The join covers all accepted Route B controller-family IDs:

```text
L0-current
L1-one-step
L2-window-13
L2-window-25
L2-window-50
L2-window-100
L2-current-tiled
L3-online-GRU
L3-reset-truncated-control
```

All 12 runtime join rows pass. The four L2 current-tiled profiles preserve the
runtime current-tiled transform:

```text
L2_window_13_current_tiled
L2_window_25_current_tiled
L2_window_50_current_tiled
L2_window_100_current_tiled
```

The L3 reset/truncated control preserves `every_step_control` reset-hidden
policy routing:

```text
L3_reset_control_corrected
```

The actor/action boundary remains preserved:

```text
observation shape: 72
action shape: 3
hidden/oracle actor input detected: false
private holdout used: false
profile-specific tuning: false
actor input contract changed: false
```

## Outcome Semantics Caveat

M2677 is complete enough to audit, but it is not interpretable enough for
controller ranking or paper claims. The dominant outcome is off-track
non-completion:

| outcome bucket | rows | share |
| --- | ---: | ---: |
| off_track_noncollision_noncompletion | 793 | 0.9178 |
| success_obstacle_pass | 35 | 0.0405 |
| collision_failure | 35 | 0.0405 |
| speed_too_low_noncollision_noncompletion | 1 | 0.0012 |

Termination reasons show the same pattern:

| termination reason | rows | share |
| --- | ---: | ---: |
| off_track | 794 | 0.9190 |
| none/success | 35 | 0.0405 |
| obstacle_collision | 34 | 0.0394 |
| speed_too_low | 1 | 0.0012 |

This means raw success and raw profile aggregates are dominated by
road-boundary/off-track behavior. They cannot be used directly as
finite-window, GRU, current-response, paper, current-sim, or driver-performance
verdicts.

## Diagnostic Comparison Caveat

The 11 comparison aggregate rows are accepted as diagnostic-only rows. All rows
have `diagnostic_only_no_ranking_claim=True`.

M2678 records the following diagnostic facts without interpreting them as
claims:

- L2 normal versus current-tiled success-rate deltas are all `0.0` across the
  four windows.
- `L3_online_gru` minus `L3_reset_control_corrected` has diagnostic
  success-rate delta `-0.06944444444444445`, collision-rate delta
  `0.027777777777777776`, clearance-margin mean delta `-0.5557775117167676`,
  and return mean delta `1.7427032208057796`.
- `L3_online_gru` minus best normal L2 has diagnostic success-rate delta
  `0.19444444444444445` but also collision-rate delta
  `0.05555555555555555` and clearance-margin mean delta
  `-7.282939746731788`.

These mixed diagnostics are exactly why the governing plans require the weakest
supported claim and forbid deriving L3 self-ID from aggregate success,
reset-hidden-only tests, source-singleton rows, or raw profile aggregates.

## Failure Taxonomy

- `contract_violation`: not observed. P0 observation/action boundary, no
  hidden/oracle actor input, no private holdout, and no actor input change are
  preserved.
- `lineage_invalid`: not observed. M2673, M2675, M2676, M2677, and all required
  M2677 artifact paths are present.
- `metric_artifact`: active for interpretation. Diagnostic metrics are finite
  and recorded, but off-track dominance and empty hidden-dynamics buckets block
  verdict use.
- `scenario_sampling_failure`: active for paper claims. The full public T4/T5
  workload executes, but the outcome surface is dominated by off-track
  noncompletion rather than clean obstacle-avoidance comparison semantics.
- `behavior_regression`: not decided. M2678 audits behavior rows but does not
  rank controller families or select a winner.
- `objective_overfit`: controlled in M2677 execution. No training, PPO, replay,
  private holdout, profile-specific tuning, or promotion occurred. Repeated
  interpretation attempts on this public workload would increase overfit risk.
- `proof_washout`: controlled by claim boundary. Diagnostic success and
  comparison deltas are explicitly blocked from becoming paper, self-ID, or
  driver-performance claims.

## Next Route Decision

Decision:

```text
accept_m2677_route_to_route_b_full_t4_t5_public_comparison_branch_synthesis
```

M2679 should synthesize the Route B comparison branch after M2670-M2678 before
any further interpretation, calibration, rollout, training, or validation. The
synthesis should decide whether to:

- pivot to task-quality or outcome-dominance calibration before another Route B
  execution;
- design an outcome-semantics interpretation plan that treats off-track,
  collision, obstacle pass, recovery, and mitigation metrics separately;
- stop the current public T4/T5 comparison branch as insufficient for paper
  interpretation;
- or route to a new evidence axis consistent with the post-M2470 plan.

M2679 must not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, success-rate verdict computation, finite-window-vs-GRU verdict,
current-response verdict, current-sim verdict, paper verdict, high-fidelity
validation claim, full ideal driver claim, or self-ID claim.

## Claim Boundary

Allowed M2678 claim:

```text
M2677 full public T4/T5 comparison execution artifacts are complete,
guardrail-clean, and claim-safe enough to require branch synthesis before
interpretation.
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
