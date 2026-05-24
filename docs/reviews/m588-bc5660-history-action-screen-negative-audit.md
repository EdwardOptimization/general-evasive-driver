# m588-bc5660-history-action-screen-negative-audit Research Review

## Summary

- Generated at UTC: 20260524T070938Z
- Type: gate
- Gate tier: process
- Promotion decision: bc5660_history_action_screen_negative_admit_hidden_use_objective_audit
- Decision reason: M588 confirms M587 is a real negative hidden-history action diagnostic and redirects to BC hidden-use objective audit before any training or outcome rollout

## Hypothesis

Because wrong_matched_history and delayed_history have no above-threshold action rows on both M586 surfaces, BC5660 likely transferred L2 behavior without using accumulated online-GRU hidden state; the next step should audit training/objective or surface choices rather than force outcome rollout.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m587_bc5660_history_action_screen_fresh_seed25560/variant_summary.csv, runs/m587_bc5660_history_action_screen_ood_seed25660/variant_summary.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: audit negative wrong/delayed-history action screen before any outcome rollout or training
- derived_from: m587-bc5660-history-intervention-action-screen
- blocked_by: m587-bc5660-history-intervention-action-screen
- supersedes: None
- invalidates: m588-bc5660-persistent-history-outcome-gate

## Success Criteria

- audit summarizes M587 negative wrong/delayed action results and positive controls
- audit explains why persistent outcome rollout is blocked
- audit selects the next research branch with a pre-registered blocker
- research validation passes

## Failure Criteria

- audit overclaims self-ID from zero-current or zero-action sensitivity
- audit proceeds to outcome rollout despite action-screen rejection
- audit starts training without pre-registering the objective problem
- audit promotes a checkpoint

## Evidence Gates

- audit M587 wrong/delayed action-screen failure
- separate current-response and previous-command sensitivity from hidden-history sensitivity
- decide whether the next path is training-objective repair, alternate surface mining, or alternate checkpoint-family testing
- do not run persistent outcome rollout without action-screen admission
- do not train update or promote a checkpoint in audit milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not reinterpret zero-current action sensitivity as wrong-history sensitivity
- do not run persistent outcome gate after action-screen rejection without a new manifest
- do not change actor inputs
- do not run PPO or behavior cloning
- do not promote checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m588-bc5660-history-action-screen-negative-audit
- type: gate
- checkpoint: docs/m588-bc5660-history-action-screen-negative-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc5660_history_action_screen_negative_admit_hidden_use_objective_audit
- reason: M588 confirms M587 is a real negative hidden-history action diagnostic and redirects to BC hidden-use objective audit before any training or outcome rollout

## Next Blocker

m589-bc-hidden-use-objective-audit
