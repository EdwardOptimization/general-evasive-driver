# M2794 Engineering Controller Route A Source-Only Belief-Stress Guardrailed Candidate Fresh-Holdout Triad Delta Panel Result Audit

## Metadata

- status: completed
- decision: `accept_m2793_route_to_source_only_belief_stress_guardrailed_candidate_triad_branch_synthesis`
- manifest: `experiments/manifests/m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit.json`
- audit doc: `docs/m2794-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-fresh-holdout-triad-delta-panel-result-audit.md`
- parent summary: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/summary.json`
- parent triad execution rows: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/triad_execution_rows.csv`
- parent candidate-minus-source deltas: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/candidate_minus_source_delta_rows.csv`
- parent candidate-minus-base deltas: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/candidate_minus_base_delta_rows.csv`
- parent gate matrix: `runs/m2793_engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-triad-branch-synthesis.json`
- next: `m2795-engineering-controller-route-a-source-only-belief-stress-guardrailed-candidate-triad-branch-synthesis`

## Audit Result

M2794 accepts M2793 as complete and claim-safe source-only diagnostic evidence.
The accepted parent result has:

```text
status_pass: true
required_artifacts_present: true
gate_matrix_pass: true
failed_gate_ids: []
seed_start_index: 8
seed_count: 4
fresh_holdout_seed_indices: [8, 9, 10, 11]
previous_seed_indices: [0, 1, 2, 3, 4, 5, 6, 7]
fresh_holdout_seed_indices_disjoint_from_previous: true
horizon_steps: 140
m2787_horizon_steps: 120
objective_row_count: 18
triad_execution_row_count: 216
candidate_minus_source_delta_row_count: 72
candidate_minus_base_delta_row_count: 72
proof_gate_row_count: 16
generalization_gate_row_count: 9
behavior_retention_gate_row_count: 6
promotion_guard_row_count: 4
actor_guard_row_count: 7
mitigation_reference_guard_row_count: 8
claim_boundary_row_count: 11
gate_matrix_row_count: 35
```

Checkpoint lineage is preserved:

```text
source_checkpoint_hash: e6ecf4bc3f273ea8f7bd4149c068708a86c0969a982cac602635339639938b87
base_candidate_checkpoint_hash: 96944838f1075e6ce6d463f336056f1d81799d7ac69d419ca3a9644582cc0ae8
candidate_checkpoint_hash: 32b001944b688162ba9afb379aa6ed54f59920261d3a10ec8572d6e2da769651
```

## Diagnostic Delta Accounting

M2793 fresh-holdout candidate-minus-source deltas are diagnostic row accounting
only:

```text
candidate_minus_source_minimum_obstacle_clearance_m:
  mean: -0.0003189920460919861
  median: -0.0026030437199309198
  min: -0.006653873890877904
  max: 0.011410545190809529
  positive rows: 30
  negative rows: 42

candidate_minus_source_minimum_road_margin_m:
  mean: 0.0034386080322648363
  median: 0.00372921837408291
  positive rows: 72
  negative rows: 0

candidate_minus_source_final_speed_mps:
  mean: 0.003411489771898279
  median: 0.003972710138293367
  positive rows: 72
  negative rows: 0

candidate_minus_source_max_abs_yaw_rate:
  mean: 0.000749332315266252
  median: -0.00012169519104787696
  positive rows: 31
  negative rows: 41

candidate_minus_source_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72
```

M2793 fresh-holdout candidate-minus-base deltas are also diagnostic row
accounting only:

```text
candidate_minus_base_minimum_obstacle_clearance_m:
  mean: -0.00013214111660788612
  median: -0.00039442807985579087
  min: -0.00235656386714167
  max: 0.0022516642629391015
  positive rows: 29
  negative rows: 43

candidate_minus_base_minimum_road_margin_m:
  mean: 0.0005574076583107706
  median: 0.0005734233075074258
  positive rows: 71
  negative rows: 1

candidate_minus_base_final_speed_mps:
  mean: 0.0005114971257720868
  median: 0.0006114056618961028
  positive rows: 70
  negative rows: 2

candidate_minus_base_max_abs_yaw_rate:
  mean: 0.00011760097164286581
  median: -0.000019362223364738362
  positive rows: 31
  negative rows: 41

candidate_minus_base_throttle_brake_conflict_proxy:
  mean: 0.0
  zero rows: 72
```

The fresh-holdout triad panel shows positive road-margin and final-speed row
accounting, but obstacle-clearance deltas remain mixed and skew negative in both
delta families. Obstacle-clearance retention therefore remains an active
behavior-regression risk and must stay the hard guard before road-margin,
yaw-rate, speed, conflict, or action-delta interpretation.

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
outside ordinary denominators and outside delta interpretation.

## Rejected Claims

M2794 rejects these interpretations:

```text
M2793 proves M2791 candidate is better than source: false
M2793 proves M2791 candidate is better than base: false
M2793 admits checkpoint ranking: false
M2793 admits winner selection: false
M2793 admits checkpoint promotion: false
M2793 admits validation readiness or validation result: false
M2793 proves repair success: false
M2793 proves driver performance: false
M2793 proves paper-level evidence: false
M2793 proves current-sim or high-fidelity validation: false
M2793 proves finite-window-vs-GRU evidence: false
M2793 proves level3 self-identification: false
M2793 completes the full ideal driver gate: false
```

## Failure Taxonomy

Controlled failures and risks:

```text
contract_violation:
  controlled. Actor observation/action shape and hidden/oracle exclusion pass.

lineage_invalid:
  controlled. Source, base-candidate, and M2791 candidate checkpoint hashes are
  recorded and distinct.

scenario_sampling_failure:
  controlled for this panel. Seed indices 8-11 are disjoint from prior 0-7 and
  all ordinary role, dynamics, and stress buckets are covered.

proof_washout:
  controlled. Mitigation reference rows remain outside ordinary denominators.

objective_overfit:
  partially controlled. Fresh holdout rows reduce same-surface risk, but
  wording must not promote road-margin or speed positives over clearance.
```

Active risks:

```text
behavior_regression:
  active. Obstacle-clearance deltas are mixed with 42 negative candidate-minus-source
  rows and 43 negative candidate-minus-base rows.

metric_artifact:
  active. The M2791 update is tiny and source-only; action deltas remain small.

local_search:
  active if the next step is another same-style guardrailed delta panel without
  a synthesis decision or materially different evidence axis.
```

## Route Decision

M2794 accepts M2793 completeness and claim safety, then routes to M2795 branch
synthesis before any continuation, new training update, ranking, promotion, or
performance interpretation.

M2795 must decide whether the M2790-M2794 guardrailed candidate branch should:

```text
continue with a different evidence axis
pivot to a broader architecture or scenario-distribution change
stop the branch as diagnostic-only
defer to Route C high-fidelity interface work
package the source-only result with strict limitations
```

The accepted M2793 result is fresh closed-loop diagnostic evidence only. It is
not a full-driver, high-fidelity, paper, performance, or self-ID result.
