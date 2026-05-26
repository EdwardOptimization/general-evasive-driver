# m977-v4-public-base-post-promotion-exact-repair-promotion-audit Research Review

## Summary

- Generated at UTC: 20260526T110814Z
- Type: gate
- Gate tier: promotion
- Promotion decision: exact_repair_promote_public_gate_base
- Decision reason: M977 promotes the M974 exact-repaired candidate as current public-gate base while PPO private holdout and paper-level claims remain blocked

## Hypothesis

The M974 exact-repaired candidate has enough public proof, fresh generalization, and behavior evidence to be promoted as the new public-gate base while keeping PPO, private-holdout, paper-level, and real-vehicle claims blocked.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m974-v4-public-base-post-promotion-exact-repair-projection-probe.md, docs/m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation.md, runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/summary.json
- parent_config: experiments/manifests/m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation.json
- parent_objective: audit whether the M974 exact-repaired candidate should replace alpha_1_0 as the current public-gate base
- derived_from: m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation, m974-v4-public-base-post-promotion-exact-repair-projection-probe
- blocked_by: M976 classifies the exact-repaired candidate as a full public-gate candidate but promotion has not been audited
- supersedes: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt as current public-gate base
- invalidates: using M974 exact-repaired candidate as public-gate base without promotion audit

## Success Criteria

- audit document exists
- M974 exact and first-replay evidence is cited
- M976 full public gate evidence is cited
- promotion or rejection decision is explicit
- current-status public-gate base is updated if promoted
- PPO and private holdout remain blocked

## Failure Criteria

- audit promotes without checking M974 and M976 evidence
- audit changes actor inputs
- audit runs PPO
- audit uses private holdout evidence
- audit omits promotion caveats

## Evidence Gates

- M977 must not train
- M977 must not run PPO
- M977 must not use private holdout
- M977 must preserve the P0 actor-input contract
- M977 must verify M974 exact/first-replay pass
- M977 must verify M976 full public proof/generalization/behavior pass
- M977 must explicitly decide whether to update the public-gate base

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not run PPO
- do not claim paper-level or real-vehicle validation
- do not promote without recording caveats

## Failure Taxonomy

- none

## Scoreboard

- milestone: m977-v4-public-base-post-promotion-exact-repair-promotion-audit
- type: gate
- checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: exact_repair_promote_public_gate_base
- reason: M977 promotes the M974 exact-repaired candidate as current public-gate base while PPO private holdout and paper-level claims remain blocked

## Next Blocker

m978-v4-public-base-post-exact-repair-promotion-synthesis
