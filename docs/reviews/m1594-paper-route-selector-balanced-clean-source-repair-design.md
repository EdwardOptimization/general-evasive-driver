# m1594-paper-route-selector-balanced-clean-source-repair-design Research Review

## Summary

- Generated at UTC: 20260529T164404Z
- Type: gate
- Gate tier: process
- Promotion decision: selector_balanced_clean_source_repair_design_admit_bounded_implementation
- Decision reason: M1594 designs stricter source-edge cap with max 12 pairs per edge and min 8 selected edges before one bounded implementation

## Hypothesis

M1592's near-pass can be converted into a threshold-preserving selector-balanced cap design before any rerun.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1592_clean_history_control_source_generation_repair_smoke/summary.json, runs/m1592_clean_history_control_source_generation_repair_smoke/source_edge_summary.csv, docs/m1593-paper-route-clean-source-repair-result-audit.md
- parent_config: experiments/manifests/m1593-paper-route-clean-source-repair-result-audit.json
- parent_objective: design selector-balanced cap repair after M1592 source concentration near-pass
- derived_from: m1593-paper-route-clean-source-repair-result-audit
- blocked_by: M1592 improved clean rows but failed max clean source-edge share 0.35294117647058826 > 0.35
- supersedes: immediate second clean-source implementation, post-hoc threshold relaxation, candidate materialization after M1592 near-pass
- invalidates: None

## Success Criteria

- docs/m1594-paper-route-selector-balanced-clean-source-repair-design.md exists
- design preserves clean selector thresholds
- design preserves the 0.35 max clean source-edge share gate
- design pre-registers a stricter source-balanced selection rule
- design decides implementation, synthesis, pivot, or stop
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1592 as a pass by relaxing thresholds
- design ignores dominated/control-only evidence
- design routes directly to training PPO promotion private holdout corpus export actor-input changes or candidate materialization

## Evidence Gates

- M1594 must design a source-balanced cap repair without rerun
- M1594 must preserve the 0.35 max clean source-edge share gate
- M1594 must preserve clean selector thresholds
- M1594 must keep dominated/control-only diagnostics explicit
- M1594 must decide implementation, synthesis, pivot, or stop
- M1594 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1594-paper-route-selector-balanced-clean-source-repair-design
- type: gate
- checkpoint: docs/m1594-paper-route-selector-balanced-clean-source-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: selector_balanced_clean_source_repair_design_admit_bounded_implementation
- reason: M1594 designs stricter source-edge cap with max 12 pairs per edge and min 8 selected edges before one bounded implementation

## Next Blocker

m1595-paper-route-selector-balanced-clean-source-repair-implementation
