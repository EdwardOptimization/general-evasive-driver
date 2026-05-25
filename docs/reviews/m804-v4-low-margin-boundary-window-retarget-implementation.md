# m804-v4-low-margin-boundary-window-retarget-implementation Research Review

## Summary

- Generated at UTC: 20260525T061228Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_low_margin_boundary_window_geometry_only_diagnostic
- Decision reason: M804 creates 252 primary-window rows but they all come from obstacle-half-width retargeting and fail seed axis and fault-pair dominance gates

## Hypothesis

A no-training boundary-window retarget tool can convert M801 collision-side and nearest-safe anchors into a source-diverse primary low-margin normal guard corpus without relaxing the margin gate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m803-v4-low-margin-boundary-window-retarget-design.md, docs/m802-v4-low-margin-source-diverse-corpus-refresh-audit.md, runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv, runs/m801_v4_low_margin_source_diverse_corpus_refresh/diagnostic_margin_bands.csv, runs/m801_v4_low_margin_refresh_corpus_export/positive_sequence_outcomes.csv, runs/m801_v4_low_margin_refresh_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m803-v4-low-margin-boundary-window-retarget-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement no-training boundary-window retargeting around M801 collision/success transition
- derived_from: m803-v4-low-margin-boundary-window-retarget-design
- blocked_by: m801-v4-low-margin-source-diverse-corpus-refresh-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M804 writes boundary anchor, retarget plan, retarget replay, accepted row, axis summary, progress, and summary artifacts
- M804 reports accepted rows, unique seeds, unique source indices, fault-family pairs, dominance metrics, and retarget-axis diagnostics
- M804 confirms actor and residual-head checksums unchanged
- M804 classifies the result without widening the primary margin gate
- M804 keeps residual calibration, PPO, and promotion blocked

## Failure Criteria

- implementation trains actor, residual head, or a new calibrator
- implementation runs PPO
- implementation promotes a checkpoint
- implementation omits source-diversity or retarget-axis diagnostics
- implementation treats diagnostic wider bands as primary-pass evidence
- implementation changes margin by post-processing rather than closed-loop replay

## Evidence Gates

- M804 implements and runs only no-training boundary-window retargeting
- M804 preserves the P0 human-view actor contract
- M804 keeps alpha 0.2 and the primary <=0.00005 margin threshold unchanged
- M804 reruns closed-loop candidates instead of post-processing margins
- M804 confirms actor and M761 residual-head checksums unchanged
- M804 blocks residual calibration, PPO, and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not train a new residual calibrator
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not widen the primary 0.00005 margin threshold
- do not count collision rows as primary low-margin successes
- do not post-process obstacle radius after rollout to change margin
- do not treat residual alpha scans as candidate evidence
- do not claim true wheel-level faults from current single-track proxy data
- do not tune from private holdout failures

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m804-v4-low-margin-boundary-window-retarget-implementation
- type: infrastructure
- checkpoint: runs/m804_v4_low_margin_boundary_window_retarget/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_low_margin_boundary_window_geometry_only_diagnostic
- reason: M804 creates 252 primary-window rows but they all come from obstacle-half-width retargeting and fail seed axis and fault-pair dominance gates

## Next Blocker

m805-v4-low-margin-boundary-window-retarget-audit
