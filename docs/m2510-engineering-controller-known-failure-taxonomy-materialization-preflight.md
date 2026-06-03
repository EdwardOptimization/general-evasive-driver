# M2510 Engineering Controller Known Failure Taxonomy Materialization Preflight

- status: completed
- result_class: `engineering_controller_known_failure_taxonomy_materialization_pass`
- manifest: `experiments/manifests/m2510-engineering-controller-known-failure-taxonomy-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_failure_taxonomy.py`
- summary: `runs/m2510_engineering_controller_known_failure_taxonomy/summary.json`
- taxonomy CSV: `runs/m2510_engineering_controller_known_failure_taxonomy/failure_taxonomy.csv`
- next milestone: `m2511-engineering-controller-known-failure-taxonomy-result-audit`
- external high-fidelity simulation installed/imported/executed in M2510: `false`
- environment rollout/simulator step/policy rollout in M2510: `false`
- measured validation/training/replay/PPO/ranking/winner selection in M2510: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Taxonomy Artifact

M2510 materializes a structured known failure taxonomy from existing Route A
diagnostic artifacts. It does not run new simulation or policy rollout.

Generated artifacts:

```text
runs/m2510_engineering_controller_known_failure_taxonomy/summary.json
runs/m2510_engineering_controller_known_failure_taxonomy/failure_taxonomy.csv
```

Taxonomy schema:

```text
failure_id
failure_category
evidence_scope
evidence_type
source_artifact
source_milestone
severity
known_limitation
observed_evidence
route_implication
forbidden_interpretation
source_exists
```

## Summary Gates

Accepted summary:

```text
result_class: engineering_controller_known_failure_taxonomy_materialization_pass
status_pass: true
taxonomy_row_count: 10
expected_min_taxonomy_row_count: 8
required_fields_present: true
source_artifacts_exist: true
missing_source_artifacts: []
actor_contract_shape_72_action_3: true
source_only_diagnostic_scope: true
```

Failure categories:

```text
baseline_scope: 1
behavior_regression: 1
deployability_scope: 1
diagnostic_behavior_envelope: 1
metric_artifact: 2
objective_overfit: 1
scenario_sampling_failure: 1
self_id_evidence_gap: 1
validation_boundary: 1
```

Severity counts:

```text
high: 4
medium: 5
low: 1
```

## Taxonomy Rows

The materialized taxonomy covers:

```text
source_only_hf0_not_external_validation
fixed_public_fixture_scope
no_success_or_outcome_semantics
no_controller_ranking_or_winner
self_id_and_fw_vs_gru_unsupported
runtime_report_synthetic_observation_scope
behavior_regression_unmeasured
current_sim_readiness_not_resolved
large_lateral_envelope_outcome_unlabeled
open_loop_baselines_not_controller_candidates
```

These rows structure known limitations. They do not rank controllers or turn
diagnostic metrics into outcome verdicts.

## Blocked Execution And Claim Flags

```text
environment_rollout_run: false
simulator_step_run: false
external_high_fidelity_simulation_included: false
policy_action_run: false
policy_rollout_run: false
measured_validation_run: false
training_run: false
replay_run: false
ppo_run: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
controller_family_verdict_computed: false
driver_performance_claim_made: false
verdict_claim_made: false
paper_claim_made: false
finite_window_vs_gru_claim_made: false
level3_self_id_claim_made: false
current_sim_verdict_claim_made: false
high_fidelity_validation_claim_made: false
```

## Result

M2510 passes as a known failure taxonomy materialization preflight. It fills the
Route A known-limitation artifact from existing source-only diagnostics and
runtime artifacts while preserving the claim boundary.

## Next Route

Route to:

```text
m2511-engineering-controller-known-failure-taxonomy-result-audit
```

M2511 should audit the taxonomy rows, source references, and forbidden
interpretations before public export preparation or another engineering route.
