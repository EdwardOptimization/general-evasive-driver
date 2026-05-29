# m1568-paper-route-targeted-third-source-flip-anchor-design Research Review

## Summary

- Generated at UTC: 20260529T141528Z
- Type: gate
- Gate tier: process
- Promotion decision: targeted_third_source_flip_anchor_design_route_to_mandatory_branch_synthesis
- Decision reason: M1568 designs final targeted high-speed and late-reveal repair but routes to mandatory branch synthesis before implementation

## Hypothesis

A targeted design can focus the next source-generation repair on high_speed and late_reveal third-source flip anchors without weakening the evidence standard.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1566_flip_anchor_source_generation_repair_smoke/summary.json, docs/m1567-paper-route-flip-anchor-repair-result-audit.md
- parent_config: experiments/manifests/m1567-paper-route-flip-anchor-repair-result-audit.json
- parent_objective: design one targeted repair for a third flip source family after M1566 near-miss
- derived_from: m1567-paper-route-flip-anchor-repair-result-audit
- blocked_by: M1566 high_speed and late_reveal families have strong recoverable anchors but zero flip anchors
- supersedes: direct history interventions after M1566, another broad generator without third-source targeting
- invalidates: None

## Success Criteria

- docs/m1568-paper-route-targeted-third-source-flip-anchor-design.md exists
- design targets high_speed and late_reveal third-source flip anchors
- design includes a mandatory branch-synthesis fallback if the next implementation still lacks a third flip source family
- design keeps history interventions materialization training PPO promotion private holdout actor-input changes and training-corpus export blocked
- the next route is explicit

## Failure Criteria

- design document is missing
- design routes directly to history interventions training promotion private holdout or materialization
- design changes actor inputs or weakens the evidence standard
- design omits the mandatory synthesis fallback

## Evidence Gates

- M1568 must design a targeted repair for t5_high_speed_close_obstacle and late_reveal_boundary flip anchors
- M1568 must pre-register a hard stop requiring branch synthesis if the next implementation still lacks a third flip source family
- M1568 must not run simulator or history interventions
- M1568 must preserve P0 actor input contract
- M1568 must keep materialization training PPO promotion and private holdout blocked

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

- milestone: m1568-paper-route-targeted-third-source-flip-anchor-design
- type: gate
- checkpoint: docs/m1568-paper-route-targeted-third-source-flip-anchor-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: targeted_third_source_flip_anchor_design_route_to_mandatory_branch_synthesis
- reason: M1568 designs final targeted high-speed and late-reveal repair but routes to mandatory branch synthesis before implementation

## Next Blocker

m1569-paper-route-recoverable-active-set-generation-branch-synthesis
