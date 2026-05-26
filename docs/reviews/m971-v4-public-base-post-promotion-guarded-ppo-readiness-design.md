# m971-v4-public-base-post-promotion-guarded-ppo-readiness-design Research Review

## Summary

- Generated at UTC: 20260526T090524Z
- Type: gate
- Gate tier: process
- Promotion decision: post_promotion_guarded_ppo_readiness_design_admit_m972
- Decision reason: M971 designs a 1024-step guarded PPO smoke proposal from alpha 1.0 with proof fresh-generalization behavior gates and rollback criteria

## Hypothesis

A guarded PPO readiness protocol can be designed for the promoted alpha_1_0 public-gate base without weakening proof, generalization, behavior, or actor-input constraints.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m970-v4-public-base-direction-target-actor-fit-post-promotion-synthesis.md, docs/m969-v4-public-base-direction-target-actor-fit-promotion-audit.md, runs/m968_v4_public_base_direction_target_actor_fit_promotion_generalization_gate/summary.json
- parent_config: experiments/manifests/m970-v4-public-base-direction-target-actor-fit-post-promotion-synthesis.json
- parent_objective: design guarded PPO readiness from the newly promoted alpha_1_0 public-gate base
- derived_from: m970-v4-public-base-direction-target-actor-fit-post-promotion-synthesis, m969-v4-public-base-direction-target-actor-fit-promotion-audit
- blocked_by: alpha_1_0 is the public-gate base, but no guarded PPO readiness protocol exists
- supersedes: None
- invalidates: running PPO from alpha_1_0 without pre-registered proof/generalization retention and rollback criteria

## Success Criteria

- design document exists
- base checkpoint is explicit
- PPO proposal config is scoped
- proof replay retention gates are explicit
- fresh generalization and behavior gates are explicit
- rollback or rejection criteria are explicit
- training, PPO, and private holdout remain blocked

## Failure Criteria

- design runs PPO
- design changes actor inputs
- design omits M966/M968 retention gates
- design omits fresh generalization
- design lacks rollback criteria
- design uses private holdout

## Evidence Gates

- M971 must not train
- M971 must not run PPO
- M971 must not use private holdout
- M971 must preserve the P0 actor-input contract
- M971 must specify proof retention gates before PPO
- M971 must specify fresh generalization and behavior gates before PPO
- M971 must specify rollback or rejection criteria for PPO proposals

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not run PPO
- do not use private holdout
- do not treat alpha_1_0 promotion as permission for unguarded PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m971-v4-public-base-post-promotion-guarded-ppo-readiness-design
- type: gate
- checkpoint: docs/m971-v4-public-base-post-promotion-guarded-ppo-readiness-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_promotion_guarded_ppo_readiness_design_admit_m972
- reason: M971 designs a 1024-step guarded PPO smoke proposal from alpha 1.0 with proof fresh-generalization behavior gates and rollback criteria

## Next Blocker

guarded PPO readiness has not been designed for the promoted alpha_1_0 public-gate base
