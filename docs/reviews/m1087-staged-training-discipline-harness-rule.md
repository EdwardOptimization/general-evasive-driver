# m1087-staged-training-discipline-harness-rule Research Review

## Summary

- Generated at UTC: 20260527T161803Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: staged_training_discipline_harness_rule_admit_m1088_existing_artifact_smoke
- Decision reason: M1087 adds process-v4 staged training discipline: future manifests declare training_stage and train_ppo requires guarded_rl evidence

## Hypothesis

Making pretrain-posttrain-guarded-RL discipline a validator-enforced manifest rule will prevent future milestones from treating PPO as an early primary optimizer or skipping action-grounding/proof-retention admission.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: public ChatGPT share 6a170ef6-5248-83ea-a394-9b4f1492999d message 188, docs/current-status.md, docs/m1086-v4-public-base-source-balanced-boundary-tooling-implementation.md
- parent_config: experiments/manifests/m1086-v4-public-base-source-balanced-boundary-tooling-implementation.json
- parent_objective: turn the pretrain-posttrain-RL staged training concept into a durable repo document and harness validation rule
- derived_from: m1086-v4-public-base-source-balanced-boundary-tooling-implementation, user instruction to落成 repo 文档或 harness 规则
- blocked_by: staged training discipline existed only as discussion, not as a repo-enforced manifest rule
- supersedes: None
- invalidates: running train_ppo in future manifests without declaring guarded_rl stage, treating PPO as the primary early training method instead of proposal generation after pretrain/posttrain evidence, leaving the pretrain-posttrain-RL rule as chat-only guidance

## Success Criteria

- docs/training-stage-discipline.md exists
- M1087 milestone artifact exists
- research schema defines process-v4 training-stage fields and allowed stages
- research validator enforces training_stage for future manifests
- research validator rejects train_ppo outside guarded_rl stage
- research validator tests cover the new rule
- previously planned existing-artifact smoke is preserved as M1088
- no training, PPO, promotion, private holdout, or full new mining run occurs

## Failure Criteria

- training-stage discipline remains documentation-only
- future manifests can run train_ppo without guarded_rl stage
- M1088 smoke plan is lost
- training, PPO, promotion, private holdout, or new mining starts

## Evidence Gates

- M1087 must not train
- M1087 must not run PPO
- M1087 must not promote
- M1087 must not use private holdout
- M1087 must add a durable training-stage discipline document
- M1087 must add validator-enforced manifest fields for future milestones
- M1087 must keep the previously planned existing-artifact smoke as the next milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not weaken existing proof or robustness gates
- do not leave the staged-training rule as documentation only

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1087-staged-training-discipline-harness-rule
- type: infrastructure
- checkpoint: docs/m1087-staged-training-discipline-harness-rule.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: staged_training_discipline_harness_rule_admit_m1088_existing_artifact_smoke
- reason: M1087 adds process-v4 staged training discipline: future manifests declare training_stage and train_ppo requires guarded_rl evidence

## Next Blocker

m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke
