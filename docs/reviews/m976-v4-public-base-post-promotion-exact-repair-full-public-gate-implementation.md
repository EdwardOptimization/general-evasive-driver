# m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation Research Review

## Summary

- Generated at UTC: 20260526T110814Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: exact_repair_full_public_gate_candidate_route_to_promotion_audit
- Decision reason: M976 passes six public replay surfaces source-diverse diagnostic fresh generalization and behavior gates without promotion

## Hypothesis

The M974 base-start exact-repaired candidate can pass the full public proof/generalization/behavior stack versus alpha_1_0 without PPO, private holdout, or actor-input changes.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design.md, runs/m974_exact_repair_from_base_s40_seed5974/summary.json, runs/m974_base_s40_m267_m264_first_replay/summary.json, runs/m974_base_s40_m183_m170_first_replay/summary.json
- parent_config: experiments/manifests/m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design.json
- parent_objective: run no-training full public proof/generalization/behavior gate for the M974 selected exact-repaired candidate
- derived_from: m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design, m974-v4-public-base-post-promotion-exact-repair-projection-probe
- blocked_by: M974 candidate has only exact and first-replay evidence
- supersedes: None
- invalidates: promotion of M974 candidate before full public gate

## Success Criteria

- summary artifact exists
- all six public replay surfaces pass
- source-diverse protected diagnostic is written
- fresh public and moderate-OOD generalization comparisons pass
- behavior/ablation gates pass
- no PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- any public proof replay surface fails
- fresh public or moderate-OOD comparison regresses beyond tolerance
- behavior/ablation gate fails
- actor input contract changes
- checkpoint is promoted

## Evidence Gates

- preserve human-view P0 actor input contract
- run no PPO and no optimizer
- run six public replay surfaces
- run source-diverse protected diagnostic and old-key diagnostic
- run fresh public and moderate-OOD generalization comparisons
- run behavior seeds with reset and zero-all ablations
- do not promote; route to a later promotion audit only if all gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train or optimize
- do not use private holdout
- do not skip failed proof surfaces
- do not promote directly from M976
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation
- type: driver_candidate
- checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: exact_repair_full_public_gate_candidate_route_to_promotion_audit
- reason: M976 passes six public replay surfaces source-diverse diagnostic fresh generalization and behavior gates without promotion

## Next Blocker

m977-v4-public-base-post-promotion-exact-repair-promotion-audit
