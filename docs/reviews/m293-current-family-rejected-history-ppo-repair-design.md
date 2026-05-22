# m293-current-family-rejected-history-ppo-repair-design Research Review

## Summary

- Generated at UTC: 20260522T200543Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m294_current_family_rejected_repair_smoke
- Decision reason: M293 exports failed-row extra4 trajectory anchor and M294 config with stronger M267/M264 retention plus exact M270 no-regression gate

## Hypothesis

The next PPO smoke needs explicit M267/M264 rejected-history retention and exact M270 no-regression, not only baseline action anchoring.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt, runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt
- parent_dataset: runs/m292_m291_ppo_proof_washout_audit/failed_m267_m264_rows.csv, runs/m289_row16_aware_balanced_repeat_calibration/anchors/row16_extra64_combined_anchor.npz
- parent_config: configs/ppo_m291_row16_aware_guarded_smoke.json, experiments/manifests/m292-m291-ppo-proof-washout-audit.json, docs/m292-m291-ppo-proof-washout-audit.md
- parent_objective: design a PPO repair that protects current-family rejected-history rows and fixed M270 objective
- derived_from: m292-m291-ppo-proof-washout-audit
- blocked_by: m292-m291-ppo-proof-washout-audit
- supersedes: None
- invalidates: None

## Success Criteria

- document a concrete repair recipe
- identify required corpora and anchors
- define first gates and promotion criteria
- pre-register the next runnable milestone without executing PPO

## Failure Criteria

- repair recipe does not address M267/M264 wrong-history washout
- repair recipe omits fixed M270 no-regression
- PPO is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- design current-family rejected-history retention before the next PPO smoke
- include exact M270 no-regression as a gate
- keep M183/M170 row16 and M267/M264 first gates
- pre-register the next executable PPO attempt only after the design is explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M293
- do not promote m291_a100
- do not change actor inputs
- do not treat lower learning rate alone as sufficient without rejected-history protection

## Failure Taxonomy

- none

## Scoreboard

- milestone: m293-current-family-rejected-history-ppo-repair-design
- type: infrastructure
- checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m294_current_family_rejected_repair_smoke
- reason: M293 exports failed-row extra4 trajectory anchor and M294 config with stronger M267/M264 retention plus exact M270 no-regression gate

## Next Blocker

m294-current-family-rejected-repair-ppo-smoke
