# m1575-paper-route-history-sensitive-active-set-mining-design Research Review

## Summary

- Generated at UTC: 20260529T145831Z
- Type: gate
- Gate tier: process
- Promotion decision: history_sensitive_active_set_mining_design_admit_bounded_implementation
- Decision reason: M1575 designs a miner that accepts anchors by wrong-history or donor-plus-hidden outcome degradation relative to current-frame controls

## Hypothesis

A history-sensitive active-set miner can be designed to find source-diverse anchors where policy history interventions change closed-loop outcome.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1573_source_diverse_flip_anchor_history_intervention_smoke/summary.json, docs/m1574-paper-route-source-diverse-history-intervention-result-audit.md
- parent_config: experiments/manifests/m1574-paper-route-source-diverse-history-intervention-result-audit.json
- parent_objective: design active-set mining that uses history sensitivity as the acceptance criterion
- derived_from: m1574-paper-route-source-diverse-history-intervention-result-audit
- blocked_by: M1573 history-positive evidence is source-narrow despite live intervention harness
- supersedes: candidate materialization after M1573, donor-pairing-only repair without source-sensitive mining
- invalidates: None

## Success Criteria

- docs/m1575-paper-route-history-sensitive-active-set-mining-design.md exists
- design uses history intervention outcome degradation as an acceptance criterion
- design includes current-frame substitution controls
- design pre-registers source-family and high-speed/late-reveal gates
- design blocks materialization training PPO promotion private holdout corpus export and self-ID claims

## Failure Criteria

- design document is missing
- design treats M1573 source-narrow positives as source-diverse self-ID evidence
- design omits current-frame controls
- design routes directly to training PPO promotion private holdout corpus export actor-input changes candidate materialization or implementation without gates

## Evidence Gates

- M1575 must design a bounded no-training history-sensitive active-set miner
- M1575 must use wrong-history/donor-plus-hidden outcome degradation as a primary acceptance criterion
- M1575 must include current-frame substitution controls
- M1575 must pre-register source-family and high-speed/late-reveal reporting gates
- M1575 must not run implementation smoke or history interventions
- M1575 must keep materialization training PPO promotion and private holdout blocked

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

- milestone: m1575-paper-route-history-sensitive-active-set-mining-design
- type: gate
- checkpoint: docs/m1575-paper-route-history-sensitive-active-set-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: history_sensitive_active_set_mining_design_admit_bounded_implementation
- reason: M1575 designs a miner that accepts anchors by wrong-history or donor-plus-hidden outcome degradation relative to current-frame controls

## Next Blocker

m1576-paper-route-history-sensitive-active-set-miner-implementation
