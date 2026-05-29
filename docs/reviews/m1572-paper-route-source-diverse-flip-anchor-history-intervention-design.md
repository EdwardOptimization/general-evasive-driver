# m1572-paper-route-source-diverse-flip-anchor-history-intervention-design Research Review

## Summary

- Generated at UTC: 20260529T144014Z
- Type: gate
- Gate tier: process
- Promotion decision: source_diverse_flip_anchor_history_intervention_design_admit_bounded_implementation
- Decision reason: M1572 designs bounded history interventions over 14 source-diverse M1570 flip anchors with current-frame substitution controls

## Hypothesis

A bounded history-intervention experiment can be designed over the M1570 source-diverse flip-anchor active set without weakening self-ID evidence standards.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1570_targeted_third_source_flip_anchor_smoke/summary.json, runs/m1570_targeted_third_source_flip_anchor_smoke/flip_anchor_rows.csv, docs/m1571-paper-route-targeted-third-source-flip-anchor-result-audit.md
- parent_config: experiments/manifests/m1571-paper-route-targeted-third-source-flip-anchor-result-audit.json
- parent_objective: design bounded history interventions over the M1570 source-diverse flip-anchor active set
- derived_from: m1571-paper-route-targeted-third-source-flip-anchor-result-audit
- blocked_by: history-intervention design over M1570 flip anchors does not exist yet
- supersedes: direct history-intervention implementation without design, candidate materialization after source-generation pass
- invalidates: None

## Success Criteria

- docs/m1572-paper-route-source-diverse-flip-anchor-history-intervention-design.md exists
- design names target anchor artifacts
- design includes wrong-history donor hidden and donor response/action plus hidden variants
- design includes reset, delayed, zero-current, zero-action-history, and zero-all controls
- design pre-registers source-family and window gates
- design reports high-speed and late-reveal families separately
- training PPO promotion private holdout corpus export materialization and self-ID claims remain blocked

## Failure Criteria

- design document is missing
- design omits source-diversity or current-frame substitution controls
- design treats M1570 source generation as level3 self-ID evidence
- design routes directly to training PPO promotion private holdout corpus export actor-input changes candidate materialization or implementation without gates

## Evidence Gates

- M1572 must design bounded history interventions over the M1570 source-diverse flip anchors
- M1572 must include wrong-history donor hidden, donor response/action plus hidden, delayed hidden, reset hidden, zero-current, zero-action-history, and zero-all controls
- M1572 must pre-register source-family and window coverage gates
- M1572 must report high-speed and late-reveal families separately
- M1572 must not run history interventions or simulator smoke
- M1572 must keep materialization training PPO promotion and private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run implementation smoke
- do not rerun simulator
- do not run history interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1572-paper-route-source-diverse-flip-anchor-history-intervention-design
- type: gate
- checkpoint: docs/m1572-paper-route-source-diverse-flip-anchor-history-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_diverse_flip_anchor_history_intervention_design_admit_bounded_implementation
- reason: M1572 designs bounded history interventions over 14 source-diverse M1570 flip anchors with current-frame substitution controls

## Next Blocker

m1573-paper-route-source-diverse-flip-anchor-history-intervention-implementation
