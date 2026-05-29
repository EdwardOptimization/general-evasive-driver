# m1611-paper-route-contour-aware-candidate-materialization-design Research Review

## Summary

- Generated at UTC: 20260529T180152Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_candidate_materialization_design_admit_offline_implementation
- Decision reason: M1611 designs 39-row candidate materialization with 232-row diagnostic guardrails while blocking corpus export training PPO and promotion

## Hypothesis

A design-only materialization plan can preserve M1609 primary clean evidence and diagnostic controls before any candidate export.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1609_diagnostic_complete_bounded_replay/summary.json, runs/m1609_diagnostic_complete_bounded_replay/primary_classified_rows.csv, runs/m1609_diagnostic_complete_bounded_replay/diagnostic_classified_rows.csv, docs/m1610-paper-route-diagnostic-complete-bounded-replay-result-audit.md
- parent_config: experiments/manifests/m1610-paper-route-diagnostic-complete-bounded-replay-result-audit.json
- parent_objective: design contour-aware candidate materialization after diagnostic-complete replay audit
- derived_from: m1610-paper-route-diagnostic-complete-bounded-replay-result-audit
- blocked_by: M1610 admits design-only materialization planning but still blocks actual materialization and corpus export
- supersedes: direct candidate materialization from M1609, direct training-corpus export from M1609, direct PPO after M1609
- invalidates: None

## Success Criteria

- docs/m1611-paper-route-contour-aware-candidate-materialization-design.md exists
- design preserves primary and diagnostic row separation
- row eligibility from M1609 is explicit
- source-edge and exact replay-id accounting are explicit
- post-materialization audit requirement is explicit
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design materializes candidates or exports a corpus
- design drops diagnostic guardrails
- design routes directly to training PPO promotion private holdout corpus export actor-input changes or candidate materialization

## Evidence Gates

- M1611 must design materialization without executing it
- M1611 must preserve primary and diagnostic row separation
- M1611 must define row eligibility from M1609 primary clean rows and diagnostic guardrails
- M1611 must preserve exact replay ids and source-edge accounting
- M1611 must require a post-materialization audit before corpus export or training
- M1611 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not materialize candidates
- do not export a training corpus
- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun replay
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not select diagnostics by labels
- do not relax clean selector thresholds
- do not relax the max clean source-edge share threshold
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1611-paper-route-contour-aware-candidate-materialization-design
- type: gate
- checkpoint: docs/m1611-paper-route-contour-aware-candidate-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_candidate_materialization_design_admit_offline_implementation
- reason: M1611 designs 39-row candidate materialization with 232-row diagnostic guardrails while blocking corpus export training PPO and promotion

## Next Blocker

m1612-paper-route-contour-aware-candidate-materialization-implementation
