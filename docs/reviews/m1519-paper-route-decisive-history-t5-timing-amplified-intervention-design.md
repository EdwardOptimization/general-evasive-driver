# m1519-paper-route-decisive-history-t5-timing-amplified-intervention-design Research Review

## Summary

- Generated at UTC: 20260529T094900Z
- Type: gate
- Gate tier: process
- Promotion decision: t5_timing_amplified_intervention_design_route_to_branch_synthesis
- Decision reason: M1519 designs bounded earlier-window interventions at reveal reveal-plus-four decision-minus-eight and decision anchors then routes to mandatory branch synthesis by cadence

## Hypothesis

Earlier-window interventions can test whether M1517 was null because decision-step injection was too late, while preserving no-training and no-materialization guardrails.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1518-paper-route-decisive-history-t5-intervention-result-audit.md, runs/m1517_decisive_history_t5_intervention_smoke/intervention_rows.csv, runs/m1517_decisive_history_t5_intervention_smoke/intervention_pair_summary.csv
- parent_config: experiments/manifests/m1518-paper-route-decisive-history-t5-intervention-result-audit.json
- parent_objective: design bounded earlier-window interventions after decision-step interventions produced null/weak effects
- derived_from: m1518-paper-route-decisive-history-t5-intervention-result-audit
- blocked_by: M1517 decision-step intervention starts after the policy has already reached a viable physical state
- supersedes: candidate materialization from decision-step-only null intervention rows
- invalidates: None

## Success Criteria

- docs/m1519-paper-route-decisive-history-t5-timing-amplified-intervention-design.md exists
- design defines reveal, reveal-plus-k, and decision-minus-k intervention anchors or explicitly narrows them
- design separates same-current diagnostics from diverging-trajectory timing-amplified rollouts
- design keeps candidate materialization training PPO promotion private holdout actor-input changes and corpus export blocked
- design routes to one bounded implementation or mandatory synthesis

## Failure Criteria

- design document is missing
- intervention timing or interpretation is ambiguous
- design changes actor inputs or uses private holdout
- design materializes candidates or starts training PPO promotion corpus export

## Evidence Gates

- M1519 must design bounded timing-amplified interventions for the admitted T5 high-speed subset
- M1519 must define reveal/reveal-plus-k/decision-minus-k intervention anchors and metrics
- M1519 must preserve P0 actor contract and fixed public checkpoint
- M1519 must not materialize candidates or export a training corpus
- M1519 must not train run PPO promote use private holdout or alter actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not materialize candidates during design
- do not claim self-identification from timing-amplification design

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1519-paper-route-decisive-history-t5-timing-amplified-intervention-design
- type: gate
- checkpoint: docs/m1519-paper-route-decisive-history-t5-timing-amplified-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: t5_timing_amplified_intervention_design_route_to_branch_synthesis
- reason: M1519 designs bounded earlier-window interventions at reveal reveal-plus-four decision-minus-eight and decision anchors then routes to mandatory branch synthesis by cadence

## Next Blocker

m1520-paper-route-decisive-history-bounded-runner-synthesis
