# m1612-paper-route-contour-aware-candidate-materialization-implementation Research Review

## Summary

- Generated at UTC: 20260529T180644Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: contour_aware_candidate_materialization_public_pass_route_to_audit
- Decision reason: M1612 materialized 39 candidate rows and 232 diagnostic guardrail rows without training corpus export and routes to audit

## Hypothesis

Offline candidate materialization can preserve M1609 clean primary rows and diagnostic guardrails without exporting a training corpus.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1609_diagnostic_complete_bounded_replay/primary_classified_rows.csv, runs/m1609_diagnostic_complete_bounded_replay/diagnostic_classified_rows.csv, docs/m1611-paper-route-contour-aware-candidate-materialization-design.md
- parent_config: experiments/manifests/m1611-paper-route-contour-aware-candidate-materialization-design.json
- parent_objective: offline materialize contour-aware public-pass candidate rows and diagnostic guardrails
- derived_from: m1611-paper-route-contour-aware-candidate-materialization-design
- blocked_by: M1611 admits exactly one offline candidate materialization implementation
- supersedes: direct training-corpus export from M1609, direct PPO after M1609, diagnostic rows entering candidate rows
- invalidates: None

## Success Criteria

- runs/m1612_contour_aware_candidate_materialization/summary.json exists
- candidate_directed_pair_count == 39
- candidate_source_edge_count == 4
- max_candidate_source_edge_share <= 0.35
- candidate_rows_from_primary_only == true
- candidate_rows_all_clean == true
- candidate_rows_missing_variants_count == 0
- candidate_pair_ids_unique == true
- diagnostic_guardrail_directed_pair_count == 232
- diagnostic_reason_count == 3
- diagnostic_dominated_or_control_count >= 75
- diagnostic_clean_share <= 0.02
- diagnostic_rows_enter_candidate_rows == false
- training_corpus_exported == false
- candidate_materialized == true
- candidate_materialization_only == true
- training PPO promotion private holdout corpus export and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- implementation exports a training corpus
- diagnostic rows enter candidate rows
- implementation changes actor inputs or uses private holdout
- implementation claims level3 self-identification
- implementation fails to route to audit

## Evidence Gates

- M1612 must materialize only candidate-row artifacts, not a training corpus
- M1612 must use only M1609 primary clean rows as candidates
- M1612 must carry all M1609 diagnostic rows as guardrails
- M1612 must preserve stable pair ids and source-edge accounting
- M1612 must keep training PPO promotion and private holdout blocked
- M1612 must route to audit whether gates pass or fail

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export a training corpus
- do not train
- do not run PPO
- do not rerun replay
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not include diagnostic rows in candidate rows
- do not select diagnostics by labels
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m1612-paper-route-contour-aware-candidate-materialization-implementation
- type: infrastructure
- checkpoint: runs/m1612_contour_aware_candidate_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_candidate_materialization_public_pass_route_to_audit
- reason: M1612 materialized 39 candidate rows and 232 diagnostic guardrail rows without training corpus export and routes to audit

## Next Blocker

m1613-paper-route-contour-aware-candidate-materialization-result-audit
