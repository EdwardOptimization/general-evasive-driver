# m335-short-source-diverse-ppo-escalation-run Research Review

## Summary

- Generated at UTC: 20260523T071813Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m336_full_public_gate_for_m335_a0075
- Decision reason: M335 short PPO exact repair improves objectives but old-key floor clips accepted movement to alpha 0.0075; exact source-diverse and first replay gates pass

## Hypothesis

A 4096-step short PPO escalation from the M333 source-diverse public base can provide useful proposal movement while retaining exact objectives, source-diverse protected proof, old-key gap floor, and first replay gates after exact repair or bounded interpolation.

## Lineage

- parent_checkpoint: runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
- parent_dataset: runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m335_short_source_diverse_escalation.json, experiments/manifests/m334-short-source-diverse-ppo-escalation-design.json, docs/m334-short-source-diverse-ppo-escalation-design.md
- parent_objective: run short source-diverse protected PPO escalation from M333 base with exact repair and bounded first proof gates
- derived_from: m334-short-source-diverse-ppo-escalation-design
- blocked_by: m334-short-source-diverse-ppo-escalation-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO completes and writes checkpoint
- exact repair completes
- selected candidate does not regress exact M297 or exact M270 versus M333
- source-diverse protected bundle passes
- old 9944 margin gap is reported and remains at least 0.09 for the selected candidate
- M183/M170 and M267/M264 first replay gates pass
- actor input contract remains unchanged

## Failure Criteria

- raw PPO crashes
- exact repair fails or exact objectives regress
- source-diverse protected replay fails
- no endpoint or bounded interpolation candidate keeps old-key margin gap >= 0.09
- first replay gate fails
- actor observation inputs change

## Evidence Gates

- raw PPO is proposal only
- exact M297 and exact M270 no-regression versus M333 after repair
- source-diverse protected replay bundle passes
- old 9944 margin gap remains at least 0.09 or bounded interpolation selects an alpha that does
- M183/M170 first replay gate versus M333
- M267/M264 first replay gate versus M333
- no promotion in M335

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from M335
- do not skip exact repair
- do not skip source-diverse protected gates
- do not lower the old-key gap floor
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m335-short-source-diverse-ppo-escalation-run
- type: driver_candidate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m336_full_public_gate_for_m335_a0075
- reason: M335 short PPO exact repair improves objectives but old-key floor clips accepted movement to alpha 0.0075; exact source-diverse and first replay gates pass

## Next Blocker

m336-full-public-gate-for-m335-a0075
