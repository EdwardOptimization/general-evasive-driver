# M2901 Paper Route L0/L1/L2/L3 Capability-Prediction Fresh Source-Diverse Panel Design

## Metadata

- status: completed
- decision: `admit_m2902_fresh_source_diverse_panel_materialization_preflight`
- manifest: `experiments/manifests/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.json`
- design artifact: `docs/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.md`
- parent synthesis: `docs/m2900-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-audit-synthesis-or-model-quality-design.md`
- parent inventory audit: `docs/m2885-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-result-audit.md`
- parent candidate rows: `runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight/candidate_panel_rows.csv`
- parent source inventory: `runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight/source_inventory_rows.csv`
- parent dataset summary: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/summary.json`
- parent fitting summary: `runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-preflight.json`
- next: `m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-preflight`

## Design Decision

M2901 admits exactly one next action:

```text
m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-preflight
```

Formal decision:

```text
admit_m2902_fresh_source_diverse_panel_materialization_preflight
```

M2902 may materialize machine-checkable fresh/source-diverse panel rows,
source-diversity accounting rows, split rows, target-coverage rows, seed/gap
rows, guard exclusion rows, rollback rows, claim rows, and a result-audit
manifest. It must not reset, step, roll out, replay, validate prediction
quality, fit additional weights, train, rank profiles, select a winner, promote
a checkpoint, publish a package, or claim model quality, driver performance,
finite-window-vs-GRU evidence, paper evidence, current-sim verdict,
high-fidelity validation, full-driver completion, or self-ID evidence.

M2901 itself did not materialize rows, run a materialization command, reset,
step, roll out, replay, validate, fit, train, rank, promote, or claim model
quality or driver evidence.

## Evidence Inputs

M2901 designs over accepted Route B artifacts only:

```text
M2884 candidate panel rows: 72
M2884 classification usable: 17
M2884 classification source-singleton: 34
M2884 classification guard: 21
M2887 usable profile-task rows: 204
M2898 source task rows: 17
M2898 target scalar dimension: 19
M2898 active target scalars: 13
M2898 available target entries: 221
M2898 run-local fitted preflight weights: 36
```

The accepted 17 usable rows cover T4/T5 only:

```text
T4 rows: 10
T5 rows: 7
t4_actuator_delay_response: 5
t4_capability_step_temporal: 3
t4_staged_warmup_capability: 2
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 2
```

The 34 source-singleton rows are not paper proof. They are useful as seeds or
gap rows for expansion:

```text
source-singleton T4 rows: 15
source-singleton T5 rows: 19
source-singleton rows with one source-family tag: 17
source-singleton rows with two source-family tags but insufficient candidate
artifact diversity: 17
```

The 21 guard rows are prior-surface/package/protected guardrails. They must
remain outside ordinary denominators and paper proof.

## Panel Row Taxonomy

M2902 must classify every candidate row into exactly one row class:

```text
public_reference_usable:
  existing 17 M2884/M2887/M2898 usable rows. These may be used for fit smoke,
  schema regression, calibration sanity, or lineage comparison only. They are
  not validation or paper rows.

source_singleton_seed:
  rows currently classified source-singleton by M2884. These can seed a later
  source-diverse expansion or identify missing coverage. They are not proof.

fresh_source_diverse_candidate:
  rows that are outside the existing public_reference_usable set, have complete
  required profile/config/checkpoint coverage, satisfy source-diversity
  criteria, and preserve evaluator-only target boundaries.

fresh_panel_gap:
  rows needed by the design but missing source diversity, profile coverage, or
  target-family coverage. These are negative planning evidence.

guard_exclusion:
  prior-surface, package, protected, or limitation guard rows. These remain
  excluded from ordinary denominators and paper proof.

rejected_boundary_violation:
  any row requiring hidden/oracle actor input, future target actor input, or
  target-visible actor fields.
