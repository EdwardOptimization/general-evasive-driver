# m330-source-diverse-ppo-fresh-seed-repeat Research Review

## Summary

- Generated at UTC: 20260523T064953Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_m330_old_key_gap_floor_failure
- Decision reason: M330 exact and 4/4 source-diverse gates pass but old-key gap falls to 0.086901 below 0.09 so first replay is skipped and candidate is rejected pending audit

## Hypothesis

A fresh PPO seed from the M328 source-diverse public base can repeat the M327 pattern: exact repair, source-diverse protected proof, old-key singleton-window audit, and first replay gates all pass before any longer PPO.

## Lineage

- parent_checkpoint: runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
- parent_dataset: runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m330_source_diverse_protected_repeat_smoke.json, experiments/manifests/m329-source-diverse-ppo-fresh-seed-repeat-design.json, docs/m329-source-diverse-ppo-fresh-seed-repeat-design.md
- parent_objective: run fresh-seed source-diverse protected PPO smoke repeat from M328 base
- derived_from: m329-source-diverse-ppo-fresh-seed-repeat-design
- blocked_by: m329-source-diverse-ppo-fresh-seed-repeat-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO completes and writes checkpoint
- exact repair completes
- repaired candidate does not regress exact M297 or exact M270 versus M328
- source-diverse protected bundle passes
- old 9944 diagnostic is reported and classified
- M183/M170 and M267/M264 first replay gates pass
- actor input contract remains unchanged

## Failure Criteria

- raw PPO crashes
- exact repair fails or exact objectives regress
- source-diverse protected replay fails
- old-key failure is not singleton-window-only
- first replay gate fails
- actor observation inputs change

## Evidence Gates

- raw PPO is proposal only
- exact M297 and exact M270 no-regression versus M328 after repair
- source-diverse protected replay bundle passes
- old 9944 diagnostic is classified explicitly
- M183/M170 first replay gate versus M328
- M267/M264 first replay gate versus M328
- no promotion in M330

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from M330
- do not skip exact repair
- do not skip source-diverse protected gates
- do not delete 9944 diagnostic
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- protected_key_window_failure

## Scoreboard

- milestone: m330-source-diverse-ppo-fresh-seed-repeat
- type: driver_candidate
- checkpoint: runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m330_old_key_gap_floor_failure
- reason: M330 exact and 4/4 source-diverse gates pass but old-key gap falls to 0.086901 below 0.09 so first replay is skipped and candidate is rejected pending audit

## Next Blocker

m331-m330-old-key-gap-floor-failure-audit
