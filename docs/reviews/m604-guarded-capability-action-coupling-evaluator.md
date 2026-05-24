# m604-guarded-capability-action-coupling-evaluator Research Review

## Summary

- Generated at UTC: 20260524T082921Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: guarded_capability_action_coupling_evaluator_pass_admit_grounded_target_design
- Decision reason: M604 joins M591 action and M601 capability rows and finds 262 real-history belief-only gaps; candidates require simulator-grounded targets before training

## Hypothesis

An exact no-update evaluator can localize rows where real hidden histories move decoded capability belief but not action, providing a grounded candidate set for later recovery or boundary target mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m601_bc_capability_belief_intervention_fresh/capability_intervention_rows.csv, runs/m601_bc_capability_belief_intervention_ood/capability_intervention_rows.csv, runs/m591_bc_hidden_action_sensitivity_probe_fresh/action_sensitivity_rows.csv, runs/m591_bc_hidden_action_sensitivity_probe_ood/action_sensitivity_rows.csv
- parent_config: docs/m603-guarded-capability-action-coupling-design.md
- parent_objective: implement exact no-update evaluator for capability-action coupling gaps
- derived_from: m603-guarded-capability-action-coupling-design
- blocked_by: m603-guarded-capability-action-coupling-design
- supersedes: None
- invalidates: None

## Success Criteria

- coupling_rows.csv is written
- variant_summary.csv is written
- belief-only gap counts are reported for real-history variants
- summary records ppo_used false promoted false actor_parameters_changed false
- research validation and focused tests pass

## Failure Criteria

- evaluator trains any model
- evaluator omits real-history variants
- evaluator claims driver improvement
- evaluator turns belief-only gaps into action targets

## Evidence Gates

- join capability movement and action movement on matched-current rows
- classify belief-only action-and-belief action-without-belief inactive rows
- report real-history source-diverse candidate counts
- prove no model weights are changed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not add capability labels to actor inputs
- do not treat belief-only gaps as action targets without grounding

## Failure Taxonomy

- none

## Scoreboard

- milestone: m604-guarded-capability-action-coupling-evaluator
- type: infrastructure
- checkpoint: runs/m604_guarded_capability_action_coupling_evaluator/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: guarded_capability_action_coupling_evaluator_pass_admit_grounded_target_design
- reason: M604 joins M591 action and M601 capability rows and finds 262 real-history belief-only gaps; candidates require simulator-grounded targets before training

## Next Blocker

m605-grounded-capability-action-target-mining-design
