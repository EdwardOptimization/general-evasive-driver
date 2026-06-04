# M2676 Paper Route History Vs Current Response Bounded Comparison Execution Result Audit

## Metadata

- status: completed
- decision: `accept_m2675_route_to_full_t4_t5_public_comparison_execution_preflight`
- manifest: `experiments/manifests/m2676-paper-route-history-vs-current-response-bounded-comparison-execution-result-audit.json`
- audit artifact: `docs/m2676-paper-route-history-vs-current-response-bounded-comparison-execution-result-audit.md`
- parent doc: `docs/m2675-paper-route-history-vs-current-response-bounded-comparison-execution-preflight.md`
- parent summary: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/summary.json`
- parent artifacts: `episode_rows.csv`, `profile_aggregate.csv`, `spec_aggregate.csv`, `runtime_enforcement_join_rows.csv`, `claim_boundary_rows.csv`, and `gate_matrix.csv`
- governing plans: `docs/post-m2470-route-plan.md`, `docs/self-id-go-no-go-paper-route-plan.md`, and `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2677-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-preflight.json`
- next: `m2677-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-preflight`

## Audit Summary

M2676 accepts M2675 as a complete bounded public comparison execution
preflight and routes to one larger audited public T4/T5 execution preflight.

Accepted M2675 state:

- `status_pass`: true
- result class: `paper_route_history_vs_current_response_bounded_comparison_execution_preflight_pass`
- episode rows: 48
- executed profiles: 12/12
- selected public specs: 4/4
- profile aggregate rows: 12
- spec aggregate rows: 4
- runtime-enforcement join rows: 12/12 pass
- protocol controller-family IDs mapped: 9/9
- claim-boundary rows: 26/26 pass
- gate-matrix rows: 18/18 pass
- selected metrics finite: true
- required artifacts present: true

M2675 did run bounded public environment rollouts and policy actions. It did
not run replay, measured validation, training, PPO, private holdout,
profile-specific tuning, controller-family ranking, winner selection,
checkpoint promotion, success-rate verdict computation, driver-performance
measurement, paper verdicts, finite-window-vs-GRU verdicts, current-sim
verdicts, high-fidelity validation, full ideal driver gates, or self-ID
verdicts.

## Artifact Audit

### Episode And Aggregate Rows

M2675 wrote the required bounded execution artifacts:

```text
episode_rows.csv: 48 rows
profile_aggregate.csv: 12 rows
spec_aggregate.csv: 4 rows
```

The executed public spec panel is intentionally small:

```text
m1686-spec-0000: T4 t4_staged_warmup_capability
m1686-spec-0001: T4 t4_actuator_delay_response
m1686-spec-0002: T5 t5_near_boundary_warmup
m1686-spec-0003: T5 t5_boundary_axis_retarget
```

All selected metric fields are finite across episode, profile aggregate, and
spec aggregate rows. The success-rate columns are accepted as diagnostic
aggregate metrics only. They are not ranking evidence and are not
success-rate verdict fields.

### Runtime-Enforcement Join Rows

M2675 joins all executed profiles back to the M2673 runtime-enforcement rows.
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
runtime `current_tiled` transform:

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

### Claim Boundary

M2675 writes 26 claim-boundary rows:

- allowed rows: 9
- blocked rows: 17
- blocked claim-made values: all false

The blocked claims include training/PPO, replay, private-holdout tuning,
profile-specific tuning, controller-family ranking, winner selection,
checkpoint promotion, success-rate verdicts, driver performance, validation
readiness/result, paper-level evidence, finite-window-vs-GRU result,
current-sim verdict, high-fidelity validation, level3 self-identification, and
full ideal driver completion.

## Outcome Semantics Caveat

M2675 is a clean execution-preflight pass, not a comparison result. The 48-row
panel is too small for controller-family ranking and only includes four public
T4/T5 specs. Historical full-rollout audit M1694 also showed that even a
complete 864-cell public rollout cannot be interpreted safely from raw success
alone because outcome semantics and termination causes can dominate the
meaning of aggregate success.

Therefore M2676 admits a larger public execution route only under the same
claim boundary. The next route must write richer execution and outcome
artifacts, but it must still route to result audit before any finite-window,
GRU, current-response, driver-performance, paper, current-sim, or self-ID
interpretation.

## Failure Taxonomy

- `contract_violation`: not observed. M2675 preserves the P0/action 3
  deployable actor boundary and no hidden/oracle actor input is detected.
- `lineage_invalid`: not observed. M2673 runtime enforcement, M2674 audit,
  M2675 summary, M2675 CSV artifacts, and the M2676 manifest are present.
- `metric_artifact`: controlled for preflight. Row counts, runtime joins, and
  selected metric finiteness pass; outcome interpretation remains blocked.
- `scenario_sampling_failure`: unresolved for paper claims. M2675 covers only
  four public T4/T5 specs, not the larger 72-spec public workload or all
  decisive task families.
- `behavior_regression`: not decided. M2675 records behavior rows but does not
  compare or rank controller families.
- `objective_overfit`: controlled. M2675 uses no private holdout, no
  profile-specific tuning, no replay, no training, no winner selection, and no
  promotion.
- `proof_washout`: controlled. Diagnostic metrics are explicitly separated
  from success-rate verdicts, paper evidence, finite-window-vs-GRU conclusions,
  and self-ID claims.

## Next Route Decision

Decision:

```text
accept_m2675_route_to_full_t4_t5_public_comparison_execution_preflight
```

M2677 should execute the materialized M1690 public T4/T5 workload under the
current M2673/M2675 runtime-control and claim-boundary discipline:

- 12 corrected M1674 profile checkpoints;
- 72 public executable T4/T5 specs;
- 864 target workload cells;
- resumable execution with failure rows;
- episode, profile, spec, stratum, comparison, outcome, termination, hidden
  dynamics diagnostic, runtime join, claim-boundary, gate-matrix, and run-state
  artifacts;
- no training, replay, PPO, private holdout, profile-specific tuning, actor
  input change, ranking, winner selection, promotion, success-rate verdict,
  driver-performance claim, paper claim, finite-window-vs-GRU conclusion,
  current-sim verdict, high-fidelity validation claim, full ideal driver claim,
  or self-ID claim.

## Claim Boundary

Allowed M2676 claim:

```text
M2675 bounded execution preflight artifacts are complete and clean enough to
admit one larger public T4/T5 execution preflight.
```

Rejected claims:

```text
controller-family ranking
finite-window superiority
GRU superiority
current-response sufficiency
recurrent-belief advantage
level3 self-identification
paper verdict
current-sim verdict
high-fidelity validation readiness or result
driver-performance result
full ideal driver completion
promotion evidence
```
