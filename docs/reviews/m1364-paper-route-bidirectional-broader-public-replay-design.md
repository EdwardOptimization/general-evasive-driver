# m1364-paper-route-bidirectional-broader-public-replay-design Research Review

## Summary

- Generated at UTC: 20260528T204042Z
- Type: gate
- Gate tier: process
- Promotion decision: bidirectional_broader_public_replay_design_admit_implementation
- Decision reason: M1364 designs six-surface public replay plus protected diagnostics and behavior ordering for M1362 alpha 0.1

## Hypothesis

M1362 alpha 0.1 should be escalated to a broader public replay design before any PPO, private holdout, or promotion route.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1363-paper-route-bidirectional-interpolation-result-audit.md, runs/m1362_bidirectional_active_set_interpolation_preflight/summary.json, runs/m1362_bidirectional_active_set_interpolation_preflight/alpha_summary.csv
- parent_config: experiments/manifests/m1363-paper-route-bidirectional-interpolation-result-audit.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: design a broader public replay escalation gate for the M1362 alpha 0.1 candidate
- derived_from: m1363-paper-route-bidirectional-interpolation-result-audit
- blocked_by: M1362 alpha 0.1 has passed only exact metrics plus M267/M264 and M183/M170 preflight
- supersedes: direct promotion after M1362, direct PPO after M1362, direct private holdout after M1362, more two-surface-only alpha tuning
- invalidates: None

## Success Criteria

- docs/m1364-paper-route-bidirectional-broader-public-replay-design.md exists
- design lists the six replay surfaces
- design defines exact non-regression checks
- design orders replay before protected-key diagnostics and behavior seeds
- design blocks promotion and private holdout
- no training, PPO, replay, promotion, private holdout, threshold relaxation, actor update, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits broad replay surfaces
- design routes directly to promotion or private holdout
- design omits exact non-regression
- training, PPO, replay, private holdout, promotion, threshold relaxation, actor update, or actor-input expansion occurs

## Evidence Gates

- M1364 must not train
- M1364 must not run PPO
- M1364 must not run replay
- M1364 must not update actor weights
- M1364 must not use private holdout
- M1364 must not promote
- M1364 must design six-surface public replay before protected-key and behavior gates

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

- milestone: m1364-paper-route-bidirectional-broader-public-replay-design
- type: gate
- checkpoint: docs/m1364-paper-route-bidirectional-broader-public-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bidirectional_broader_public_replay_design_admit_implementation
- reason: M1364 designs six-surface public replay plus protected diagnostics and behavior ordering for M1362 alpha 0.1

## Next Blocker

m1365-paper-route-bidirectional-broader-public-replay
