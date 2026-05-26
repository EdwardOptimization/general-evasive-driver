# m957-v4-public-base-low-tail-target-metric-artifact-audit-design Research Review

## Summary

- Generated at UTC: 20260526T015038Z
- Type: gate
- Gate tier: process
- Promotion decision: low_tail_metric_artifact_audit_design_admit_m958
- Decision reason: M957 designs no-training metric-grounding audit comparing low-tail action-gap proxy changes against closed-loop terminal margin effects before threshold relaxation or actor training

## Hypothesis

M956 indicates the current low-tail action-gap target may be a metric artifact, so the next step should design a no-training grounding audit before threshold relaxation or actor training.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m956-v4-public-base-low-tail-sequence-target-audit-implementation.md, runs/m956_v4_public_base_low_tail_sequence_target_audit/summary.json, runs/m956_v4_public_base_low_tail_sequence_target_audit/sequence_family_summary.csv, runs/m956_v4_public_base_low_tail_sequence_target_audit/low_tail_sequence_metrics.csv
- parent_config: experiments/manifests/m956-v4-public-base-low-tail-sequence-target-audit-implementation.json
- parent_objective: design a target-metric artifact audit after delayed low-tail projection sequences worsen terminal margin
- derived_from: m956-v4-public-base-low-tail-sequence-target-audit-implementation
- blocked_by: M956 finds delayed action-gap projection sequences preserve retention and M267 proof but do not improve terminal margin
- supersedes: None
- invalidates: threshold relaxation or actor training before checking low-tail metric grounding

## Success Criteria

- design document exists
- metric-artifact criteria are explicit
- closed-loop terminal margin comparison is required
- direction-sign and threshold-sensitivity routes are separated
- training, PPO, and promotion remain blocked

## Failure Criteria

- design recommends actor training before metric grounding
- design changes actor inputs
- design relaxes thresholds without a sensitivity audit
- design omits terminal margin comparison

## Evidence Gates

- M957 must not train
- M957 must not run PPO
- M957 must not promote
- M957 must preserve the P0 actor-input contract
- M957 must design a no-training audit comparing low-tail action-gap metrics to closed-loop terminal margin effects

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not relax thresholds without a registered sensitivity plan
- do not change actor inputs
- do not use private holdout
- do not promote

## Failure Taxonomy

- none

## Scoreboard

- milestone: m957-v4-public-base-low-tail-target-metric-artifact-audit-design
- type: gate
- checkpoint: docs/m957-v4-public-base-low-tail-target-metric-artifact-audit-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: low_tail_metric_artifact_audit_design_admit_m958
- reason: M957 designs no-training metric-grounding audit comparing low-tail action-gap proxy changes against closed-loop terminal margin effects before threshold relaxation or actor training

## Next Blocker

m958-v4-public-base-low-tail-target-metric-artifact-audit-implementation
