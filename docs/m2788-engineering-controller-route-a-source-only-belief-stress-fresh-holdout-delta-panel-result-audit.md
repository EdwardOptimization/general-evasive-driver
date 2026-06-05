# M2788 Engineering Controller Route A Source-Only Belief-Stress Fresh-Holdout Delta Panel Result Audit

## Metadata

- status: completed
- decision: `accept_m2787_route_to_source_only_belief_stress_fresh_holdout_branch_synthesis`
- manifest: `experiments/manifests/m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-result-audit.json`
- audit doc: `docs/m2788-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-delta-panel-result-audit.md`
- parent summary: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/summary.json`
- parent paired execution rows: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/paired_execution_rows.csv`
- parent paired delta rows: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/paired_delta_rows.csv`
- parent gate matrix: `runs/m2787_engineering_controller_route_a_source_only_belief_stress_fresh_holdout_delta_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis.json`
- next: `m2789-engineering-controller-route-a-source-only-belief-stress-fresh-holdout-branch-synthesis`

## Audit Result

M2788 accepts M2787 as complete and claim-safe source-only diagnostic evidence.
The accepted parent result has:

```text
status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
failed_gate_ids: []
seed_start_index: 4
seed_count: 4
fresh_holdout_seed_indices: [4, 5, 6, 7]
m2784_seed_indices: [0, 1, 2, 3]
fresh_holdout_seed_indices_disjoint_from_m2784: true
horizon_steps: 120
m2784_horizon_steps: 80
curriculum_row_count: 18
paired_execution_row_count: 144
paired_delta_row_count: 72
proof_gate_row_count: 13
generalization_gate_row_count: 8
promotion_guard_row_count: 4
actor_guard_row_count: 7
mitigation_reference_guard_row_count: 8
claim_boundary_row_count: 11
gate_matrix_row_count: 25
```

Checkpoint lineage is preserved:

```text
source_checkpoint_hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
candidate_checkpoint_hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
```

## Diagnostic Delta Accounting

M2787 fresh-holdout candidate-minus-source deltas are source-only row
accounting only:

```text
candidate_minus_source_minimum_obstacle_clearance_m:
  mean: 0.00035927758389157286
  median: 0.0012294839614694908
  min: -0.0037394441382763155
  max: 0.005563442547770414
  positive rows: 43
  negative rows: 29

candidate_minus_source_minimum_road_margin_m:
  mean: 0.003045548777864837
  median: 0.003106116556409022
  min: 0.0017406585947428166
  max: 0.004875049267406784
  positive rows: 72
  negative rows: 0

candidate_minus_source_final_speed_mps:
  mean: 0.0026159244394306303
  median: 0.0033156956468582965
  min: -0.004601285240803277
  max: 0.005643853462414361
  positive rows: 63
  negative rows: 9

candidate_minus_source_max_abs_yaw_rate:
  mean: -0.00017877287320032365
  median: -0.00024961173037246764
  min: -0.0010484951493790473
  max: 0.0017912210375098936
  positive rows: 7
  negative rows: 60
  zero rows: 5

candidate_minus_source_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72

mean_action_delta_l1:
  mean: 0.000330366297728483
  positive rows: 72
```

The fresh-holdout panel preserves the M2784 direction for road-margin and
yaw-rate accounting and flips final-speed deltas positive, while obstacle
clearance remains mixed. The action deltas remain very small. This is enough to
support a synthesis decision about the branch, not enough to support ranking,
promotion, performance, validation, or self-identification.

## Boundary Audit

Actor and claim boundaries pass:

```text
actor_contract_shape_72_action_3: true
hidden_or_oracle_actor_inputs_required: false
actor_visible_stress_admission_curriculum_labels_detected: false
mitigation_reference_rows_guarded: true
training_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
driver_performance_claim_made: false
level3_self_id_claim_made: false
```

Actor input remains P0 observation 72/action 3. Role, dynamics, stress,
curriculum, admission, outcome, success, progress, route, and verdict labels
remain actor-invisible evaluator metadata. Mitigation reference rows remain
outside ordinary denominators and outside paired delta rows.

## Rejected Claims

M2788 rejects these interpretations:

```text
M2787 proves candidate is better than source: false
M2787 admits checkpoint ranking: false
M2787 admits winner selection: false
M2787 admits checkpoint promotion: false
M2787 admits validation readiness or validation result: false
M2787 proves repair success: false
M2787 proves driver performance: false
M2787 proves paper-level evidence: false
M2787 proves current-sim or high-fidelity validation: false
M2787 proves finite-window-vs-GRU evidence: false
M2787 proves level3 self-identification: false
M2787 completes the full ideal driver gate: false
```

## Failure Taxonomy

Controlled failures and risks:

```text
contract_violation:
  controlled. Actor observation/action shape and hidden/oracle exclusion pass.

lineage_invalid:
  controlled. Source and candidate checkpoint hashes are recorded and distinct.

scenario_sampling_failure:
  controlled for this panel. Seed indices 4-7 are disjoint from M2784 0-3 and
  all ordinary role, dynamics, and stress buckets are covered.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators.

objective_overfit:
  partially controlled. Fresh holdout rows reduce same-seed overfit risk, but
  wording must not promote source-only diagnostic deltas into performance.
```

Active risks:

```text
behavior_regression:
  active. Obstacle-clearance deltas remain mixed with 29 negative rows.

metric_artifact:
  active. The action deltas are small and the panel is source-only.

local_search:
  active if the next step is another same-style diagnostic panel without a
  synthesis decision or a materially different evidence axis.
```

## Route Decision

M2788 accepts M2787 completeness and claim safety, then routes to M2789 branch
synthesis before any continuation, training update, ranking, promotion, or
performance interpretation.

M2789 must decide whether the M2786-M2788 fresh-holdout branch justifies:

```text
continue with a stronger bounded training/update recipe
pivot to a broader scenario distribution or architecture change
stop the branch as diagnostic-only
defer to Route C high-fidelity interface work
package the source-only result with strict limitations
```

The accepted M2787 result is fresh closed-loop diagnostic evidence only. It is
not a full-driver, high-fidelity, paper, performance, or self-ID result.
