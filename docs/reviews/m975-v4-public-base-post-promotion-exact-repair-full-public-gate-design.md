# m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design Research Review

## Summary

- Generated at UTC: 20260526T102815Z
- Type: gate
- Gate tier: proof
- Promotion decision: exact_repair_full_public_gate_design_admit_m976
- Decision reason: M975 designs full public proof generalization behavior gate for the M974 exact-repaired candidate before promotion audit

## Hypothesis

The M974 base-start exact-repaired candidate should be evaluated through the full public proof/generalization/behavior stack before any promotion audit.

## Lineage

- parent_checkpoint: runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt, runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m974-v4-public-base-post-promotion-exact-repair-projection-probe.md, runs/m974_exact_repair_from_base_s40_seed5974/summary.json, runs/m974_base_s40_m267_m264_first_replay/summary.json, runs/m974_base_s40_m183_m170_first_replay/summary.json
- parent_config: experiments/manifests/m974-v4-public-base-post-promotion-exact-repair-projection-probe.json
- parent_objective: design full public gate for the M974 exact-repaired base-start candidate after exact M297/M270 and first replay pass
- derived_from: m974-v4-public-base-post-promotion-exact-repair-projection-probe, m973-v4-public-base-post-promotion-ppo-exact-repair-projection-design
- blocked_by: M974 selected candidate has only first replay evidence, not full public gate evidence
- supersedes: None
- invalidates: promotion of M974 candidate before full public proof/generalization/behavior gates

## Success Criteria

- M975 writes a full public-gate design document
- the design names the selected M974 checkpoint and alpha_1_0 baseline
- the design requires six public replay surfaces
- the design requires fresh public, moderate OOD, and behavior/ablation comparisons
- the design blocks PPO, private holdout, and promotion

## Failure Criteria

- design promotes from first replay only
- design skips public replay surfaces
- design changes actor inputs
- design uses private holdout
- design allows PPO continuation before full gate

## Evidence Gates

- M975 must not run PPO
- M975 must not promote
- M975 must not use private holdout
- M975 must preserve the P0 actor-input contract
- M975 must design six-surface proof replay for the M974 selected candidate
- M975 must design fresh public/moderate-OOD and behavior/ablation gates before promotion audit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from first replay only
- do not skip M267/M264 full-surface replay
- do not skip old public proof surfaces
- do not use private holdout
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design
- type: gate
- checkpoint: docs/m975-v4-public-base-post-promotion-exact-repair-full-public-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: exact_repair_full_public_gate_design_admit_m976
- reason: M975 designs full public proof generalization behavior gate for the M974 exact-repaired candidate before promotion audit

## Next Blocker

m976-v4-public-base-post-promotion-exact-repair-full-public-gate-implementation
