# m474-combined-fresh-anchor-adversarial-search Research Review

## Summary

- Generated at UTC: 20260523T215330Z
- Type: gate
- Gate tier: generalization
- Promotion decision: combined_adversarial_surface_pass_admit_m475
- Decision reason: M474 exports 197 adversarial pairs across 82 near-boundary left states 9 seeds 2 labels and 3 targets with single-seed share 0.197970

## Hypothesis

Combining M467 same-window anchors with M473 fresh-window anchors and candidate pools will produce a source-diverse adversarial wrong-history surface suitable for later outcome probing.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv, runs/m471_expanded_matched_current_seed10200/candidate_pairs.csv, runs/m473_combined_fresh_window_anchor_summary/near_boundary_candidates_combined.csv, runs/m473a_fresh_window_matched_current_seed10500/candidate_pairs.csv, runs/m473b_fresh_window_matched_current_seed10800/candidate_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m473-fresh-window-anchor-discovery-run.json
- parent_objective: combined source-diverse adversarial wrong-history search
- derived_from: m473-fresh-window-anchor-discovery-run
- blocked_by: m473-fresh-window-anchor-discovery-run
- supersedes: None
- invalidates: None

## Success Criteria

- combined anchor CSV is created from M467 and M473 near-boundary no-effect anchors
- combined candidate-pair CSV is created from M471 and M473 candidate pools
- adversarial search completes on the combined CSVs
- adversarial_pairs >= 96
- near_boundary_left_state_count >= 32
- probe_seed_count >= 6
- left_obstacle_label_count >= 2
- target_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- combined CSVs cannot be built reproducibly
- adversarial pair count remains below 96
- single_seed_share exceeds 0.50
- surface is dominated by one obstacle label
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- combine M467 and M473 near-boundary anchors
- combine M471 and M473 candidate-pair pools
- run adversarial wrong-history search on the combined surface
- decide whether the adversarial surface is source-diverse enough for outcome probing
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not outcome-probe until the combined adversarial surface passes source-diversity gates
- do not loosen single-seed balance requirements
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m474-combined-fresh-anchor-adversarial-search
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_adversarial_surface_pass_admit_m475
- reason: M474 exports 197 adversarial pairs across 82 near-boundary left states 9 seeds 2 labels and 3 targets with single-seed share 0.197970

## Next Blocker

m475-combined-adversarial-outcome-proof-probe
