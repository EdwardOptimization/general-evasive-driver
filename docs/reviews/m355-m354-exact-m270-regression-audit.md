# m355-m354-exact-m270-regression-audit Research Review

## Summary

- Generated at UTC: 20260523T105256Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m356_exact_repair_best_step_selection
- Decision reason: M355 shows the M354 raw PPO proposal had a feasible 39-step exact repair state; the saved 40-step endpoint failed because final-step checkpoint selection crossed the M270 boundary after pre-update metrics were logged

## Hypothesis

M354 may have failed because the exact repair objective overfit M297 while allowing M270 to regress, so the next step should audit the exact repair traces and decide whether a M270-dominant repair or different line search is needed.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt
- parent_dataset: runs/m354_old_key_neighborhood_ppo_fresh_seed_repeat/summary.json, runs/m354_exact_repair_from_raw_s40_seed10103/summary.json, runs/ppo_m354_old_key_neighborhood_repeat_seed5240/eval_summary.json
- parent_config: experiments/manifests/m354-old-key-neighborhood-ppo-fresh-seed-repeat.json, docs/m354-old-key-neighborhood-ppo-fresh-seed-repeat.md
- parent_objective: audit why M354 exact repair improved M297 but regressed M270
- derived_from: m354-old-key-neighborhood-ppo-fresh-seed-repeat
- blocked_by: m354-old-key-neighborhood-ppo-fresh-seed-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- audit document identifies the immediate failure mode
- audit states whether M354 should be retried with altered exact repair or archived
- audit does not run PPO or promotion gates
- research validation passes

## Failure Criteria

- audit treats M354 as promotable
- audit runs downstream gates on a lexicographic-failing candidate
- audit changes actor inputs
- research validation fails

## Evidence Gates

- audit only; no PPO run
- do not run downstream replay gates for rejected candidate
- classify M270 regression before another PPO attempt
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat M354 as a candidate
- do not skip the M270 regression audit
- do not run longer PPO from M352 before audit
- do not change actor inputs

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m355-m354-exact-m270-regression-audit
- type: gate
- checkpoint: runs/m355_m354_repair_step39_diagnostic/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m356_exact_repair_best_step_selection
- reason: M355 shows the M354 raw PPO proposal had a feasible 39-step exact repair state; the saved 40-step endpoint failed because final-step checkpoint selection crossed the M270 boundary after pre-update metrics were logged

## Next Blocker

m356-exact-repair-best-step-selection-implementation
