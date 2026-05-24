# m506-terminal-boundary-aware-selector Research Review

## Summary

- Generated at UTC: 20260524T004552Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_outcome_gate_admission
- Decision reason: M506 improves low-margin rows to 35/76/101 within margin 0.5/1.0/2.0 but source-capped targeted count is only 101 and label share is 0.733

## Hypothesis

Selecting low-margin normal-history rows first and then requiring smaller wrong-history action perturbations will yield a source-diverse targeted surface suitable for outcome testing.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m504_boundary_action_sensitive_targeted_pair_triage/action_sensitive_candidates.csv, runs/m504_boundary_action_sensitive_targeted_pair_triage/summary.json
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m505-terminal-boundary-alignment-redesign.json
- parent_objective: terminal-boundary-aware targeted selector
- derived_from: m505-terminal-boundary-alignment-redesign
- blocked_by: m505-terminal-boundary-alignment-redesign
- supersedes: None
- invalidates: None

## Success Criteria

- terminal-boundary-aware selector runs on M504 candidates
- targeted_pair_count >= 240
- probe_seed_count >= 6
- obstacle_label_count >= 2
- target_count >= 2
- config_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- single_config_share <= 0.70
- rows with normal_min_clearance_margin <= 0.50 >= 40
- rows with normal_min_clearance_margin <= 1.00 >= 100
- rows with normal_min_clearance_margin <= 2.00 >= 180
- targeted_trajectory_mean >= 0.04
- targeted_trajectory_p90 >= 0.08
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- selected rows remain high-margin
- selected rows are low-margin but have no wrong-history action signal
- candidate surface is source-narrow
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- select rows from M504 candidates by terminal-boundary sensitivity first
- apply softer wrong-history action-sensitivity thresholds suitable for low-margin states
- require source diversity and low-margin bucket coverage before any outcome gate
- do not run outcome gates, train, or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not select high-margin rows to satisfy action metrics
- do not tune from private holdouts

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m506-terminal-boundary-aware-selector
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
- reason: M506 improves low-margin rows to 35/76/101 within margin 0.5/1.0/2.0 but source-capped targeted count is only 101 and label share is 0.733

## Next Blocker

M507 should design terminal-boundary anchor mining because M506 improves low-margin coverage but remains too small after source caps.
