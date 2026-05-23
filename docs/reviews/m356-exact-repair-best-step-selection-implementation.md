# m356-exact-repair-best-step-selection-implementation Research Review

## Summary

- Generated at UTC: 20260523T105833Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m357_m354_best_step_repair_proof_gate
- Decision reason: M356 changes exact repair to log post-update metrics and save the best-feasible checkpoint; the M354 repair probe selects step 25 and passes exact M297/M270 while final step 40 still fails M270

## Hypothesis

The M354 M270 regression can be prevented at the infrastructure layer by making exact repair evaluate post-update losses and save the best lexicographically feasible checkpoint instead of the final optimizer step.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/ppo_m354_old_key_neighborhood_repeat_seed5240/checkpoint.pt
- parent_dataset: runs/m354_exact_repair_from_raw_s40_seed10103/train_metrics.csv, runs/m354_exact_repair_from_raw_s40_seed10103/summary.json, runs/m355_m354_repair_step39_diagnostic/summary.json
- parent_config: experiments/manifests/m355-m354-exact-m270-regression-audit.json, docs/m355-m354-exact-m270-regression-audit.md
- parent_objective: fix exact repair endpoint selection so feasible intermediate steps are not discarded
- derived_from: m355-m354-exact-m270-regression-audit
- blocked_by: m355-m354-exact-m270-regression-audit
- supersedes: None
- invalidates: None

## Success Criteria

- exact_post_ppo_repair records post-update metrics consistently with saved checkpoints
- exact_post_ppo_repair supports best-feasible checkpoint selection
- tests cover best-step selection and candidate-summary consistency
- research validation passes

## Failure Criteria

- implementation changes actor inputs
- implementation only changes documentation while leaving final-step selection unchanged
- tests do not exercise the M355 failure mode
- research validation fails

## Evidence Gates

- infrastructure only; no PPO run
- post-update exact metrics are logged for repair steps
- exact repair can select and save the best lexicographically feasible step
- candidate summary describes the saved selected checkpoint
- actor input contract remains unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote the M354 39-step diagnostic candidate
- do not run downstream replay gates before the tool fix is validated
- do not change actor inputs
- do not hide exact M270 regressions by relaxing tolerances

## Failure Taxonomy

- none

## Scoreboard

- milestone: m356-exact-repair-best-step-selection-implementation
- type: infrastructure
- checkpoint: runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m357_m354_best_step_repair_proof_gate
- reason: M356 changes exact repair to log post-update metrics and save the best-feasible checkpoint; the M354 repair probe selects step 25 and passes exact M297/M270 while final step 40 still fails M270

## Next Blocker

m357-m354-best-step-repair-proof-gate
