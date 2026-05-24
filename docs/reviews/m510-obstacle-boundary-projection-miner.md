# m510-obstacle-boundary-projection-miner Research Review

## Summary

- Generated at UTC: 20260524T011751Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_outcome_gate_admission
- Decision reason: M510 keeps projection_l2 p50/p90 at 1.0/1.118 and trajectory mean 0.089577 but selected rows are 102 unavoidable-only rows so projected-label diversity fails

## Hypothesis

Bounded obstacle projection around natural M508 anchors can create a source-diverse terminal-boundary wrong-history-sensitive projection surface while preserving natural ego/history state.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m508_terminal_boundary_anchor_miner/summary.json, runs/m508_terminal_boundary_anchor_miner/anchors.csv, runs/m508_terminal_boundary_anchor_miner/scored_pairs.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m509-obstacle-boundary-projection-design.json
- parent_objective: bounded obstacle-boundary projection miner
- derived_from: m509-obstacle-boundary-projection-design
- blocked_by: m509-obstacle-boundary-projection-design
- supersedes: None
- invalidates: None

## Success Criteria

- projection miner runs on M508 anchors and both M502 configs
- pair_count >= 240
- probe_seed_count >= 6
- obstacle_label_count >= 2
- target_count >= 2
- config_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- single_config_share <= 0.70
- rows with normal_min_clearance_margin <= 0.50 >= 40
- rows with normal_min_clearance_margin <= 1.00 >= 100
- targeted_trajectory_mean >= 0.04
- targeted_trajectory_p90 >= 0.08
- projection_l2_p50 <= 3.0
- projection_l2_p90 <= 6.0
- primary_projection_share >= 0.80
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- too few source-diverse projected rows are found
- projection magnitude is too large to support a controlled diagnostic proof
- projected rows have no wrong-history action signal
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- implement and run bounded obstacle-boundary projection mining from M508 anchors
- preserve natural ego state, recurrent hidden state, and actor input contract
- report projection magnitudes before any outcome-gate admission
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not claim projection rows as raw natural proof
- do not satisfy admission with large diagnostic projection rows unless pre-registered

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m510-obstacle-boundary-projection-miner
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_outcome_gate_admission
- reason: M510 keeps projection_l2 p50/p90 at 1.0/1.118 and trajectory mean 0.089577 but selected rows are 102 unavoidable-only rows so projected-label diversity fails

## Next Blocker

M511 should design label-targeted projection mining because bounded local projection preserves action signal but produces only unavoidable projected rows.
