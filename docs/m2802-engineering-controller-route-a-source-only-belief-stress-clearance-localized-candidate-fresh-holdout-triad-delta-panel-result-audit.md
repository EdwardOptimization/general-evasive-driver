# M2802 Engineering Controller Route A Source-Only Belief-Stress Clearance-Localized Candidate Fresh-Holdout Triad Delta Panel Result Audit

## Metadata

- status: completed
- decision: `accept_m2801_route_to_clearance_localized_corrective_branch_synthesis`
- manifest: `experiments/manifests/m2802-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-result-audit.json`
- audit doc: `docs/m2802-engineering-controller-route-a-source-only-belief-stress-clearance-localized-candidate-fresh-holdout-triad-delta-panel-result-audit.md`
- parent summary: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/summary.json`
- parent triad execution rows: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/triad_execution_rows.csv`
- parent candidate-minus-source deltas: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/candidate_minus_source_delta_rows.csv`
- parent candidate-minus-base deltas: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/candidate_minus_base_delta_rows.csv`
- parent gate matrix: `runs/m2801_engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2803-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-branch-synthesis.json`
- next: `m2803-engineering-controller-route-a-source-only-belief-stress-clearance-localized-corrective-branch-synthesis`

## Audit Result

M2802 accepts M2801 as complete and claim-safe source-only diagnostic evidence.
The accepted parent result has:

```text
status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
failed_gate_ids: []
seed_start_index: 12
seed_count: 4
fresh_holdout_seed_indices: [12, 13, 14, 15]
previous_seed_indices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
fresh_holdout_seed_indices_disjoint_from_previous: true
horizon_steps: 160
m2793_horizon_steps: 140
objective_row_count: 18
triad_execution_row_count: 216
candidate_minus_source_delta_row_count: 72
candidate_minus_base_delta_row_count: 72
proof_gate_row_count: 16
generalization_gate_row_count: 9
behavior_retention_gate_row_count: 9
promotion_guard_row_count: 4
actor_guard_row_count: 7
mitigation_reference_guard_row_count: 8
claim_boundary_row_count: 12
gate_matrix_row_count: 38
```

Checkpoint lineage is preserved:

```text
source_checkpoint_hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
base_candidate_checkpoint_hash: 32b001944b688162ba9afb379aa6ed54f59920261d3a10ec8572d6e2da769651
candidate_checkpoint_hash: 44bedadceae2e53efaa7c37cf5be211cb8652b9088a1d7e1f237843f69ab2f20
m2799_manifest_m2782_base_hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
```

The M2801 triad subjects are therefore M2655 source, M2791 start candidate, and
M2799 clearance-localized corrective candidate. M2782 remains recorded lineage
and is not reinterpreted as the M2801 base subject.

## Diagnostic Delta Accounting

M2801 fresh-holdout candidate-minus-source deltas are diagnostic row accounting
only:

```text
candidate_minus_source_minimum_obstacle_clearance_m:
  mean: -0.00365399786071096
  median: -0.004516664759614875
  min: -0.014554557376424304
  max: 0.006923733641878371
  positive rows: 23
  negative rows: 49

candidate_minus_source_minimum_road_margin_m:
  mean: 0.0034070942843518006
  median: 0.0051379295250229
  positive rows: 60
  negative rows: 12

candidate_minus_source_final_speed_mps:
  mean: 0.0010017903825189295
  median: 0.0014799093692587917
  positive rows: 49
  negative rows: 23

candidate_minus_source_max_abs_yaw_rate:
  mean: 0.0028702986539291125
  median: 0.003020197857187046
  positive rows: 48
  negative rows: 24

candidate_minus_source_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72
```

M2801 fresh-holdout candidate-minus-M2791-start deltas are also diagnostic row
accounting only:

