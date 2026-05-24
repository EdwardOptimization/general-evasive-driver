# m664-action-critical-wrong-history-source-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T141815Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: action_critical_wrong_history_source_miner_negative_admit_audit
- Decision reason: M664 finds larger wrong-history action gaps but accepts 0 rows because action-threshold rows are already normal-failed and no margin or success-drop gap appears

## Hypothesis

Action/outcome-first source mining over a broader snapshot bank can find source-diverse wrong-history pairs that M661's matched-current surfaces missed.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m663-action-critical-wrong-history-source-mining-design.md, runs/m661_action_divergent_wrong_history_corpus/summary.json
- parent_config: experiments/manifests/m663-action-critical-wrong-history-source-mining-design.json
- parent_objective: implement no-training action-critical wrong-history source miner
- derived_from: m663-action-critical-wrong-history-source-mining-design
- blocked_by: m663-action-critical-wrong-history-source-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- accepted rows >= 40
- accepted physical pairs >= 8
- accepted left seeds >= 6
- accepted right seeds >= 6
- source-heldout split is nonempty
- mean preferred_vs_rejected_action_mean_l2 >= 0.010
- mean margin_gap >= 0.010 or accepted success_drop_rate >= 0.25
- actor checksum unchanged
- no actor checkpoint written
- research validation passes

## Failure Criteria

- too few accepted rows
- action/outcome acceptance fails under scene compatibility constraints
- source diversity fails
- actor checksum changes
- actor checkpoint is written
- hidden-distance-only rows are accepted

## Evidence Gates

- build broader snapshot bank
- pair compatible current scenes with many candidate wrong histories
- score action-sequence and outcome divergence
- write source-diverse accepted rows and explicit preferred/rejected NPZ fields
- verify actor checksum unchanged and no actor checkpoint written

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor parameters
- do not promote checkpoint
- do not accept hidden-distance-only rows
- do not use hidden parameters or labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m664-action-critical-wrong-history-source-miner-implementation
- type: infrastructure
- checkpoint: runs/m664_action_critical_wrong_history_source_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_critical_wrong_history_source_miner_negative_admit_audit
- reason: M664 finds larger wrong-history action gaps but accepts 0 rows because action-threshold rows are already normal-failed and no margin or success-drop gap appears

## Next Blocker

m665-action-critical-wrong-history-source-miner-audit
