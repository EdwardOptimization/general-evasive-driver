# m646-bc-v2-head-only-smoke-implementation Research Review

## Summary

- Generated at UTC: 20260524T125359Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_v2_head_only_smoke_pass_admit_audit
- Decision reason: M646 head-only smoke improves train delta-MSE 97.28 percent and source-heldout 84.50 percent with unchanged actor checksum but validation overfit requires audit

## Hypothesis

A frozen BC5660 feature extractor plus a small sequence-delta head can reduce source-balanced masked sequence loss without mutating the actor.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m644_source_balanced_bc_v2_objective/summary.json, docs/m645-bc-v2-head-only-smoke-design.md
- parent_config: experiments/manifests/m645-bc-v2-head-only-smoke-design.json
- parent_objective: implement a frozen-actor auxiliary sequence-delta head-only smoke
- derived_from: m645-bc-v2-head-only-smoke-design
- blocked_by: m645-bc-v2-head-only-smoke-design
- supersedes: None
- invalidates: None

## Success Criteria

- head-only training reduces train delta MSE by at least 30 percent
- source-heldout validation delta MSE does not increase
- actor checksum is unchanged
- only a head checkpoint is written
- source split and target summaries are written
- research validation passes

## Failure Criteria

- actor checksum changes
- head-only training cannot reduce train loss
- source-heldout validation regresses
- actor checkpoint is written
- source-balanced summaries are missing

## Evidence Gates

- freeze all BC5660 actor parameters
- train only sequence-delta head
- use source-balanced masked losses
- write train and source-heldout validation metrics
- verify actor checksum unchanged
- write no actor checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run PPO
- do not promote checkpoint
- do not use source ids target labels or split labels as actor inputs
- do not report raw row-count weighted metrics as primary
- do not write actor checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m646-bc-v2-head-only-smoke-implementation
- type: infrastructure
- checkpoint: runs/m646_bc_v2_head_only_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_head_only_smoke_pass_admit_audit
- reason: M646 head-only smoke improves train delta-MSE 97.28 percent and source-heldout 84.50 percent with unchanged actor checksum but validation overfit requires audit

## Next Blocker

m647-bc-v2-head-only-smoke-audit
