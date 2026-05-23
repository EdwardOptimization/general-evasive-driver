# m308-exact-repair-fresh-seed-repeat Research Review

## Summary

- Generated at UTC: 20260523T050120Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_exact_repaired_ppo_proposal_design
- Decision reason: M308 fresh repair repeat matches M306 exact deltas and passes M183/M170 plus M267/M264 first replay gates so optimizer seed fragility is not the blocker

## Hypothesis

The M306 exact repair projection recipe is not a single optimizer-seed accident and can repeat exact-objective improvement plus first replay retention with a fresh seed.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt, runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt, runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m307-full-public-gate-for-m306-raw-s40.json, docs/m307-full-public-gate-for-m306-raw-s40.md
- parent_objective: repeat the exact repair projection recipe with a fresh optimizer seed before more PPO proposals
- derived_from: m307-full-public-gate-for-m306-raw-s40
- blocked_by: m307-full-public-gate-for-m306-raw-s40
- supersedes: None
- invalidates: None

## Success Criteria

- fresh repair candidate improves or retains exact M297 versus M299
- fresh repair candidate improves or retains exact M270 versus M299
- fresh repair candidate passes M183/M170 and M267/M264 first replay gates
- document whether M307 promotion is seed-stable enough to admit another PPO proposal

## Failure Criteria

- fresh repair candidate regresses exact M297 or exact M270
- fresh repair candidate loses M183/M170 or M267/M264 first replay retention
- fresh repair movement collapses to a base-equivalent no-op
- actor input contract is changed

## Evidence Gates

- preserve human-view actor input contract
- repeat exact_post_ppo_repair from M302 raw with a fresh optimizer seed
- exact M297 candidate loss must not regress versus M299
- exact M270 candidate loss must not regress versus M299
- M183/M170 first replay gate
- M267/M264 first replay gate
- decide whether seed-repeat evidence is enough for another PPO proposal

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not assume M306 is seed-robust from one optimizer seed
- do not run long PPO before fresh repair repeat
- do not promote without exact and replay gates
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m308-exact-repair-fresh-seed-repeat
- type: driver_candidate
- checkpoint: runs/m308_exact_repair_from_raw_s40_seed10094/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_exact_repaired_ppo_proposal_design
- reason: M308 fresh repair repeat matches M306 exact deltas and passes M183/M170 plus M267/M264 first replay gates so optimizer seed fragility is not the blocker

## Next Blocker

m309-exact-repaired-ppo-proposal-design
