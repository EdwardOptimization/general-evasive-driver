# m649-bc-v2-head-only-repeat-implementation Research Review

## Summary

- Generated at UTC: 20260524T130841Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_v2_head_only_repeat_pass_admit_audit
- Decision reason: M649 all three frozen-head seeds pass best-validation thresholds with unchanged actor checksum but wrong-history source gaps remain near zero

## Hypothesis

A three-seed best-validation frozen-head repeat will reproduce the M646 sequence-delta learnability result while controlling final-epoch overfit.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m646_bc_v2_head_only_smoke/summary.json, docs/m648-bc-v2-head-only-repeat-design.md
- parent_config: experiments/manifests/m648-bc-v2-head-only-repeat-design.json
- parent_objective: implement early-stopped multi-seed frozen-head repeat
- derived_from: m648-bc-v2-head-only-repeat-design
- blocked_by: m648-bc-v2-head-only-repeat-design
- supersedes: None
- invalidates: None

## Success Criteria

- at least two of three seeds meet repeat pass thresholds
- all actor checksums are unchanged
- all seeds write best-validation head checkpoints
- no actor checkpoints are written
- wrong-history source summaries are written
- research validation passes

## Failure Criteria

- fewer than two seeds pass repeat thresholds
- actor checksum changes
- best-validation head is not saved
- actor checkpoint is written
- wrong-history summary is missing

## Evidence Gates

- run seeds 6460 6461 6462
- save best-validation and final head checkpoints for every seed
- verify actor checksum unchanged for every seed
- write seed source target and wrong-history summaries
- write no actor checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run PPO
- do not promote checkpoint
- do not use source-heldout as private promotion evidence
- do not hide final-vs-best validation regression
- do not omit wrong-history source summary

## Failure Taxonomy

- none

## Scoreboard

- milestone: m649-bc-v2-head-only-repeat-implementation
- type: infrastructure
- checkpoint: runs/m649_bc_v2_head_only_repeat/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_head_only_repeat_pass_admit_audit
- reason: M649 all three frozen-head seeds pass best-validation thresholds with unchanged actor checksum but wrong-history source gaps remain near zero

## Next Blocker

m650-bc-v2-head-only-repeat-audit