```

This taxonomy is deliberately allowed to produce a negative M2902 result. If no
fresh_source_diverse_candidate rows exist, M2902 must record gap rows and route
to panel-source repair, not weaken the source-diversity criteria.

## Source-Diversity Criteria

For a row to be admitted as `fresh_source_diverse_candidate`, M2902 must require:

```text
task_source_id not in the 17 public_reference_usable task_source_ids
classification not equal to guard
required_profiles_present: true
config_checkpoint_complete: true
candidate_artifact_count >= 2
source_family_tag_count >= 2
diagnostic_artifact_count >= 2
deployable_history_features_available: true
future_capability_targets_available: true
actor_contract_shape_72_action_3: true
hidden_oracle_actor_input_required: false
evaluator_targets_actor_visible: false
```

For the materialized fresh panel as a whole, M2902 must report:

```text
fresh_candidate_task_count
fresh_candidate_profile_task_count
source_family_count
task_family_count
max_single_source_family_share
max_single_task_family_share
target_family_coverage_count
guard_exclusion_count
source_singleton_seed_count
fresh_panel_gap_count
```

The design target for later model-quality work is:

```text
fresh_candidate_task_count >= 24
fresh_candidate_profile_task_count >= 288
source_family_count >= 3
task_family_count >= 2
max_single_source_family_share <= 0.40
max_single_task_family_share <= 0.70
target_family_coverage_count == 6
```

M2902 may pass as a materialization preflight only if it writes the accounting
rows and preserves claim boundaries. It must not convert unmet design targets
into a success claim. If the design targets are not met, M2902 must set a
negative decision such as `fresh_panel_materialized_insufficient_diversity` and
route to repair or source acquisition.

## Split And Holdout Semantics

M2902 must write split rows, but the splits remain preflight semantics:

```text
public_reference_fit:
  existing 17 public rows; allowed for schema, smoke, and calibration only.

fresh_panel_candidate:
  fresh_source_diverse_candidate rows; allowed for later design admission only.

source_singleton_seed:
  source-singleton seeds or gap rows; not proof or validation.

guard_exclusion:
  guard rows; not ordinary denominator.

paper_holdout:
  not admitted in M2902.
```

No ordinary model-quality denominator is admitted until a later result audit
accepts M2902 and a separate model-quality design defines the denominator.

## Target-Coverage Criteria

M2902 must preserve the six evaluator-only target families:

```text
future_braking_deceleration_envelope
future_yaw_authority
future_lateral_acceleration_response
actuator_response_lag_proxy
recovery_margin_after_maneuver
first_critical_action_quality
```

Target rows must record:

```text
target_family
required_columns
available_columns
fresh_candidate_available_count
source_singleton_seed_available_count
public_reference_available_count
actor_visible_allowed: false
target_scope: evaluator_only_actor_invisible
status_pass
```

Unavailable targets are masked, not zero targets. Any actor-visible evaluator
target must fail the materialization preflight.

## M2902 Artifact Contract

M2902 must write a new run directory:

```text
runs/m2902_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_materialization_preflight/
```

Required artifacts:

```text
summary.json
panel_row_taxonomy_rows.csv
source_diversity_rows.csv
split_contract_rows.csv
target_coverage_rows.csv
seed_gap_rows.csv
guard_exclusion_rows.csv
materialization_gate_rows.csv
rollback_rows.csv
claim_rows.csv
run_state.json
follow-up result-audit manifest
```

`summary.json` must report at least:

```text
status_pass
gate_matrix_pass
decision
panel_row_taxonomy_row_count
source_diversity_row_count
split_contract_row_count
target_coverage_row_count
seed_gap_row_count
guard_exclusion_row_count
rollback_row_count
claim_row_count
fresh_candidate_task_count
fresh_candidate_profile_task_count
source_singleton_seed_count
public_reference_usable_count
guard_exclusion_count
fresh_panel_gap_count
target_family_coverage_count
source_family_count
task_family_count
max_single_source_family_share
max_single_task_family_share
paper_holdout_admitted
preflight_only_split
actor_contract_shape_72_action_3
hidden_oracle_actor_input_required
future_target_actor_input_required
evaluator_targets_actor_visible
source_singleton_rows_paper_proof_allowed
guard_rows_ordinary_success_denominator_allowed
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

## Rollback Conditions

M2902 must fail closed and route to repair or audit if any of these occur:

```text
actor observation/action contract differs from 72/3
hidden/oracle actor input is required
future target or evaluator label becomes actor-visible
source-singleton rows enter paper proof
guard rows enter ordinary denominators
public_reference_usable rows become validation or paper rows
paper holdout is admitted without a separate manifest
materialization computes model-quality ranking or selects a winner
materialization promotes M2898 fitted preflight weights
materialization runs reset, step, rollout, replay, training, PPO, validation,
or additional optimizer fitting
```

## Claim Boundary

Accepted M2901 interpretation:

```text
M2901 is a complete design for one bounded fresh/source-diverse panel
materialization preflight.
```

Rejected interpretations:

```text
fresh panel rows already exist
prediction quality is validated
L0/L1/L2/L3 profiles are ranked
finite-window-vs-GRU outcome is known
driver performance evidence exists
paper evidence exists
current-sim or high-fidelity verdict exists
full ideal driver gate is complete
level3 self-ID is supported
```

## Follow-Up Route

M2901 registers exactly one bounded follow-up:

```text
m2902-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-materialization-preflight
```

M2902 is admitted to materialize the designed panel accounting artifacts from
existing repository-local sources only. It must preserve all actor, target,
split, holdout, source-singleton, guard, and claim boundaries and register a
result-audit manifest before any model-quality or paper route.
