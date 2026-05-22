# m292-m291-ppo-proof-washout-audit Research Review

## Summary

- Generated at UTC: 20260522T200228Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_current_family_rejected_history_ppo
- Decision reason: M292 finds raw M291 PPO makes M267/M264 rows 6 11 15 16 wrong-history safe by raising wrong-history margins; next repair must protect current-family rejected-history rows and exact M270

## Hypothesis

M291 raw PPO washes out M267/M264 because the PPO reward update overpowers current-family rejected-history retention while preserving old row16 margins.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt, runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt, runs/m291_row16_aware_guarded_ppo_smoke/interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m291_row16_aware_guarded_ppo_smoke/gates/raw_m267_m264/boundary_replay_rows.csv, runs/m291_row16_aware_guarded_ppo_smoke/interpolation/alpha_summary.csv
- parent_config: configs/ppo_m291_row16_aware_guarded_smoke.json, experiments/manifests/m291-row16-aware-guarded-ppo-smoke.json, docs/m291-row16-aware-guarded-ppo-smoke.md
- parent_objective: audit why raw smoke PPO worsens exact M270 and loses M267/M264 wrong-history drops
- derived_from: m291-row16-aware-guarded-ppo-smoke
- blocked_by: m291-row16-aware-guarded-ppo-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- identify which M267/M264 rows raw PPO makes safe
- compare action and terminal-margin changes for M290, m291_a100, and m291raw
- classify the failure cause using process-v2 taxonomy
- select the next repair strategy without running PPO

## Failure Criteria

- audit cannot explain the M267/M264 success-drop loss
- audit discovers metric or lineage inconsistency
- PPO is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- inspect raw M291 failed M267/M264 rows
- compare M290, m291_a100, and m291raw action/margin deltas
- identify whether washout comes from PPO reward, anchor weakness, or current-family rejected-history underweighting
- pre-register the next PPO repair only after the audit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not start another PPO run in M292
- do not promote m291_a100
- do not change actor inputs
- do not treat public behavior retention as enough when fixed M270 regresses

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m292-m291-ppo-proof-washout-audit
- type: gate
- checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: repair_current_family_rejected_history_ppo
- reason: M292 finds raw M291 PPO makes M267/M264 rows 6 11 15 16 wrong-history safe by raising wrong-history margins; next repair must protect current-family rejected-history rows and exact M270

## Next Blocker

m293-current-family-rejected-history-ppo-repair-design
