# m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design Research Review

## Summary

- Generated at UTC: 20260527T020223Z
- Type: gate
- Gate tier: process
- Promotion decision: combined_active_set_guarded_ppo_readiness_design_admit_m1044_smoke
- Decision reason: M1043 designs one guarded PPO smoke proposal from the new public-gate base with exact combined active-set public replay fresh OOD and behavior gates before any promotion

## Hypothesis

A guarded PPO readiness protocol can be specified for the new public-gate base using exact full-corpus gates, combined active-set retention, replay rollback, and behavior/generalization non-regression before any PPO run.

## Lineage

- parent_checkpoint: runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt
- parent_dataset: docs/m1042-v4-public-base-combined-active-set-post-promotion-synthesis.md, runs/m1040_candidate_b_combined_active_set_full_public_gate/summary.json
- parent_config: experiments/manifests/m1042-v4-public-base-combined-active-set-post-promotion-synthesis.json
- parent_objective: design guarded PPO readiness from the combined active-set public-gate base
- derived_from: m1042-v4-public-base-combined-active-set-post-promotion-synthesis
- blocked_by: new public-gate base has been promoted but PPO readiness protocol is not yet specified
- supersedes: None
- invalidates: running PPO directly from the new public-gate base without readiness gates

## Success Criteria

- readiness design artifact exists
- base checkpoint is fixed to the M1041 public-gate base
- P0 actor-input contract is explicit
- exact gates and replay gates are ordered
- row15 and row16 rollback criteria are explicit
- future smoke PPO command and stop conditions are specified
- no training or PPO occurs

## Failure Criteria

- design artifact is missing
- PPO starts
- actor inputs change
- rollback criteria are ambiguous
- private holdout is used

## Evidence Gates

- M1043 must design only; no PPO run
- M1043 must preserve P0 actor input contract
- M1043 must require exact M997, M297/M270, and combined active-set checks
- M1043 must require six public replay surfaces before any future promotion
- M1043 must define rollback conditions for row15 and row16 regressions
- M1043 must keep private holdout blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train
- do not change actor inputs
- do not use private holdout
- do not claim PPO readiness without exact and replay rollback criteria
- do not claim paper-level generalization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design
- type: gate
- checkpoint: docs/m1043-v4-public-base-combined-active-set-guarded-ppo-readiness-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_active_set_guarded_ppo_readiness_design_admit_m1044_smoke
- reason: M1043 designs one guarded PPO smoke proposal from the new public-gate base with exact combined active-set public replay fresh OOD and behavior gates before any promotion

## Next Blocker

m1044-v4-public-base-combined-active-set-guarded-ppo-smoke
