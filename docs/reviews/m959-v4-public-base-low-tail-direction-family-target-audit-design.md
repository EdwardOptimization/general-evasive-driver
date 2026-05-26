# m959-v4-public-base-low-tail-direction-family-target-audit-design Research Review

## Summary

- Generated at UTC: 20260526T023244Z
- Type: gate
- Gate tier: process
- Promotion decision: low_tail_direction_family_target_audit_design_admit_m960
- Decision reason: M959 designs no-training direction-family target audit using M958 behavior-improving families with normal-retention terminal-margin and M267 proof-retention checks before actor training

## Hypothesis

Behavior-improving direction families from M958 can be converted into normal-retained low-tail target candidates before actor training.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m958-v4-public-base-low-tail-target-metric-artifact-audit-implementation.md, runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/summary.json, runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/direction_family_summary.csv, runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/row_metric_grounding.csv
- parent_config: experiments/manifests/m958-v4-public-base-low-tail-target-metric-artifact-audit-implementation.json
- parent_objective: design no-training target-direction audit after M958 finds direction-sign suspicion
- derived_from: m958-v4-public-base-low-tail-target-metric-artifact-audit-implementation
- blocked_by: M958 finds away-from-intervention proxy improvement is anti-aligned with terminal margin while toward/brake/throttle directions improve behavior
- supersedes: None
- invalidates: training on away-from-intervention low-tail targets before direction-family target audit

## Success Criteria

- design document exists
- candidate direction families are explicit
- normal-retention and terminal-margin criteria are explicit
- M267 proof-retention handling remains explicit
- training, PPO, and promotion remain blocked

## Failure Criteria

- design recommends actor training before target feasibility
- design changes actor inputs
- design omits M267 proof retention
- design reuses away-from-intervention targets as primary without justification

## Evidence Gates

- M959 must not train
- M959 must not run PPO
- M959 must not promote
- M959 must preserve the P0 actor-input contract
- M959 must design a no-training audit for behavior-improving direction-family target candidates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not promote
- do not train on direction-family targets before target audit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m959-v4-public-base-low-tail-direction-family-target-audit-design
- type: gate
- checkpoint: docs/m959-v4-public-base-low-tail-direction-family-target-audit-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: low_tail_direction_family_target_audit_design_admit_m960
- reason: M959 designs no-training direction-family target audit using M958 behavior-improving families with normal-retention terminal-margin and M267 proof-retention checks before actor training

## Next Blocker

low-tail direction-family target audit has not been designed
