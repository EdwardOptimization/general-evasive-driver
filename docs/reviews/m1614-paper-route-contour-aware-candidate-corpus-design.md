# m1614-paper-route-contour-aware-candidate-corpus-design Research Review

## Summary

- Generated at UTC: 20260529T181202Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_candidate_corpus_design_admit_offline_export
- Decision reason: M1614 designs candidate corpus package roles and metadata while blocking training corpus export objective construction training PPO and promotion

## Hypothesis

A design-only corpus plan can preserve candidate and diagnostic roles before any corpus export or training.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1612_contour_aware_candidate_materialization/summary.json, runs/m1612_contour_aware_candidate_materialization/candidate_rows.csv, runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_rows.csv, docs/m1613-paper-route-contour-aware-candidate-materialization-result-audit.md
- parent_config: experiments/manifests/m1613-paper-route-contour-aware-candidate-materialization-result-audit.json
- parent_objective: design contour-aware candidate corpus after materialization audit
- derived_from: m1613-paper-route-contour-aware-candidate-materialization-result-audit
- blocked_by: M1613 admits design-only corpus planning but blocks actual corpus export and training
- supersedes: direct corpus export from M1612, direct actor update from M1612, direct PPO after M1612
- invalidates: None

## Success Criteria

- docs/m1614-paper-route-contour-aware-candidate-corpus-design.md exists
- candidate and diagnostic roles are explicit
- public-proof and no-paper-claim metadata are explicit
- post-export audit requirement is explicit
- training PPO promotion private holdout corpus export and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design exports a corpus or constructs a loss
- design treats diagnostic rows as positive candidates
- design routes directly to training PPO promotion private holdout corpus export actor-input changes

## Evidence Gates

- M1614 must design corpus assembly without exporting a corpus
- M1614 must keep candidate and diagnostic roles separate
- M1614 must define public-proof metadata and no-paper-claim metadata
- M1614 must require corpus-export audit before actor update or PPO
- M1614 must keep training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not export a training corpus
- do not construct a loss
- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun replay
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not include diagnostic rows as positive candidates
- do not relax clean selector thresholds
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1614-paper-route-contour-aware-candidate-corpus-design
- type: gate
- checkpoint: docs/m1614-paper-route-contour-aware-candidate-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_candidate_corpus_design_admit_offline_export
- reason: M1614 designs candidate corpus package roles and metadata while blocking training corpus export objective construction training PPO and promotion

## Next Blocker

m1615-paper-route-contour-aware-candidate-corpus-export-implementation
