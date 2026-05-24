# m544-l3-variance-recipe-failure-audit Research Review

## Summary

- Generated at UTC: 20260524T035635Z
- Type: gate
- Gate tier: proof
- Promotion decision: l3_recipe_failure_confirmed_admit_m545_recurrent_recipe_repair_design
- Decision reason: M544 confirms current L3 recipe instability: valid contract but early training peak collapses and M543 L3-L2 public deltas are strongly negative

## Hypothesis

The M543 L3 regression is likely a recurrent recipe or optimization failure, not evidence against command-response history itself; a focused audit should identify whether L3 needs recipe repair before more training.

## Lineage

- parent_checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m542_matched_l3_variance_seed3540/checkpoint.pt, runs/m533_matched_l2_short_train_seed3531/checkpoint.pt, runs/m533_matched_l3_short_train_seed3531/checkpoint.pt
- parent_dataset: runs/m543_m542_public_surface_eval_aggregate/summary.json, runs/m539_matched_history_seed_fragility_audit/summary.json
- parent_config: configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json, configs/ppo_m531_matched_l2_short_train.json, configs/ppo_m531_matched_l3_short_train.json
- parent_objective: diagnose why current L3 recurrent recipe regresses while L2 finite window remains strong
- derived_from: m543-m542-public-surface-eval, m539-matched-history-seed-fragility-audit
- blocked_by: m543-m542-public-surface-eval
- supersedes: None
- invalidates: None

## Success Criteria

- config and metadata differences between L2 and L3 are enumerated
- train metric and route eval differences are summarized
- public surface failure pattern is linked to candidate causes
- next decision is explicit: repair L3 recipe, expand L2 baseline, or run controlled ablation
- research validation passes

## Failure Criteria

- audit treats L3 regression as final without checking recipe path
- audit launches training before documenting the blocker
- public diagnostics are treated as private evidence

## Evidence Gates

- compared L3 and L2 config/training metadata
- compared train metric trajectories and eval summaries
- inspected whether recurrent_sequence_training or hidden-state handling creates an optimization disadvantage
- decided to design L3 recurrent recipe repair while keeping L2 as the strong baseline
- did not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not hide the M543 L3 regression
- do not expand L3 multi-seed runs before diagnosing recipe failure
- do not tune from public rows and report the same rows as private evidence

## Failure Taxonomy

- training_instability

## Scoreboard

- milestone: m544-l3-variance-recipe-failure-audit
- type: gate
- checkpoint: runs/m544_l3_variance_recipe_failure_audit/summary.json
- success_rate: -0.195633
- termination_rate: None
- clearance_margin_mean: -0.793024
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l3_recipe_failure_confirmed_admit_m545_recurrent_recipe_repair_design
- reason: M544 confirms current L3 recipe instability: valid contract but early training peak collapses and M543 L3-L2 public deltas are strongly negative

## Next Blocker

m545-l3-recurrent-recipe-repair-design
