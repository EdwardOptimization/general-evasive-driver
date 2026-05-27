# m1045-v4-public-base-combined-active-set-guarded-ppo-promotion-audit Research Review

## Summary

- Generated at UTC: 20260527T023348Z
- Type: gate
- Gate tier: promotion
- Promotion decision: combined_active_set_guarded_ppo_promote_public_gate_base
- Decision reason: M1045 promotes the M1044 raw PPO checkpoint as current public-gate base after full public gate pass; scope remains public-gate only

## Hypothesis

The M1044 raw PPO checkpoint should replace the combined active-set base as the current public-gate base if M1044 evidence is complete and promotion remains scoped to public-gate status.

## Lineage

- parent_checkpoint: runs/m1038_candidate_b_combined_active_set_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a0_15.pt, runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
- parent_dataset: docs/m1044-v4-public-base-combined-active-set-guarded-ppo-smoke.md, runs/m1044_v4_public_base_combined_active_set_guarded_ppo_smoke/summary.json
- parent_config: configs/ppo_m1044_combined_active_set_guarded_smoke.json, experiments/manifests/m1044-v4-public-base-combined-active-set-guarded-ppo-smoke.json
- parent_objective: audit whether the M1044 raw PPO checkpoint should replace the combined active-set base as the current public-gate base
- derived_from: m1044-v4-public-base-combined-active-set-guarded-ppo-smoke
- blocked_by: M1044 classifies the raw PPO checkpoint as a public-gate raw candidate but does not promote
- supersedes: None
- invalidates: using the M1044 raw PPO checkpoint as the public base before explicit promotion audit

## Success Criteria

- promotion audit artifact exists
- M1044 evidence is summarized
- promotion decision is explicit
- current-status and scoreboard lineage are updated if promoted
- PPO, private holdout, multi-seed, long-run, and paper-level claims remain blocked

## Failure Criteria

- promotion decision is missing
- promotion occurs without current-status update
- private holdout is used
- PPO starts
- long-run PPO stability is claimed
- paper-level generalization is claimed

## Evidence Gates

- M1045 must audit M1044 evidence
- M1045 must decide promote or reject for public-gate base status
- M1045 must not train or run PPO
- M1045 must not use private holdout
- M1045 must preserve actor input contract
- M1045 must scope any promotion to public-gate base status only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not change actor inputs
- do not use private holdout
- do not promote without updating current status and scoreboard lineage
- do not claim multi-seed PPO repeatability
- do not claim long-run PPO stability
- do not claim paper-level generalization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1045-v4-public-base-combined-active-set-guarded-ppo-promotion-audit
- type: driver_candidate
- checkpoint: runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: combined_active_set_guarded_ppo_promote_public_gate_base
- reason: M1045 promotes the M1044 raw PPO checkpoint as current public-gate base after full public gate pass; scope remains public-gate only

## Next Blocker

m1046-v4-public-base-guarded-ppo-post-promotion-synthesis
