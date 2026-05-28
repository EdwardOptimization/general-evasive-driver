# m1254-paper-route-capability-separable-event-timing-source-design Research Review

## Summary

- Generated at UTC: 20260528T110726Z
- Type: gate
- Gate tier: process
- Promotion decision: event_timing_source_design_admit_bounded_smoke
- Decision reason: M1254 designs no-training event-timing/source-state source mining and admits bounded M1255 smoke

## Hypothesis

Changing source-state/event timing can determine whether the trajectory proposal near-miss is a timing artifact rather than an action proposal limitation.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit.md, runs/m1252_capability_separable_proposal_margin_restoration_smoke/summary.json, runs/m1252_capability_separable_proposal_margin_restoration_smoke/matched_capability_pairs.csv
- parent_config: experiments/manifests/m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit.json
- parent_objective: design event-timing/source-state source mining after trajectory proposal near-miss remains zero-accepted
- derived_from: m1253-paper-route-capability-separable-trajectory-proposal-source-variable-audit
- blocked_by: M1253 stops same trajectory proposal budget and selects source-state/event timing as the next variable
- supersedes: another proposal-budget expansion on the same source states
- invalidates: None

## Success Criteria

- docs/m1254-paper-route-capability-separable-event-timing-source-design.md exists
- design names source-state/timing variables
- design names acceptance metrics and thresholds
- design names runtime bounds
- design names no-leak actor contract guardrails
- M1255 bounded no-training smoke manifest exists
- no training, PPO, promotion, private holdout, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design feeds timing/proposal labels or oracle outcomes into actor inputs
- design lacks acceptance gates
- training, PPO, private holdout, promotion, or actor-input expansion occurs

## Evidence Gates

- M1254 must preserve actor input contract
- M1254 must not train controllers
- M1254 must not run PPO
- M1254 must not use private holdout
- M1254 must not promote
- M1254 must define a no-training event-timing/source-state source protocol

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, timing labels, proposal labels, oracle outcomes, or search outputs to actor inputs
- do not lower accepted source thresholds
- do not claim self-identification from source design

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1254-paper-route-capability-separable-event-timing-source-design
- type: gate
- checkpoint: docs/m1254-paper-route-capability-separable-event-timing-source-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: event_timing_source_design_admit_bounded_smoke
- reason: M1254 designs no-training event-timing/source-state source mining and admits bounded M1255 smoke

## Next Blocker

m1255-paper-route-capability-separable-event-timing-source-smoke
