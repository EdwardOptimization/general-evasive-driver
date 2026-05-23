# m366-alpha02-old-key-regression-audit Research Review

## Summary

- Generated at UTC: 20260523T114921Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m367_old_key_hard_row_weighting_design
- Decision reason: M366 classifies alpha 0.2 failure as one wrong-history terminal-margin sign crossing on case 9951 perturbed; no threshold lowering or PPO

## Hypothesis

The alpha 0.2 old-key failure may be localized to a single hard row that should become an explicit repair weight or constraint before trying to enlarge the old-key-aware repair step.

## Lineage

- parent_checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt, runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt
- parent_dataset: runs/m364_old_key_aware_repair_alpha02_old_key_replay_gate/summary.json, runs/m364_old_key_aware_repair_interpolation_old_key_targeted_replay/guard_results.csv
- parent_config: experiments/manifests/m365-full-public-gate-for-m364-alpha01.json
- parent_objective: audit the single old-key accepted regression at alpha 0.2 before another repair or PPO step
- derived_from: m365-full-public-gate-for-m364-alpha01
- blocked_by: m365-full-public-gate-for-m364-alpha01
- supersedes: None
- invalidates: None

## Success Criteria

- audit identifies the failing compact row and its margin deltas
- audit recommends hard-row weighting, constraint design, or stopping this branch
- no PPO is run
- research validation passes

## Failure Criteria

- audit ignores the alpha 0.2 accepted regression
- audit changes acceptance thresholds to pass alpha 0.2
- actor input contract changes
- research validation fails

## Evidence Gates

- process audit only; no PPO run
- identify alpha 0.2 old-key failing row
- compare alpha 0.1 and alpha 0.2 guard deltas
- decide whether to add hard-row weighting or constraint terms
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote alpha 0.2
- do not lower old-key replay acceptance thresholds
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m366-alpha02-old-key-regression-audit
- type: gate
- checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m367_old_key_hard_row_weighting_design
- reason: M366 classifies alpha 0.2 failure as one wrong-history terminal-margin sign crossing on case 9951 perturbed; no threshold lowering or PPO

## Next Blocker

m367-old-key-hard-row-weighting-design
