# m296-current-family-rejected-margin-objective-design Research Review

## Summary

- Generated at UTC: 20260523T002803Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: implement_rejected_history_preference_objective_sanity
- Decision reason: M296 designs a pairwise rejected-history preference objective using rejected_action and margin labels so M297 can test proof-washout sensitivity before any PPO

## Hypothesis

M291 and M294 fail because action-anchor pressure is not a direct constraint on rejected-history outcomes; a margin/preference objective that scores correct-history versus wrong-history rollouts can target current-family proof retention before PPO.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m295_current_family_ppo_repair_audit/failed_row_comparison.csv, runs/m294_current_family_rejected_repair_ppo_smoke/gates/raw_m267_m264/boundary_replay_rows.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m295-current-family-ppo-repair-audit.json, docs/m295-current-family-ppo-repair-audit.md
- parent_objective: design direct current-family rejected-history margin/preference objective after M294 trajectory action anchoring failed
- derived_from: m295-current-family-ppo-repair-audit
- blocked_by: m295-current-family-ppo-repair-audit
- supersedes: None
- invalidates: None

## Success Criteria

- write a concrete objective design with inputs, labels, loss terms, and pass/fail gates
- identify the exact artifacts needed for implementation
- pre-register the next implementation or objective-sanity milestone
- keep PPO blocked until the objective has a no-training sanity check

## Failure Criteria

- objective is only another stronger action anchor
- design requires privileged actor inputs
- design lacks an exact M270 no-regression guard
- PPO is run

## Evidence Gates

- do not run PPO
- preserve human-view actor input contract
- define the direct rejected-history margin/preference objective
- define the exact M270 no-regression and M267/M264 retention gates required before PPO
- state how the objective differs from stronger trajectory action anchoring

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train a driver in M296
- do not promote M291 or M294
- do not change actor inputs
- do not use hidden vehicle parameters as actor inputs
- do not treat a lower action-anchor loss as proof retention

## Failure Taxonomy

- none

## Scoreboard

- milestone: m296-current-family-rejected-margin-objective-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: implement_rejected_history_preference_objective_sanity
- reason: M296 designs a pairwise rejected-history preference objective using rejected_action and margin labels so M297 can test proof-washout sensitivity before any PPO

## Next Blocker

m297-current-family-rejected-preference-objective-implementation
