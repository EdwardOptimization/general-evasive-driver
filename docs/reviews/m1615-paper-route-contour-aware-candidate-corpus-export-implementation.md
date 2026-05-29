# m1615-paper-route-contour-aware-candidate-corpus-export-implementation Research Review

## Summary

- Generated at UTC: 20260529T181636Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: contour_aware_candidate_corpus_export_public_pass_route_to_audit
- Decision reason: M1615 exports candidate corpus package metadata with 39 positives 232 diagnostics and no training corpus loss objective config

## Hypothesis

A candidate corpus package can be exported with explicit public-proof metadata while keeping training corpus export and objective construction blocked.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1612_contour_aware_candidate_materialization/candidate_rows.csv, runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_rows.csv, docs/m1614-paper-route-contour-aware-candidate-corpus-design.md
- parent_config: experiments/manifests/m1614-paper-route-contour-aware-candidate-corpus-design.json
- parent_objective: offline export contour-aware candidate corpus package without training corpus export
- derived_from: m1614-paper-route-contour-aware-candidate-corpus-design
- blocked_by: M1614 admits one offline candidate corpus package export
- supersedes: direct training-corpus export, direct objective construction, direct PPO
- invalidates: None

## Success Criteria

- runs/m1615_contour_aware_candidate_corpus/summary.json exists
- candidate_corpus_exported == true
- training_corpus_exported == false
- loss_constructed == false
- objective_constructed == false
- positive_candidate_count == 39
- diagnostic_guardrail_count == 232
- positive_rows_all_clean == true
- diagnostic_rows_used_as_positive == false
- candidate_pair_ids_unique == true
- diagnostic_pair_ids_unique == true
- source_edge_count == 4
- max_source_edge_share <= 0.35
- public_proof_metadata_complete == true
- requires_export_audit == true
- requires_objective_design_before_training == true
- training PPO promotion private holdout and self-ID claims remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- implementation or artifacts are missing
- implementation exports training_corpus.csv
- implementation constructs a loss or objective
- diagnostic rows enter positive candidates
- implementation claims level3 self-identification
- implementation fails to route to audit

## Evidence Gates

- M1615 must export a candidate corpus package, not a training corpus
- M1615 must keep positive candidates and diagnostic guardrails separate
- M1615 must write public-proof and no-paper-claim metadata
- M1615 must keep loss construction, training, PPO, promotion, and private holdout blocked
- M1615 must route to audit whether gates pass or fail

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export training_corpus.csv
- do not construct a loss
- do not construct an objective
- do not train
- do not run PPO
- do not rerun replay
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not include diagnostic rows as positive candidates
- do not claim level3 self-identification

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m1615-paper-route-contour-aware-candidate-corpus-export-implementation
- type: infrastructure
- checkpoint: runs/m1615_contour_aware_candidate_corpus/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_candidate_corpus_export_public_pass_route_to_audit
- reason: M1615 exports candidate corpus package metadata with 39 positives 232 diagnostics and no training corpus loss objective config

## Next Blocker

m1616-paper-route-contour-aware-candidate-corpus-export-result-audit
