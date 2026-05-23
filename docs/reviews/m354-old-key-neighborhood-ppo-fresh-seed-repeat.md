# m354-old-key-neighborhood-ppo-fresh-seed-repeat Research Review

## Summary

- Generated at UTC: 20260523T104524Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_m354_exact_m270_regression
- Decision reason: M354 raw PPO completes but exact repair improves M297 while regressing M270 by 0.000040591 so source-diverse old-key and replay gates are skipped

## Hypothesis

A fresh-seed short PPO proposal from the M352 public base may repeat the M351 proof-preserving pattern before any longer PPO escalation.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
- parent_dataset: runs/m352_full_public_gate_for_m351_a0075/summary.json, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m354_old_key_neighborhood_repeat.json, experiments/manifests/m353-old-key-neighborhood-ppo-fresh-seed-repeat-design.json, docs/m353-old-key-neighborhood-ppo-fresh-seed-repeat-design.md
- parent_objective: run fresh-seed repeat short PPO proposal from M352 base with exact repair and old-key neighborhood acceptance
- derived_from: m353-old-key-neighborhood-ppo-fresh-seed-repeat-design
- blocked_by: m353-old-key-neighborhood-ppo-fresh-seed-repeat-design
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO completes as proposal-only
- exact repair candidate does not regress exact M297/M270 versus M352
- selected candidate passes source-diverse protected gates
- selected candidate passes old-key neighborhood replay gate
- selected candidate passes M183/M170 and M267/M264 first replay gates
- research validation passes

## Failure Criteria

- raw PPO cannot run
- exact repair regresses M297 or M270
- source-diverse protected gate fails
- old-key neighborhood gate fails without a passing interpolation
- first replay gate fails
- actor input contract changes

## Evidence Gates

- raw PPO is proposal-only
- exact M297 and exact M270 no-regression versus M352
- source-diverse protected gate pass
- old-key neighborhood replay gate pass
- M183/M170 and M267/M264 first replay gates pass before any full public gate
- do not promote directly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote raw PPO
- do not skip exact repair
- do not skip old-key neighborhood targeted replay
- do not use singleton 9944 as the only old-key gate
- do not change actor inputs

## Failure Taxonomy

- objective_overfit

## Scoreboard

- milestone: m354-old-key-neighborhood-ppo-fresh-seed-repeat
- type: driver_candidate
- checkpoint: runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m354_exact_m270_regression
- reason: M354 raw PPO completes but exact repair improves M297 while regressing M270 by 0.000040591 so source-diverse old-key and replay gates are skipped

## Next Blocker

m355-m354-exact-m270-regression-audit
