# m1629-paper-route-contour-aware-full-target-materialization-design Research Review

## Summary

- Generated at UTC: 20260529T191829Z
- Type: gate
- Gate tier: process
- Promotion decision: contour_aware_full_target_materialization_design_admit_implementation
- Decision reason: M1629 designs full 39-positive 232-diagnostic policy-target materialization and admits exactly one bounded implementation while keeping objective update and training blocked

## Hypothesis

A full policy-target materialization design can safely scale the M1626 capture path to all 39 positive and 232 diagnostic public rows while preserving role integrity.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1628-paper-route-contour-aware-policy-target-materialization-branch-synthesis.md, runs/m1626_contour_aware_tensor_capture_dry_run/summary.json, runs/m1623_contour_aware_policy_target_traceability_preflight/summary.json, runs/m1615_contour_aware_candidate_corpus/summary.json
- parent_config: experiments/manifests/m1628-paper-route-contour-aware-policy-target-materialization-branch-synthesis.json
- parent_objective: design full contour-aware policy-target materialization
- derived_from: m1628-paper-route-contour-aware-policy-target-materialization-branch-synthesis
- blocked_by: M1628 admits design-only full target materialization and blocks implementation until design is explicit
- supersedes: direct full target materialization implementation after M1628, direct objective update after M1628, direct PPO after M1628
- invalidates: None

## Success Criteria

- docs/m1629-paper-route-contour-aware-full-target-materialization-design.md exists
- full positive and diagnostic metadata schemas are specified
- full NPZ tensor schemas are specified
- success and failure gates are explicit
- diagnostics remain used_as_positive false and role_weight 0.0
- implementation objective update training PPO promotion private holdout and actor-input changes remain blocked

## Failure Criteria

- design document is missing
- design skips full-package schema or guardrails
- design routes directly to objective update training PPO promotion private holdout or actor-input changes
- design treats diagnostics as positive targets
- design claims paper-level or level3 self-identification evidence

## Evidence Gates

- M1629 must design full 39-positive 232-diagnostic tensor materialization
- M1629 must specify metadata and NPZ tensor schemas
- M1629 must require diagnostics to stay zero-weight and non-positive
- M1629 must require full materialization audit before any loss/objective construction
- M1629 must keep training PPO promotion private holdout and actor-input changes blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not implement full materialization
- do not construct a loss
- do not construct an objective config
- do not train
- do not run PPO
- do not run actor update
- do not promote a checkpoint
- do not use private holdout
- do not add actor inputs
- do not claim level3 self-identification
- do not treat diagnostics as positive targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1629-paper-route-contour-aware-full-target-materialization-design
- type: gate
- checkpoint: docs/m1629-paper-route-contour-aware-full-target-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: contour_aware_full_target_materialization_design_admit_implementation
- reason: M1629 designs full 39-positive 232-diagnostic policy-target materialization and admits exactly one bounded implementation while keeping objective update and training blocked

## Next Blocker

m1629-paper-route-contour-aware-full-target-materialization-design
