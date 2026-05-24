# m606-grounded-capability-action-target-miner-implementation Research Review

## Summary

- Generated at UTC: 20260524T084548Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: grounded_capability_action_target_miner_negative_admit_audit
- Decision reason: M606 writes 4508 local first-action candidate rollouts from 23 unique M604 source rows but accepts 0 targets under pre-registered margin/risk thresholds; no target corpus training PPO or promotion

## Hypothesis

A bounded first-action local search around M604 belief-only gap rows can find simulator-grounded target actions that improve short-horizon margin or risk while preserving the actor input contract.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv, runs/m604_guarded_capability_action_coupling_evaluator/summary.json
- parent_config: docs/m605-grounded-capability-action-target-mining-design.md, configs/ppo_m541_matched_l3_variance_4096.json, configs/eval_m574_moderate_ood_l3.json
- parent_objective: implement grounded local action target miner for M604 belief-only gaps
- derived_from: m605-grounded-capability-action-target-mining-design
- blocked_by: m605-grounded-capability-action-target-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- target_candidates.csv is written
- accepted_targets.csv is written
- unaccepted_rows.csv is written
- target_corpus.npz is written when accepted targets exist
- summary records labels_enter_actor_input false ppo_used false promoted false actor_parameters_changed false
- research validation and focused tests pass

## Failure Criteria

- miner trains any model
- miner uses private holdout rows
- miner omits unaccepted rows
- miner writes privileged actor inputs
- miner promotes a checkpoint

## Evidence Gates

- write target candidate rollouts
- write accepted target rows
- write unaccepted rows
- write deployable-only target corpus
- prove no model weights are changed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not add privileged actor inputs
- do not hide unaccepted rows
- do not convert ungrounded belief-only gaps into targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m606-grounded-capability-action-target-miner-implementation
- type: infrastructure
- checkpoint: runs/m606_grounded_capability_action_target_miner/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: grounded_capability_action_target_miner_negative_admit_audit
- reason: M606 writes 4508 local first-action candidate rollouts from 23 unique M604 source rows but accepts 0 targets under pre-registered margin/risk thresholds; no target corpus training PPO or promotion

## Next Blocker

m607-grounded-target-mining-audit
