# m1598-paper-route-clean-active-set-contour-mapping-design Research Review

## Summary

- Generated at UTC: 20260529T165836Z
- Type: gate
- Gate tier: process
- Promotion decision: clean_active_set_contour_mapping_design_admit_offline_implementation
- Decision reason: M1598 designs label-preserving offline contour mapper over M1588 M1592 M1595 before any replay

## Hypothesis

Offline contour mapping can explain why M1592 was near-pass and M1595 failed before another replay is attempted.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1588_history_vs_control_active_set_selector/classified_directed_pair_rows.csv, runs/m1592_clean_history_control_source_generation_repair_smoke/classified_directed_pair_rows.csv, runs/m1595_selector_balanced_clean_source_repair_smoke/classified_directed_pair_rows.csv, docs/m1597-paper-route-clean-source-repair-branch-synthesis.md
- parent_config: experiments/manifests/m1597-paper-route-clean-source-repair-branch-synthesis.json
- parent_objective: design offline clean active-set contour mapping after local cap tuning failed
- derived_from: m1597-paper-route-clean-source-repair-branch-synthesis
- blocked_by: M1592 near-pass and M1595 negative show active-set sensitivity, further local cap tuning risks public-row overfit
- supersedes: another direct cap-tuning implementation, candidate materialization from M1592 near-pass, training corpus export from public clean rows
- invalidates: None

## Success Criteria

- docs/m1598-paper-route-clean-active-set-contour-mapping-design.md exists
- design pre-registers contour input artifacts
- design pre-registers contour features and label taxonomy
- design decides implementation, synthesis, pivot, or stop
- training PPO promotion private holdout corpus export materialization replay and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design treats M1592 as materialization or level3 self-ID evidence
- design ignores M1595 negative result
- design routes directly to training PPO promotion private holdout corpus export actor-input changes or candidate materialization

## Evidence Gates

- M1598 must design offline contour mapping over existing public artifacts
- M1598 must pre-register contour features and label splits
- M1598 must preserve clean selector thresholds and source-share gate
- M1598 must decide implementation, synthesis, pivot, or stop
- M1598 must keep replay materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run replay
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
- objective_overfit

## Scoreboard

- milestone: m1598-paper-route-clean-active-set-contour-mapping-design
- type: gate
- checkpoint: docs/m1598-paper-route-clean-active-set-contour-mapping-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: clean_active_set_contour_mapping_design_admit_offline_implementation
- reason: M1598 designs label-preserving offline contour mapper over M1588 M1592 M1595 before any replay

## Next Blocker

m1599-paper-route-clean-active-set-contour-mapper-implementation
