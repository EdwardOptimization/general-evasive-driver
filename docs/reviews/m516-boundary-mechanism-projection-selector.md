# m516-boundary-mechanism-projection-selector Research Review

## Summary

- Generated at UTC: 20260524T020000Z
- Type: gate
- Gate tier: proof
- Promotion decision: boundary_mechanism_projection_gate_pass_admit_m517_projection_aware_outcome_gate_design
- Decision reason: M516 selects 292 terminal-boundary projected rows across 6 seeds 3 targets 2 configs 12 obstacle buckets and 46 projection buckets; scenario label diversity is reported separately

## Hypothesis

Using geometry/source diversity instead of projected-label diversity for terminal-boundary mechanism proof will yield a valid proof surface from M514 scored rows.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m514_projected_label_margin_conflict_audit/scored_pairs.csv, runs/m514_projected_label_margin_conflict_audit/summary.json
- parent_config: experiments/manifests/m515-proof-scenario-gate-split-design.json
- parent_objective: boundary mechanism projection selector
- derived_from: m515-proof-scenario-gate-split-design
- blocked_by: m515-proof-scenario-gate-split-design
- supersedes: None
- invalidates: None

## Success Criteria

- targeted_pair_count >= 240
- probe_seed_count >= 6
- target_count >= 2
- config_count >= 2
- projected_obstacle_bucket_count >= 8
- projection_bucket_count >= 8
- single_seed_share <= 0.50
- single_config_share <= 0.70
- single_target_share <= 0.70
- single_obstacle_bucket_share <= 0.35
- single_projection_bucket_share <= 0.35
- rows with normal_min_clearance_margin <= 0.50 >= 40
- rows with normal_min_clearance_margin <= 1.00 >= 100
- targeted_trajectory_mean >= 0.04
- targeted_trajectory_p90 >= 0.08
- scenario-label distribution is reported
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- source/config/target/geometry diversity remains too small
- selected rows have no wrong-history action signal
- selector claims scenario-label generalization
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- select terminal-boundary projected rows with source/config/target/geometry diversity
- report scenario-label distribution without using it as mechanism proof admission
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim scenario-label generalization from mechanism rows
- do not skip geometry bucket diversity

## Failure Taxonomy

- none

## Scoreboard

- milestone: m516-boundary-mechanism-projection-selector
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_mechanism_projection_gate_pass_admit_m517_projection_aware_outcome_gate_design
- reason: M516 selects 292 terminal-boundary projected rows across 6 seeds 3 targets 2 configs 12 obstacle buckets and 46 projection buckets; scenario label diversity is reported separately

## Next Blocker

M517 should design a projection-aware outcome gate that preserves relocated obstacle geometry.
