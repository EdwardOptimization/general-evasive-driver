# m645-bc-v2-head-only-smoke-design Research Review

## Summary

- Generated at UTC: 20260524T124831Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_v2_head_only_smoke_design_admit_m646
- Decision reason: M645 designs a frozen-actor auxiliary sequence-delta head-only smoke with source-balanced masked loss train/source-heldout reporting checksum gate and no promotion

## Hypothesis

A frozen-actor auxiliary sequence-delta head can test whether BC5660 features contain the M641 local correction signal before any actor coupling update.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m644_source_balanced_bc_v2_objective/summary.json, docs/m644-source-balanced-bc-v2-objective-implementation.md
- parent_config: experiments/manifests/m644-source-balanced-bc-v2-objective-implementation.json
- parent_objective: design a frozen-actor source-balanced BC-v2 head-only smoke after exact evaluator implementation
- derived_from: m644-source-balanced-bc-v2-objective-implementation
- blocked_by: m644-source-balanced-bc-v2-objective-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- design document specifies frozen modules and trainable head
- design document specifies source-balanced masked losses
- design document specifies train/source-heldout reporting
- design document specifies actor checksum non-mutation gate
- design document rejects checkpoint promotion
- research validation passes

## Failure Criteria

- design allows actor mutation
- design allows promotion from head-only loss
- design omits source-heldout reporting
- design collapses source-balanced weights
- design changes actor inputs

## Evidence Gates

- freeze actor recurrent encoder and actor mean
- train only an auxiliary sequence-delta head if implementation is admitted
- use source-balanced masked sequence losses
- report train and source-heldout validation separately
- confirm actor checksum remains unchanged

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in the design milestone
- do not update actor parameters in the later head-only smoke
- do not promote checkpoint from head-only loss
- do not use source ids target labels or split labels as actor observations
- do not tune on source-heldout validation and call it unbiased evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m645-bc-v2-head-only-smoke-design
- type: infrastructure
- checkpoint: docs/m645-bc-v2-head-only-smoke-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_head_only_smoke_design_admit_m646
- reason: M645 designs a frozen-actor auxiliary sequence-delta head-only smoke with source-balanced masked loss train/source-heldout reporting checksum gate and no promotion

## Next Blocker

m646-bc-v2-head-only-smoke-implementation
