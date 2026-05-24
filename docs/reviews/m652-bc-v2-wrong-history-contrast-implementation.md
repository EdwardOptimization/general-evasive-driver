# m652-bc-v2-wrong-history-contrast-implementation Research Review

## Summary

- Generated at UTC: 20260524T132250Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: bc_v2_wrong_history_contrast_negative_admit_feature_separability_audit
- Decision reason: M652 preserves normal validation loss but 0 of 3 seeds pass wrong-history gap thresholds so actor coupling remains blocked

## Hypothesis

Adding a wrong-history rejection loss can preserve normal sequence-delta learning while increasing wrong-history prediction gaps on sources 30 and 32.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m649_bc_v2_head_only_repeat/wrong_history_source_summary.csv, docs/m651-bc-v2-wrong-history-contrast-design.md
- parent_config: experiments/manifests/m651-bc-v2-wrong-history-contrast-design.json
- parent_objective: implement frozen-head wrong-history contrast smoke
- derived_from: m651-bc-v2-wrong-history-contrast-design
- blocked_by: m651-bc-v2-wrong-history-contrast-design
- supersedes: None
- invalidates: None

## Success Criteria

- at least two of three seeds pass contrast thresholds
- normal validation loss remains <= 0.0010
- wrong-history train and validation gaps pass thresholds
- actor checksum remains unchanged
- no actor checkpoint is written
- research validation passes

## Failure Criteria

- fewer than two seeds pass
- normal validation loss regresses beyond threshold
- wrong-history gaps remain near zero
- actor checksum changes
- actor checkpoint is written

## Evidence Gates

- train only frozen-head contrast objective
- run seeds 6510 6511 6512
- report normal target retention
- report wrong-history train and source-heldout gaps
- verify actor checksum unchanged
- write no actor checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run PPO
- do not promote checkpoint
- do not include delayed-history rows in wrong-history rejection without audit
- do not use metadata as actor input

## Failure Taxonomy

- none

## Scoreboard

- milestone: m652-bc-v2-wrong-history-contrast-implementation
- type: infrastructure
- checkpoint: runs/m652_bc_v2_wrong_history_contrast/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_wrong_history_contrast_negative_admit_feature_separability_audit
- reason: M652 preserves normal validation loss but 0 of 3 seeds pass wrong-history gap thresholds so actor coupling remains blocked

## Next Blocker

m653-bc-v2-wrong-history-contrast-audit
