# m471-expanded-adversarial-pool-run Research Review

## Summary

- Generated at UTC: 20260523T213431Z
- Type: gate
- Gate tier: generalization
- Promotion decision: expanded_same_window_count_pass_balance_fail_admit_m472
- Decision reason: M471 expands candidate pool to 380877 and adversarial pairs to 67 but single-seed share remains 0.671642 so outcome probe is rejected

## Hypothesis

A higher-sample matched-current mining pass on the same seed window will increase adversarial wrong-history coverage enough to justify a later outcome probe.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv, runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m470-expanded-adversarial-pool-design.json
- parent_objective: expanded same-window adversarial candidate-pool run
- derived_from: m470-expanded-adversarial-pool-design
- blocked_by: m470-expanded-adversarial-pool-design
- supersedes: None
- invalidates: None

## Success Criteria

- expanded matched-current mining completes without sampling failure
- adversarial search completes on the expanded candidate pool
- adversarial_pairs >= 64
- near_boundary_left_state_count >= 16
- probe_seed_count >= 3
- left_obstacle_label_count >= 2
- target_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- no checkpoint is promoted

## Failure Criteria

- expanded mining fails scenario sampling
- adversarial pair count remains below 64
- single seed share remains above 0.50
- actor contract changes

## Evidence Gates

- run expanded matched-current mining on seed window 10200/10300/10400
- rerun adversarial wrong-history search on M467 near-boundary anchors
- decide whether surface is source-diverse enough for outcome probing
- write docs and artifacts
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not run outcome probe unless the adversarial surface passes source-diversity gates
- do not loosen normal-margin requirements
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m471-expanded-adversarial-pool-run
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: expanded_same_window_count_pass_balance_fail_admit_m472
- reason: M471 expands candidate pool to 380877 and adversarial pairs to 67 but single-seed share remains 0.671642 so outcome probe is rejected

## Next Blocker

m472-fresh-window-near-boundary-anchor-design
