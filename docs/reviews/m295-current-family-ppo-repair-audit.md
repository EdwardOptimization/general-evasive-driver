# m295-current-family-ppo-repair-audit Research Review

## Summary

- Generated at UTC: 20260523T002232Z
- Type: gate
- Gate tier: process
- Promotion decision: design_direct_current_family_rejected_history_margin_preference_objective
- Decision reason: M295 finds M294 trajectory-anchor pressure partially restores row 11 but still fails rows 6 15 16 and worsens exact M270 more than M291 so next repair must target wrong-history margin/preference directly

## Hypothesis

M294 shows trajectory-anchor pressure helps M267 retention but is the wrong control variable for exact M270; the next repair needs a direct current-family rejected-history margin/preference objective.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt, runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt, runs/ppo_m294_current_family_rejected_repair_smoke_seed5232/checkpoint.pt
- parent_dataset: runs/m292_m291_ppo_proof_washout_audit/failed_m267_m264_rows.csv, runs/m294_current_family_rejected_repair_ppo_smoke/gates/raw_m267_m264/boundary_replay_rows.csv, runs/m294_current_family_rejected_repair_ppo_smoke/interpolation/alpha_summary.csv
- parent_config: configs/ppo_m291_row16_aware_guarded_smoke.json, configs/ppo_m294_current_family_rejected_repair_smoke.json, experiments/manifests/m294-current-family-rejected-repair-ppo-smoke.json, docs/m294-current-family-rejected-repair-ppo-smoke.md
- parent_objective: audit why stronger rejected-history anchoring partially fixes M267 but worsens exact M270
- derived_from: m294-current-family-rejected-repair-ppo-smoke
- blocked_by: m294-current-family-rejected-repair-ppo-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- explain why M294 recovers one M267 row but worsens exact M270
- classify the failure cause
- select the next repair strategy without running PPO
- pre-register a follow-up only if the repair is concrete

## Failure Criteria

- audit cannot explain the M291 to M294 difference
- audit recommends another PPO without a changed mechanism
- PPO is run
- actor observation inputs change

## Evidence Gates

- do not run PPO
- compare M291 and M294 failed current-family rows
- audit exact M270 regression versus M267 retention
- decide whether the next repair needs a new objective rather than stronger trajectory anchoring

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not start another PPO run in M295
- do not promote M294
- do not change actor inputs
- do not keep increasing anchor pressure without explaining exact M270 regression

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m295-current-family-ppo-repair-audit
- type: gate
- checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: design_direct_current_family_rejected_history_margin_preference_objective
- reason: M295 finds M294 trajectory-anchor pressure partially restores row 11 but still fails rows 6 15 16 and worsens exact M270 more than M291 so next repair must target wrong-history margin/preference directly

## Next Blocker

m296 current-family rejected-history margin/preference objective design before any further PPO
