# m1427-paper-route-bounded-relocation-replay-design Research Review

## Summary

- Generated at UTC: 20260529T021908Z
- Type: gate
- Gate tier: process
- Promotion decision: bounded_relocation_replay_design_admit_implementation
- Decision reason: M1427 designs a no-training bounded relocation replay probe and admits implementation with focused tests only

## Hypothesis

A bounded relocation replay probe can test whether M1425's action-divergent proxy pressure rows become actual history-positive terminal-margin rows under relocated obstacle geometry.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv, docs/m1426-paper-route-action-divergent-pressure-result-audit.md
- parent_config: experiments/manifests/m1426-paper-route-action-divergent-pressure-result-audit.json
- parent_objective: design bounded no-training relocation replay probe after proxy source rows have zero history-positive margin separation
- derived_from: m1426-paper-route-action-divergent-pressure-result-audit
- blocked_by: M1426 admits design-only bounded relocation replay route before any replay run
- supersedes: threshold lowering after M1425, training from proxy rows, direct large replay sweep without design
- invalidates: None

## Success Criteria

- docs/m1427-paper-route-bounded-relocation-replay-design.md exists
- design specifies trace reconstruction inputs and replay variants
- design specifies relocation bounds and candidate caps
- design specifies actual replay success criteria separate from proxy criteria
- design chooses a non-training next route without running replay training PPO promotion private holdout corpus export or actor-input changes

## Failure Criteria

- design document is missing
- design requires actor input changes
- design counts M1425 proxy rows as actual replay evidence
- design routes directly to training PPO promotion private holdout corpus export or claim expansion
- design ignores reset and zero-current controls

## Evidence Gates

- M1427 must design bounded relocation replay before implementation or run
- M1427 must keep relocation as scenario generation and not actor input
- M1427 must pre-register source caps success criteria failure criteria and forbidden shortcuts
- M1427 must not run replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export a training corpus
- do not lower M1425 thresholds after seeing the result
- do not count proxy rows as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1427-paper-route-bounded-relocation-replay-design
- type: gate
- checkpoint: docs/m1427-paper-route-bounded-relocation-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bounded_relocation_replay_design_admit_implementation
- reason: M1427 designs a no-training bounded relocation replay probe and admits implementation with focused tests only

## Next Blocker

m1428-paper-route-bounded-relocation-replay-implementation
