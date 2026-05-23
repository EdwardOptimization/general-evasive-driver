# m310-fresh-ppo-proposal-exact-repair-smoke Research Review

## Summary

- Generated at UTC: 20260523T051029Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m311_full_public_gate_for_m310_repaired_ppo_proposal
- Decision reason: Raw PPO regresses exact M297/M270 but exact repair improves both versus M307 and passes M183/M170 plus M267/M264 first replay gates

## Hypothesis

A fresh smoke-scale PPO proposal from the M307 base can provide useful movement if it is accepted only through exact M297/M270 post-PPO repair before replay gates.

## Lineage

- parent_checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: configs/ppo_m310_exact_repaired_proposal_smoke.json, experiments/manifests/m309-exact-repaired-ppo-proposal-design.json, docs/m309-exact-repaired-ppo-proposal-design.md
- parent_objective: run one fresh smoke-scale PPO proposal from M307 and accept only an exact-repaired candidate
- derived_from: m309-exact-repaired-ppo-proposal-design
- blocked_by: m309-exact-repaired-ppo-proposal-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO run completes from M307 base
- exact repair candidate improves or retains exact M297 versus M307
- exact repair candidate improves or retains exact M270 versus M307
- exact repair candidate passes M183/M170 first replay gate versus M307
- exact repair candidate passes M267/M264 first replay gate versus M307
- if all first gates pass, admit a separate full public-gate milestone

## Failure Criteria

- raw PPO cannot run or checkpoint is incompatible
- repaired candidate regresses exact M297 or exact M270
- repaired candidate loses M183/M170 or M267/M264 first replay retention
- repair collapses to base-equivalent no-op and provides no useful movement
- actor input contract is changed

## Evidence Gates

- preserve human-view actor input contract
- run smoke PPO from M307 only as a raw proposal
- run exact post-PPO repair from raw proposal
- exact M297 repaired candidate loss must not regress versus M307
- exact M270 repaired candidate loss must not regress versus M307
- M183/M170 first replay gate versus M307
- M267/M264 first replay gate versus M307
- do not run full public gate unless exact and first replay gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote raw PPO checkpoint
- do not run replay for exact-regressing repaired candidates
- do not change actor inputs
- do not tune from private holdouts
- do not skip M297 or M270 exact no-regression gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m310-fresh-ppo-proposal-exact-repair-smoke
- type: driver_candidate
- checkpoint: runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m311_full_public_gate_for_m310_repaired_ppo_proposal
- reason: Raw PPO regresses exact M297/M270 but exact repair improves both versus M307 and passes M183/M170 plus M267/M264 first replay gates

## Next Blocker

m311-full-public-gate-for-m310-repaired-ppo-proposal
