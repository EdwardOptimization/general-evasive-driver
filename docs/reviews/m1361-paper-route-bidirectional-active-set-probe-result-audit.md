# m1361-paper-route-bidirectional-active-set-probe-result-audit Research Review

## Summary

- Generated at UTC: 20260528T203242Z
- Type: gate
- Gate tier: process
- Promotion decision: bidirectional_active_set_probe_audit_route_to_interpolation_preflight
- Decision reason: M1361 classifies M1360 as a narrow M267 margin-gap washout and routes to interpolation preflight before new gap-aware terms

## Hypothesis

M1360's bidirectional active-set result should be classified as a narrower M267 margin-gap proof washout and routed before any coefficient tuning or PPO.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1360_bidirectional_active_set_probe/checkpoints/raw_bidirectional_active_set_update.pt
- parent_dataset: docs/m1360-paper-route-bidirectional-active-set-probe-implementation.md, runs/m1360_bidirectional_active_set_probe/summary.json, runs/m1360_bidirectional_active_set_probe/replay/m267_m264/summary.json
- parent_config: experiments/manifests/m1360-paper-route-bidirectional-active-set-probe-implementation.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: audit M1360 exact-positive but M267 margin-gap-negative bidirectional active-set result
- derived_from: m1360-paper-route-bidirectional-active-set-probe-implementation
- blocked_by: M1360 improves exact metrics and preserves success-drop count but fails M267/M264 margin-gap retention
- supersedes: direct coefficient tuning after M1360, direct PPO after M1360, direct promotion after M1360
- invalidates: None

## Success Criteria

- docs/m1361-paper-route-bidirectional-active-set-probe-result-audit.md exists
- audit records M1360 exact metrics
- audit records M1360 M267/M264 success-count retention
- audit records M1360 M267/M264 margin-gap failure
- audit routes to a specific next design
- no training, PPO, replay, promotion, private holdout, threshold relaxation, actor update, or actor-input expansion occurs

## Failure Criteria

- audit document is missing
- audit omits M1360 exact or replay evidence
- audit treats M1360 as promotion
- audit routes directly to PPO
- training, PPO, replay, private holdout, promotion, threshold relaxation, actor update, or actor-input expansion occurs

## Evidence Gates

- M1361 must not train
- M1361 must not run PPO
- M1361 must not run replay
- M1361 must not update actor weights
- M1361 must not use private holdout
- M1361 must not promote
- M1361 must classify whether M1360 failure is interpolation-addressable or needs a new gap-aware term

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
- do not update actor weights
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax thresholds
- do not claim driver performance
- do not claim strong self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1361-paper-route-bidirectional-active-set-probe-result-audit
- type: gate
- checkpoint: docs/m1361-paper-route-bidirectional-active-set-probe-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_active_set_probe_audit_route_to_interpolation_preflight
- reason: M1361 classifies M1360 as a narrow M267 margin-gap washout and routes to interpolation preflight before new gap-aware terms

## Next Blocker

m1362-paper-route-bidirectional-active-set-interpolation-preflight
