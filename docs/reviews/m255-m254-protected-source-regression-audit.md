# m255-m254-protected-source-regression-audit Research Review

## Summary

- Generated at UTC: 20260522T151059Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_post_ppo_protected_source_projection
- Decision reason: M255 shows M248 and M254 share the same protected-key regression sign under PPO; starting from M253 lowers baseline loss but does not solve the PPO direction conflict

## Hypothesis

M248 and M254 share a persistent PPO-gradient conflict: source-balanced PPO improves the broad M223 source while regressing the protected-key source, so the next repair needs a stronger lexicographic projection or hard protected-source constraint rather than another plain PPO smoke.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt, runs/ppo_m254_exact_source_from_m253_seed5225/checkpoint.pt, runs/ppo_m248_source_balanced_from_m239_seed5224/checkpoint.pt
- parent_dataset: runs/m254_source_aware_exact_m232_eval/source_summary.csv, runs/m248_source_aware_exact_m232_eval/source_summary.csv
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json, docs/m254-exact-source-gated-ppo-smoke-from-m253.md
- parent_objective: audit persistent protected-key source regression under PPO
- derived_from: m254-exact-source-gated-ppo-smoke-from-m253
- blocked_by: m254-exact-source-gated-ppo-smoke-from-m253
- supersedes: None
- invalidates: None

## Success Criteria

- compare M248 and M254 protected-key and M223 source slopes
- audit train-time source metrics against exact source deltas
- classify whether the failure is base-specific or PPO-direction persistent
- choose one bounded repair before more PPO
- no PPO is run

## Failure Criteria

- run PPO before the audit decision
- treat aggregate exact loss as sufficient despite protected-key regression
- change actor inputs
- leave the next blocker ambiguous

## Evidence Gates

- M248 versus M254 source-delta comparison
- PPO train metric audit
- repair decision before more PPO
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run more PPO before the audit
- do not tune from private holdouts
- do not ignore protected-key source deltas
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m255-m254-protected-source-regression-audit
- type: gate
- checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_post_ppo_protected_source_projection
- reason: M255 shows M248 and M254 share the same protected-key regression sign under PPO; starting from M253 lowers baseline loss but does not solve the PPO direction conflict

## Next Blocker

Run a no-PPO protected-source projection from the M254 raw PPO checkpoint, then exact-source-gate and interpolate if needed.
