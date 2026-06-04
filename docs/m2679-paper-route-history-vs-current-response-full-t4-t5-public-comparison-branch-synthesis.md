# M2679 Paper Route History Vs Current Response Full T4/T5 Public Comparison Branch Synthesis

## Metadata

- status: completed
- decision: `pivot_to_route_b_task_quality_outcome_dominance_calibration_materialization_preflight`
- manifest: `experiments/manifests/m2679-paper-route-history-vs-current-response-full-t4-t5-public-comparison-branch-synthesis.json`
- synthesis artifact: `docs/m2679-paper-route-history-vs-current-response-full-t4-t5-public-comparison-branch-synthesis.md`
- parent audit: `docs/m2678-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-result-audit.md`
- parent execution summary: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/summary.json`
- parent full-runner summary: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/full_rollout_execution_summary.json`
- governing plans: `docs/post-m2470-route-plan.md`, `docs/self-id-go-no-go-paper-route-plan.md`, and `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2680-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-materialization-preflight.json`
- next: `m2680-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-materialization-preflight`

## Route Decision

M2679 does not continue to another full public T4/T5 comparison rollout.

The Route B branch should continue only by first materializing task-quality and
outcome-dominance calibration evidence from the already executed M2677 rows.
This follows the post-M2470 route rule: do not keep spending milestones on
static or public-gate infrastructure unless the artifact can change the next
admission or interpretation decision.

Selected follow-up:

```text
m2680-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-materialization-preflight
```

M2680 is a no-rollout, no-training, no-ranking materialization preflight. It
must consume existing M2677 artifacts and write explicit spec, profile,
task-family, comparison-interpretability, calibration-gap, claim-boundary, and
gate-matrix rows before any Route B interpretation planning or new execution.

## Evidence Summary

M2670-M2678 produced a complete Route B diagnostic comparison branch:

- M2670 admitted a fair history-vs-current-response comparison matrix under the
  governing paper route.
- M2671 and M2672 materialized and audited the protocol rows, including L2
  current-tiled and L3 reset/truncated controls.
- M2673 and M2674 mapped protocol families to concrete runtime profiles and
  audited runtime enforcement.
- M2675 and M2676 proved a bounded public execution preflight with runtime joins
  and claim-boundary rows.
- M2677 executed the full 864-cell public T4/T5 workload with 12 profiles, 72
  public specs, and zero failure rows.
- M2678 accepted M2677 as complete and claim-safe, but blocked direct
  interpretation because the outcome surface is dominated by off-track
  noncompletion and hidden-dynamics buckets are empty.

Accepted M2677 operational facts:

```text
status_pass: true
episode rows: 864/864
executed profiles: 12/12
public T4/T5 specs: 72/72
failure rows: 0
runtime joins: 12/12 pass
claim-boundary rows: 36/36 pass
gate-matrix rows: 26/26 pass
```

Outcome facts that block interpretation:

| bucket | rows | share |
| --- | ---: | ---: |
| off_track_noncollision_noncompletion | 793 | 0.9178 |
| success_obstacle_pass | 35 | 0.0405 |
| collision_failure | 35 | 0.0405 |
| speed_too_low_noncollision_noncompletion | 1 | 0.0012 |

Termination facts show the same blocker:

| termination reason | rows | share |
| --- | ---: | ---: |
| off_track | 794 | 0.9190 |
| none/success | 35 | 0.0405 |
| obstacle_collision | 34 | 0.0394 |
| speed_too_low | 1 | 0.0012 |

The 11 comparison aggregate rows remain diagnostic only. L2 normal versus
current-tiled success-rate deltas are all zero, while L3 online versus L3 reset
control is mixed: lower success, higher collision, lower clearance, and higher
return. These rows are useful for localization, not for ranking or paper
claims.

## Supported Claims

M2679 supports only the following claims:

- The Route B public comparison pipeline can execute end to end under the
  pre-registered actor/action contract.
- M2677 produced complete diagnostic artifacts for the full public T4/T5 matrix.
- Runtime controls for L2 current-tiled and L3 reset/truncated families were
  preserved through execution.
- The full public comparison branch is not interpretable as a controller-family
  verdict without outcome and task-quality calibration.
- A bounded M2680 calibration materialization route is the next admissible Route
  B step.

## Falsified Or Rejected Claims

M2679 rejects the following claims from M2677/M2678:

- Raw success-rate aggregates are sufficient for Route B controller-family
  ranking.
- The M2677 comparison aggregate supports finite-window superiority, GRU
  superiority, current-response sufficiency, or recurrent-belief advantage.
- The M2677 result supports paper evidence, current-sim verdicts, high-fidelity
  validation readiness, driver-performance claims, full ideal driver completion,
  or level3 self-identification.
- Another full public T4/T5 rollout would be the right next step before
  calibrating outcome dominance and task-quality semantics.
- Hidden-dynamics robustness can be interpreted from M2677; the diagnostic
  bucket artifacts exist but contain zero rows.

## Failure Taxonomy Summary

- `contract_violation`: not observed. P0 observation shape 72, action shape 3,
  no hidden/oracle actor input, no private holdout, and no actor input change
  remain preserved.
- `lineage_invalid`: not observed. M2670-M2678 artifacts and M2677 execution
  outputs exist and are linked.
- `metric_artifact`: active for interpretation. Diagnostic metrics are finite,
  but aggregate success and comparison deltas are dominated by outcome semantics
  rather than clean controller-family behavior.
- `scenario_sampling_failure`: active for paper claims. The public workload is
  executable but produces mostly off-track noncompletion.
- `behavior_regression`: not decided. M2679 does not rank profiles or select a
  winner.
- `objective_overfit`: medium if the branch repeats public full rollouts;
  controlled if it pivots to no-rollout calibration rows.
- `proof_washout`: controlled only if diagnostic rows stay non-verdict and the
  next step materializes blocker evidence explicitly.

## Public Gate Overfit Risk

The overfit risk is high for any next step that repeats the same public T4/T5
rollout or tries to reinterpret the same raw aggregates as proof. The M2677
rows already show the branch's limiting condition: off-track dominance and empty
hidden-dynamics buckets. Re-running the same matrix would mostly measure the
same public gate again.

The overfit risk is lower for a no-rollout materialization that asks a narrower
question:

```text
Which specs, profiles, task families, and comparisons are blocked by outcome
dominance, reset-control ambiguity, mixed metrics, missing hidden-dynamics
buckets, or role/task-quality gaps?
```

That question can change the next admission decision without executing another
public rollout or weakening the claim boundary.

## Next Branch Decision

Decision:

```text
pivot_to_route_b_task_quality_outcome_dominance_calibration_materialization_preflight
```

M2680 must materialize:

- `spec_outcome_dominance_rows.csv`
- `profile_outcome_dominance_rows.csv`
- `task_family_outcome_dominance_rows.csv`
- `comparison_interpretability_rows.csv`
- `calibration_gap_rows.csv`
- `claim_boundary_rows.csv`
- `gate_matrix.csv`
- `summary.json`

The intended output is not a verdict. It is an audit-ready calibration surface
that decides whether Route B can proceed to outcome-semantics interpretation
planning, must repair task quality first, should stop this public comparison
branch, or should pivot to another evidence axis.

## Claim Boundary

Allowed M2679 claim:

```text
M2670-M2678 establish a complete but outcome-dominated Route B public
comparison branch and require no-rollout task-quality and outcome-dominance
calibration before interpretation.
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

M2679 did not execute reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or verdict computation.
