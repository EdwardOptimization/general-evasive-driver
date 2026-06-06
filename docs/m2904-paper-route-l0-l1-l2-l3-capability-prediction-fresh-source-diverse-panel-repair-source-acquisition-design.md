# M2904 Paper Route L0/L1/L2/L3 Capability-Prediction Fresh Source-Diverse Panel Repair Source-Acquisition Design

## Metadata

- status: completed
- decision: `admit_m2905_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight`
- manifest: `experiments/manifests/m2904-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-design.json`
- parent audit: `docs/m2903-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-result-audit.md`
- parent materialization summary: `runs/m2902_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_materialization_preflight/summary.json`
- parent seed gaps: `runs/m2902_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_materialization_preflight/seed_gap_rows.csv`
- follow-up manifest: `experiments/manifests/m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-preflight.json`
- next: `m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-preflight`

## Design Decision

M2904 admits a bounded repair/source-acquisition materialization preflight.

Formal decision:

```text
admit_m2905_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight
```

The design preserves the M2901 admission thresholds. It does not convert
source-singleton rows into proof rows, does not use public reference rows as a
validation denominator, and does not treat guard rows as ordinary success rows.

The immediate blocker is exact:

```text
fresh_source_diverse_candidate rows: 0
source_singleton_seed rows: 34
guard rows: 21
candidate_artifact_count>=2 gaps: 24
source_family_tag_count>=2 gaps: 17
```

M2904 therefore chooses a repair materialization route instead of model-quality
validation, paper proof, or branch stop.

## Repair Surface

The 34 seed-gap rows remain useful only as repair seeds. They split as follows:

```text
candidate_artifact_count>=2 only: 17
source_family_tag_count>=2 only: 10
candidate_artifact_count>=2 and source_family_tag_count>=2: 7
```

Task-family coverage in the repair surface:

```text
T4: 15
T5: 19
```

Environment-template families in the repair surface:

```text
t5_near_boundary_warmup: 14
t4_capability_step_temporal: 7
t4_actuator_delay_response: 6
t5_boundary_axis_retarget: 5
t4_staged_warmup_capability: 2
```

This is enough to design a repair acquisition surface, but not enough to admit a
fresh/source-diverse panel.

## Admission Contract

A repaired row may become a `fresh_source_diverse_candidate` only if it satisfies
the original M2901 criteria:

```text
outside the 17 public_reference_usable task_source_id set
classification is not guard
required_profiles_present is true
config_checkpoint_complete is true
candidate_artifact_count >= 2
source_family_tag_count >= 2
diagnostic_artifact_count >= 2
deployable_history_features_available is true
future_capability_targets_available is true
actor_contract_shape_72_action_3 is true
hidden_oracle_actor_input_required is false
future_target_actor_input_required is false
evaluator_targets_actor_visible is false
```

The aggregate design targets also remain unchanged:

```text
fresh_candidate_task_count >= 24
fresh_candidate_profile_task_count >= 288
source_family_count >= 3
task_family_count >= 2
max_single_source_family_share <= 0.40
max_single_task_family_share <= 0.70
target_family_coverage_count == 6
```

M2905 may report that the repaired surface is still insufficient. That outcome
must route to result audit, pivot, synthesis, or stop; it must not weaken the
contract.

## Acquisition Lanes

M2905 must materialize acquisition rows, not validation rows.

### Lane A: Candidate-Support Repair

Rows missing `candidate_artifact_count>=2` require at least one additional
candidate artifact from an allowed independent source trace. Candidate support
must be linked to source provenance and cannot be inferred from a guard row.

Allowed materialization evidence:

```text
repo-local execution/fresh-candidate diagnostic artifacts
repo-local paired-delta artifacts
repo-local selected-candidate artifacts
repo-local post-package candidate artifacts that are not guard or limitation rows
explicit acquisition-required rows when no repo-local source exists
```

### Lane B: Source-Family Repair

Rows missing `source_family_tag_count>=2` require support from a second source
family. The second family must be source-level provenance, not a renamed copy of
the same artifact.

Allowed family repair evidence:

```text
independent executable source family
paired-delta source family linked to the same task_source_id
selected-candidate source family linked to the same task_source_id
explicit source-acquisition-required row if only one source family exists
```

### Lane C: Dual Repair

Rows missing both candidate and source-family support must satisfy both Lane A
and Lane B before they can be considered repaired.

### Lane D: Exclusion

Public reference rows, guard rows, protected rows, package limitation rows,
prior-surface rows, and rows requiring actor-visible future targets remain
excluded. They may explain gaps, but they cannot become validation, paper, or
ordinary denominator rows.

## M2905 Required Artifacts

M2905 must write:

```text
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/summary.json
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/seed_gap_repair_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/candidate_support_repair_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/source_family_repair_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/dual_repair_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/acquisition_required_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/repaired_candidate_projection_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/exclusion_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/split_boundary_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/target_boundary_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/gate_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/rollback_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/claim_rows.csv
runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/run_state.json
```

The M2905 summary must report:

```text
status_pass
gate_matrix_pass
decision
seed_gap_row_count
candidate_support_gap_count
source_family_gap_count
dual_gap_count
repaired_candidate_projection_count
acquisition_required_count
projected_fresh_candidate_task_count
projected_fresh_candidate_profile_task_count
projected_source_family_count
projected_task_family_count
projected_target_family_coverage_count
projected_max_single_source_family_share
projected_max_single_task_family_share
projected_design_targets_satisfied
actor_contract_shape_72_action_3
hidden_oracle_actor_input_required
future_target_actor_input_required
evaluator_targets_actor_visible
paper_holdout_admitted
preflight_only_split
model_quality_claim_made
paper_claim_made
finite_window_vs_gru_claim_made
level3_self_id_claim_made
driver_performance_claim_made
current_sim_verdict_claim_made
high_fidelity_validation_claim_made
full_ideal_driver_gate_passed
next_blocker
```

## Boundary Rules

M2905 is allowed to inspect existing repo-local M2902/M2903/M2884/M2887/M2898
artifacts. It is not allowed to reset, step, roll out, replay, validate, fit,
train, run PPO, rank, promote, publish, select a winner, or claim performance.

M2905 must preserve:

```text
actor observation/action contract: 72/action 3
hidden_oracle_actor_input_required: false
future_target_actor_input_required: false
evaluator_targets_actor_visible: false
paper_holdout_admitted: false
preflight_only_split: true
source-singleton rows paper proof allowed: false
guard rows ordinary success denominator allowed: false
```

## Supported Claim

M2904 supports only this claim:

```text
The negative M2903 audit has a bounded repair/source-acquisition route that can be materialized before deciding whether Route B can still create a fresh/source-diverse capability-prediction panel.
```

This is a process/design claim. It is not driver evidence and not paper
evidence.

## Rejected Interpretations

M2904 rejects:

```text
fresh/source-diverse panel repaired: false
model-quality validation admitted: false
public reference rows are validation denominator: false
source-singleton rows are proof: false
guard rows are ordinary denominator: false
finite-window-vs-GRU verdict: false
current-sim verdict: false
high-fidelity readiness: false
driver performance evidence: false
level3 self-identification evidence: false
full ideal driver gate passed: false
```

## Follow-Up Route

M2904 registers exactly one next route:

```text
m2905-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-preflight
```

M2905 must materialize repair/source-acquisition accounting rows from the M2902
seed-gap surface and M2903 audit. It must preserve the negative result unless
the original M2901 criteria are actually satisfied by audited source support.
