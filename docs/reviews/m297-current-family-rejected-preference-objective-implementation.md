# m297-current-family-rejected-preference-objective-implementation Research Review

## Summary

- Generated at UTC: 20260523T004657Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: admit_no_ppo_rejected_preference_objective_only_probe
- Decision reason: M297 implements the rejected-history preference objective and exact sanity ranks M290 loss 1.191800 below M291raw 1.192550 and M294raw 1.192730 with focused diagnostics for rows 6 11 15 16

## Hypothesis

A rejected-history preference loss that includes a rejected action and margin labels will distinguish the M290 base from M291/M294 proof-washout checkpoints more directly than the current preferred-action-only outcome loss.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt, runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt, runs/ppo_m294_current_family_rejected_repair_smoke_seed5232/checkpoint.pt
- parent_dataset: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz, runs/m295_current_family_ppo_repair_audit/failed_row_comparison.csv
- parent_config: experiments/manifests/m296-current-family-rejected-margin-objective-design.json, docs/m296-current-family-rejected-margin-objective-design.md
- parent_objective: implement the direct rejected-history preference objective designed in M296
- derived_from: m296-current-family-rejected-margin-objective-design
- blocked_by: m296-current-family-rejected-margin-objective-design
- supersedes: None
- invalidates: None

## Success Criteria

- corpus exporter writes the M296 schema with rejected_action and row-level labels
- loader rejects malformed corpora and accepts the exported corpus
- exact evaluator reports finite losses for M290 M291 raw and M294 raw
- M290 exact loss is lower than both M291 raw and M294 raw on the M267/M264 preference corpus
- row 11 and rows 6 15 16 have per-row diagnostics

## Failure Criteria

- new loss cannot distinguish M290 from M291 or M294
- implementation duplicates the old action-anchor loss without pairwise preference
- PPO or actor update is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- preserve human-view actor input contract
- implement rejected-history preference corpus loader and loss
- evaluate M290 versus M291 raw and M294 raw on the new exact loss
- write unit tests for shape validation and finite loss

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train a driver in M297
- do not promote a checkpoint
- do not change actor inputs
- do not use hidden vehicle parameters as actor inputs
- do not skip per-row reports for rows 6 11 15 16

## Failure Taxonomy

- none

## Scoreboard

- milestone: m297-current-family-rejected-preference-objective-implementation
- type: objective_sanity
- checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_no_ppo_rejected_preference_objective_only_probe
- reason: M297 implements the rejected-history preference objective and exact sanity ranks M290 loss 1.191800 below M291raw 1.192550 and M294raw 1.192730 with focused diagnostics for rows 6 11 15 16

## Next Blocker

m298-rejected-preference-objective-only-probe
