# m663-action-critical-wrong-history-source-mining-design Research Review

## Summary

- Generated at UTC: 20260524T140958Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: action_critical_wrong_history_source_mining_design_admit_m664
- Decision reason: M663 designs broader action/outcome-first wrong-history source mining with compatibility filters strict thresholds diversity rules and no-training constraints

## Hypothesis

A broader action/outcome-first source miner can find wrong-history pairs that are both scene-compatible and action-critical, unlike the M586/M636 matched-current surfaces.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m661_action_divergent_wrong_history_corpus/summary.json, runs/m661_action_divergent_wrong_history_corpus/candidate_scores.csv, docs/m662-action-divergent-wrong-history-corpus-audit.md
- parent_config: experiments/manifests/m662-action-divergent-wrong-history-corpus-audit.json
- parent_objective: design action-critical wrong-history source mining after M661 empty corpus
- derived_from: m662-action-divergent-wrong-history-corpus-audit
- blocked_by: m662-action-divergent-wrong-history-corpus-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines snapshot bank inputs and sampling limits
- design defines wrong-history candidate pairing strategy
- design defines action-sequence and margin/success-drop thresholds
- design defines source diversity and heldout split rules
- design defines negative-result interpretation
- research validation passes

## Failure Criteria

- design falls back to hidden-distance-only acceptance
- design omits scene/current-state compatibility constraints
- design admits training or PPO before source evidence exists
- design omits failure interpretation if no action-critical rows are found

## Evidence Gates

- design broader wrong-history source selection based on action and outcome sensitivity
- pre-register scene/current-state similarity limits
- pre-register source-diverse acceptance thresholds and split rules
- keep actor coupling, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not use hidden-distance-only acceptance
- do not use hidden parameters or labels as actor inputs
- do not weaken M661 thresholds post hoc

## Failure Taxonomy

- none

## Scoreboard

- milestone: m663-action-critical-wrong-history-source-mining-design
- type: infrastructure
- checkpoint: docs/m663-action-critical-wrong-history-source-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_critical_wrong_history_source_mining_design_admit_m664
- reason: M663 designs broader action/outcome-first wrong-history source mining with compatibility filters strict thresholds diversity rules and no-training constraints

## Next Blocker

m664-action-critical-wrong-history-source-miner-implementation
