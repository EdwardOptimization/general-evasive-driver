# m605-grounded-capability-action-target-mining-design Research Review

## Summary

- Generated at UTC: 20260524T083159Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: grounded_capability_action_target_mining_design_admit_m606
- Decision reason: M605 designs local first-action target mining with simulator-grounded margin/risk acceptance and keeps action-coupling training blocked

## Hypothesis

M604 belief-only gaps are useful only if local recovery or terminal-boundary search can ground them in action targets that improve margin or risk without violating the actor contract.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m604_guarded_capability_action_coupling_evaluator/summary.json, runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv, runs/m604_guarded_capability_action_coupling_evaluator/variant_summary.csv
- parent_config: docs/m603-guarded-capability-action-coupling-design.md
- parent_objective: design grounded target mining for belief-only capability-action coupling candidates
- derived_from: m604-guarded-capability-action-coupling-evaluator
- blocked_by: m604-guarded-capability-action-coupling-evaluator
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies target mining commands and artifacts
- design specifies action search trust region and acceptance thresholds
- design distinguishes normal-branch repair from wrong-history branch preservation
- design keeps training blocked until target mining passes
- research validation passes

## Failure Criteria

- design starts training
- design treats M604 candidates as labels
- design lacks margin or risk acceptance criteria
- design permits target mining from private holdout
- design promotes a checkpoint

## Evidence Gates

- define local recovery search scope
- define terminal-boundary or route-risk grounding criteria
- define target acceptance thresholds
- forbid treating belief-only gaps as direct action targets
- keep actor training and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not run PPO
- do not promote checkpoint
- do not add privileged actor inputs
- do not create action targets without simulator-grounded margin or risk improvement

## Failure Taxonomy

- none

## Scoreboard

- milestone: m605-grounded-capability-action-target-mining-design
- type: infrastructure
- checkpoint: docs/m605-grounded-capability-action-target-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: grounded_capability_action_target_mining_design_admit_m606
- reason: M605 designs local first-action target mining with simulator-grounded margin/risk acceptance and keeps action-coupling training blocked

## Next Blocker

m606-grounded-capability-action-target-miner-implementation
