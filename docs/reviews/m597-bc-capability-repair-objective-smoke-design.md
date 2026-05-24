# m597-bc-capability-repair-objective-smoke-design Research Review

## Summary

- Generated at UTC: 20260524T074544Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_capability_repair_smoke_design_admit_head_only_implementation
- Decision reason: M597 registers a frozen-actor head-only capability smoke using regression/ranking losses and action-anchor metrics without route evaluation PPO promotion or driver claims

## Hypothesis

The first repair smoke should optimize capability regression and pair ranking with a strong action anchor on the M596 train/validation corpora, then judge only objective wiring and metadata preservation.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m596_bc_capability_corpus_train_smoke/capability_corpus.npz, runs/m596_bc_capability_corpus_validation_smoke/capability_corpus.npz, runs/m596_bc_capability_corpus_train_smoke/pairs.csv, runs/m596_bc_capability_corpus_validation_smoke/pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: design first capability repair objective smoke after corpus export
- derived_from: m596-bc-capability-corpus-export-smoke
- blocked_by: m596-bc-capability-corpus-export-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies trainable modules and frozen modules
- design specifies loss weights and action-anchor tolerance
- design specifies metrics for train and validation regression ranking and action anchor losses
- design blocks route evaluation PPO and promotion
- research validation passes

## Failure Criteria

- design starts training before smoke protocol is registered
- design changes actor input contract
- design omits validation objective checks
- design promotes a checkpoint

## Evidence Gates

- design objective smoke before training
- define optimizer scope and freeze policy
- define loss weights and action-anchor tolerance
- define validation metrics and failure taxonomy

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run smoke training in design milestone
- do not run PPO
- do not promote checkpoint
- do not feed capability labels to actor inputs
- do not claim driver performance from objective loss

## Failure Taxonomy

- none

## Scoreboard

- milestone: m597-bc-capability-repair-objective-smoke-design
- type: infrastructure
- checkpoint: docs/m597-bc-capability-repair-objective-smoke-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_repair_smoke_design_admit_head_only_implementation
- reason: M597 registers a frozen-actor head-only capability smoke using regression/ranking losses and action-anchor metrics without route evaluation PPO promotion or driver claims

## Next Blocker

m598-bc-capability-repair-objective-smoke-implementation
