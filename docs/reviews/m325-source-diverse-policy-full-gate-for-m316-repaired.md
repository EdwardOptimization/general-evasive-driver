# m325-source-diverse-policy-full-gate-for-m316-repaired Research Review

## Summary

- Generated at UTC: 20260523T062806Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m316_repaired_source_diverse_public_gate_base
- Decision reason: M325 promotes M316 repaired under source-diverse protected policy with exact objectives improved plus 2/2 source-diverse gates pass plus 6/6 replay gates pass plus 9944 singleton-window saturation gap 0.096982 plus behavior seeds retain

## Hypothesis

The M316 repaired endpoint may be promotable under the M324 source-diverse protected policy if it passes exact objectives, source-diverse protected proof, six replay surfaces, behavior seeds, and the old 9944 conflict is classified as single-key window saturation.

## Lineage

- parent_checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt, runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- parent_dataset: runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m316_protected_key_sweep/guard_results.csv
- parent_config: experiments/manifests/m324-single-key-window-override-policy-design.json, docs/m324-single-key-window-override-policy-design.md
- parent_objective: run full public gate for M316 repaired endpoint under source-diverse protected policy
- derived_from: m324-single-key-window-override-policy-design
- blocked_by: m324-single-key-window-override-policy-design
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes exact M297 and exact M270 no-regression versus M317
- candidate passes source-diverse protected replay bundle
- old 9944 diagnostic is reported and classified
- candidate passes all six public replay gates versus M317
- candidate retains behavior on seeds 9505 and 9506
- actor input contract remains unchanged

## Failure Criteria

- exact M297 or exact M270 regresses
- source-diverse protected replay fails
- old 9944 failure is not singleton-window-only
- any public replay gate fails
- behavior seeds materially regress
- actor observation inputs change

## Evidence Gates

- exact M297 and exact M270 no-regression versus M317 public-gate base
- source-diverse protected replay bundle passes
- old 9944 diagnostic is classified explicitly
- M183/M168 replay gate versus M317
- M183/M170 replay gate versus M317
- M193/M189 replay gate versus M317
- M212/M204 replay gate versus M317
- M223/M219 replay gate versus M317
- M267/M264 replay gate versus M317
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote because source-diverse gate alone passes
- do not delete or hide 9944 diagnostic
- do not run PPO
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m325-source-diverse-policy-full-gate-for-m316-repaired
- type: driver_candidate
- checkpoint: runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_m316_repaired_source_diverse_public_gate_base
- reason: M325 promotes M316 repaired under source-diverse protected policy with exact objectives improved plus 2/2 source-diverse gates pass plus 6/6 replay gates pass plus 9944 singleton-window saturation gap 0.096982 plus behavior seeds retain

## Next Blocker

m326-source-diverse-protected-ppo-proposal-design
