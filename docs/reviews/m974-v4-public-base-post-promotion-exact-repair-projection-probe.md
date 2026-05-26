# m974-v4-public-base-post-promotion-exact-repair-projection-probe Research Review

## Summary

- Generated at UTC: 20260526T102402Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: exact_repair_projection_first_replay_pass_route_to_full_public_gate_design
- Decision reason: M974 selects base-start exact repair candidate after exact M297/M270 and M267/M264 plus M183/M170 first replay pass

## Hypothesis

The M972 raw PPO proposal contains useful movement that can be repaired by exact full-corpus projection while retaining M297/M270 and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/ppo_m972_post_promotion_guarded_smoke_seed5972/checkpoint.pt
- parent_dataset: docs/m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design.md, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
- parent_config: experiments/manifests/m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design.json
- parent_objective: generate no-PPO exact repair/projection candidates for the M972 raw PPO proposal and gate exact objectives before first replay
- derived_from: m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design, m972-v4-public-base-post-promotion-guarded-ppo-smoke-implementation
- blocked_by: M972 raw PPO checkpoint fails M267/M264 success-drop retention 17 -> 15
- supersedes: None
- invalidates: promotion of M972 raw PPO checkpoint, longer PPO before exact repair/projection probe

## Success Criteria

- raw-start, base-start, and line-boundary candidates are generated or explicit failures are logged
- at least one candidate passes exact M297 and M270 no-regression versus alpha_1_0
- selected exact-passing candidate passes M267/M264 first replay
- selected exact-passing candidate passes M183/M170 first replay
- no PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- all candidates regress exact M297 or M270
- exact-passing candidate fails M267/M264 first replay
- exact-passing candidate fails M183/M170 first replay
- repair only reproduces base-equivalent movement with no useful raw proposal retention
- actor input contract is changed

## Evidence Gates

- preserve human-view P0 actor input contract
- run no PPO
- produce raw-start, base-start, and line-boundary exact repair candidates
- exact M297 candidate loss must not regress versus alpha_1_0
- exact M270 candidate loss must not regress versus alpha_1_0
- only exact-passing candidates may enter M267/M264 and M183/M170 first replay gates
- do not promote unless a later full public gate passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run medium or long PPO
- do not run full replay for exact-regressing candidates
- do not use private holdout
- do not change actor inputs
- do not relax M267/M264 success-drop retention

## Failure Taxonomy

- none

## Scoreboard

- milestone: m974-v4-public-base-post-promotion-exact-repair-projection-probe
- type: driver_candidate
- checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: exact_repair_projection_first_replay_pass_route_to_full_public_gate_design
- reason: M974 selects base-start exact repair candidate after exact M297/M270 and M267/M264 plus M183/M170 first replay pass

## Next Blocker

m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design