```text
candidate_minus_base_minimum_obstacle_clearance_m:
  mean: -0.001043581525003352
  median: -0.0016528113121421217
  min: -0.00591508324654022
  max: 0.0017836451484196658
  positive rows: 23
  negative rows: 49

candidate_minus_base_minimum_road_margin_m:
  mean: 0.0008685596277096715
  median: 0.001303491179564631
  positive rows: 60
  negative rows: 12

candidate_minus_base_final_speed_mps:
  mean: 0.00033127288279043306
  median: 0.0005978255597214321
  positive rows: 49
  negative rows: 23

candidate_minus_base_max_abs_yaw_rate:
  mean: 0.0007452456651026714
  median: 0.0007822529462475081
  positive rows: 48
  negative rows: 24

candidate_minus_base_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72
```

The corrective candidate remains mixed and skew negative on the hard obstacle-
clearance guard in both delta families. The stable_avoidable retention slice
also contains clearance-negative rows:

```text
stable_avoidable_candidate_minus_source_obstacle_clearance_negative_count: 4
stable_avoidable_candidate_minus_base_obstacle_clearance_negative_count: 2
```

Road-margin, final-speed, yaw-rate, conflict, and action-delta summaries are
allowed diagnostic side effects only. They do not override the clearance and
stable_avoidable guard outcome.

## Boundary Audit

Actor and claim boundaries pass:

```text
actor_contract_shape_72_action_3: true
hidden_or_oracle_actor_inputs_required: false
actor_visible_atlas_or_role_labels_detected: false
mitigation_reference_rows_guarded: true
training_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
repair_success_claim_made: false
driver_performance_claim_made: false
level3_self_id_claim_made: false
```

Actor input remains P0 observation 72/action 3. Atlas, role, dynamics, stress,
clearance, outcome, success, progress, route, and verdict labels remain
actor-invisible evaluator metadata. Mitigation reference rows remain outside
ordinary denominators and outside delta interpretation.

## Rejected Claims

M2802 rejects these interpretations:

```text
M2801 proves the M2799 candidate is better than source: false
M2801 proves the M2799 candidate is better than M2791 start: false
M2801 admits checkpoint ranking: false
M2801 admits winner selection: false
M2801 admits checkpoint promotion: false
M2801 admits validation readiness or validation result: false
M2801 proves clearance-localized repair success: false
M2801 proves driver performance: false
M2801 proves paper-level evidence: false
M2801 proves current-sim or high-fidelity validation: false
M2801 proves finite-window-vs-GRU evidence: false
M2801 proves level3 self-identification: false
M2801 completes the full ideal driver gate: false
```

## Failure Taxonomy

Controlled failures and risks:

```text
contract_violation:
  controlled. Observation/action shape and hidden/oracle exclusion pass.

lineage_invalid:
  controlled. Source, M2791-start, M2799-candidate, and retained M2782 lineage
  hashes are recorded.

scenario_sampling_failure:
  controlled for this panel. Seed indices 12-15 are disjoint from prior 0-11
  and all ordinary role, dynamics, and stress buckets are covered.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators.

objective_overfit:
  active risk. Favorable side metrics must not hide clearance-negative rows.
```

Active blocker:

```text
behavior_regression:
  active. Obstacle-clearance deltas are negative in 49/72 candidate-minus-source
  rows and 49/72 candidate-minus-M2791-start rows, with stable_avoidable
  negative rows still present.

local_search:
  active if the next step is another same-axis corrective update or panel
  without a branch synthesis and a materially different evidence axis.
```

## Route Decision

M2802 accepts M2801 completeness and claim safety, then routes to M2803 branch
synthesis before any further clearance-localized corrective update, new panel,
ranking, promotion, or performance interpretation.

M2803 must decide whether the M2796-M2802 clearance-localized corrective branch
should:

```text
stop as diagnostic-only because the corrective update worsened the hard
  clearance guard on fresh holdout;
package M2799/M2801 with strict limitations and no promotion;
pivot to a broader Route A architecture or scenario-distribution change;
pivot to Route C high-fidelity interface preparation;
defer to Route B only through a separate fair controller-family matrix.
```

The accepted M2801 result is fresh closed-loop diagnostic evidence only. It is
not a validation result, promotion result, driver-performance result, paper
result, current-sim verdict, high-fidelity result, full-driver result, or
self-ID result.
