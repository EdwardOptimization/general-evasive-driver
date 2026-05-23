# m469-adversarial-wrong-history-pair-search Research Review

## Summary

- Generated at UTC: 20260523T212557Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: search_surface_too_small_admit_m470_expanded_pool_design
- Decision reason: M469 exports only 50 adversarial pairs with single seed share 0.68 so outcome probing is rejected until pool expansion

## Hypothesis

Searching the full candidate-pair pool for more adversarial right histories around M467 near-boundary left states can produce a stronger wrong-history probe surface than M464's one-pass targeted pair triage.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv, runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m468-near-boundary-task-family-redesign.json
- parent_objective: adversarial wrong-history pair search for near-boundary left states
- derived_from: m468-near-boundary-task-family-redesign
- blocked_by: m468-near-boundary-task-family-redesign
- supersedes: None
- invalidates: None

## Success Criteria

- adversarial pair search CLI writes search_candidates.csv adversarial_pairs.csv and summary.json
- adversarial_pairs >= 64
- near_boundary_left_state_count >= 16
- probe_seed_count >= 3
- left_obstacle_label_count >= 2
- target_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- no checkpoint is promoted

## Failure Criteria

- search ignores normal-margin anchors
- search drops matched-current similarity constraints
- search returns only one seed or one label
- search requires privileged actor inputs

## Evidence Gates

- implement adversarial wrong-history search over full candidate_pairs.csv
- anchor search on M467 near-boundary no-effect left states
- preserve matched-current and normal-margin constraints
- write adversarial_pairs.csv search_candidates.csv and summary.json
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not count high-slack diagnostics as proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m469-adversarial-wrong-history-pair-search
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: search_surface_too_small_admit_m470_expanded_pool_design
- reason: M469 exports only 50 adversarial pairs with single seed share 0.68 so outcome probing is rejected until pool expansion

## Next Blocker

m470-expanded-adversarial-pool-design
