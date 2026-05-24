# m593-bc-capability-repair-objective-implementation Research Review

## Summary

- Generated at UTC: 20260524T073153Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_capability_repair_objective_implementation_admit_corpus_design
- Decision reason: M593 implements capability head regression ranking action-anchor losses and metadata preservation tests without real checkpoint training or promotion

## Hypothesis

A capability-supervised repair objective can be implemented as a training-only auxiliary path that preserves P0 actor inputs and exposes regression/ranking/action-anchor metrics before any driver claim.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m567_scaled_l2_teacher_corpus_train/l2_teacher_corpus.npz, runs/m567_scaled_l2_teacher_corpus_validation/l2_teacher_corpus.npz, runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv, runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: implement capability-supervised hidden repair objective after M592 design
- derived_from: m592-bc-hidden-use-repair-objective-design
- blocked_by: m592-bc-hidden-use-repair-objective-design
- supersedes: None
- invalidates: None

## Success Criteria

- implementation adds a tested capability repair objective or corpus path
- tests verify P0 actor inputs and metadata are preserved
- tests verify capability and ranking losses are finite and decrease on a tiny synthetic case
- manifest and docs state that output checkpoints are smoke-only and unpromoted
- research validation passes

## Failure Criteria

- implementation changes actor observation contract
- implementation feeds capability labels to deployable actor inputs
- implementation runs PPO or promotion gates
- implementation lacks focused tests

## Evidence Gates

- implement objective infrastructure and focused tests only
- preserve P0 actor input metadata
- write train validation and pair objective metrics
- do not claim driver improvement from infrastructure smoke

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not add hidden vehicle parameters or wheel/slip inputs to actor
- do not use capability labels as deployable actor inputs
- do not optimize ungrounded action separation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m593-bc-capability-repair-objective-implementation
- type: infrastructure
- checkpoint: docs/m593-bc-capability-repair-objective-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_capability_repair_objective_implementation_admit_corpus_design
- reason: M593 implements capability head regression ranking action-anchor losses and metadata preservation tests without real checkpoint training or promotion

## Next Blocker

m594-bc-capability-repair-corpus-design
