# m503-natural-boundary-pressure-matched-current-mining Research Review

## Summary

- Generated at UTC: 20260524T003115Z
- Type: gate
- Gate tier: proof
- Promotion decision: boundary_pressure_matched_surface_pass_admit_m504_targeted_pair_triage
- Decision reason: M503 combined surface has 5727 accepted pairs 3716 physical pairs 6 seeds 3 labels 3 targets 2 configs and single-seed/config shares 0.185/0.507

## Hypothesis

The M502 boundary-pressure configs can produce source-diverse matched-current ambiguity surfaces with lower terminal slack than M495, enabling later boundary-action-sensitive targeted pair selection.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m502_natural_boundary_pressure_config_validation/sampling_summary.json, runs/m502_natural_boundary_pressure_config_validation/behavior_summary.json
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m502-natural-boundary-pressure-config-implementation.json
- parent_objective: natural boundary-pressure matched-current ambiguity mining
- derived_from: m502-natural-boundary-pressure-config-implementation
- blocked_by: m502-natural-boundary-pressure-config-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- matched-current mining completes on both configs without sampling failure
- combined accepted_pair_count >= 512
- combined probe_seed_count >= 6
- combined obstacle_label_count >= 2
- combined target_count >= 2
- combined config_count >= 2
- combined single_seed_share <= 0.50
- combined single_label_share <= 0.70
- combined single_config_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- either config cannot produce enough matched-current candidates
- candidate surface is source-narrow
- only one obstacle label or target dominates
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- run matched-current mining on both M502 boundary-pressure configs
- require source-diverse candidate surfaces before targeted triage
- report accepted pairs, physical pairs, labels, targets, seed windows, visible distance, and target z delta
- include boundary-pressure config source in combined artifacts
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not skip source-diversity checks before outcome gates
- do not count aggregate behavior smoke as self-ID proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m503-natural-boundary-pressure-matched-current-mining
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_pressure_matched_surface_pass_admit_m504_targeted_pair_triage
- reason: M503 combined surface has 5727 accepted pairs 3716 physical pairs 6 seeds 3 labels 3 targets 2 configs and single-seed/config shares 0.185/0.507

## Next Blocker

M504 should select targeted boundary-action-sensitive pairs from the M503 combined surface before any outcome gate.
