# m598-bc-capability-repair-objective-smoke-implementation Research Review

## Summary

- Generated at UTC: 20260524T075011Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: bc_capability_repair_head_only_smoke_pass_admit_audit
- Decision reason: M598 passes frozen-actor head-only objective smoke: train/validation regression drops 79/67 percent rank losses drop and actor/action anchors remain unchanged

## Hypothesis

The M596 capability corpus contains learnable future-response signal in BC5660 base hidden states, so a frozen-actor capability head should reduce regression and ranking losses without changing policy behavior.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m596_bc_capability_corpus_train_smoke/capability_corpus.npz, runs/m596_bc_capability_corpus_validation_smoke/capability_corpus.npz, runs/m596_bc_capability_corpus_train_smoke/pairs.csv, runs/m596_bc_capability_corpus_validation_smoke/pairs.csv
- parent_config: docs/m597-bc-capability-repair-objective-smoke-design.md
- parent_objective: implement and run frozen-actor head-only capability objective smoke
- derived_from: m597-bc-capability-repair-objective-smoke-design
- blocked_by: m597-bc-capability-repair-objective-smoke-design
- supersedes: None
- invalidates: None

## Success Criteria

- runner writes capability_head.pt train_metrics.csv validation_metrics.csv and summary.json
- train regression loss drops at least 30 percent
- validation regression loss drops at least 10 percent
- train ranking loss drops at least 10 percent
- validation ranking loss does not increase more than 10 percent
- actor_parameters_changed is false and action-anchor MSE is <= 1e-8

## Failure Criteria

- actor parameters change
- capability labels enter actor inputs
- loss metrics do not meet smoke thresholds
- checkpoint is promoted or PPO is run

## Evidence Gates

- implement head-only smoke runner
- train capability head on frozen BC5660 hidden state
- write train and validation metrics
- verify actor parameters are unchanged and output is unpromoted

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run PPO
- do not run route evaluation
- do not promote checkpoint
- do not feed capability labels to actor inputs
- do not claim driver improvement from head-only loss

## Failure Taxonomy

- none

## Scoreboard

- milestone: m598-bc-capability-repair-objective-smoke-implementation
- type: gate
- checkpoint: runs/m598_bc_capability_repair_head_only_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_repair_head_only_smoke_pass_admit_audit
- reason: M598 passes frozen-actor head-only objective smoke: train/validation regression drops 79/67 percent rank losses drop and actor/action anchors remain unchanged

## Next Blocker

m599-bc-capability-head-smoke-audit
