# m284-rejected-trajectory-anchored-update Research Review

## Summary

- Generated at UTC: 20260522T190305Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_rejected_trajectory_raw_update_old_surface_washout
- Decision reason: M284 improves exact M270 objective and restores M267/M264 success drops to 17/17 but fails M183/M170 with normal success 3/17

## Hypothesis

A trajectory-level rejected-history anchor can preserve M267/M264 wrong-history success-drop evidence while the recovery anchor keeps M183/M170 row16 terminal-margin slack.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m283_current_family_rejected_trajectory_anchor/combined_recovery_rejected_anchor.npz
- parent_config: experiments/manifests/m283-current-family-rejected-trajectory-anchor-export.json, docs/m283-current-family-rejected-trajectory-anchor-export.md
- parent_objective: M270 objective plus current-family rejected-history trajectory anchor
- derived_from: m283-current-family-rejected-trajectory-anchor-export
- blocked_by: m283-current-family-rejected-trajectory-anchor-export
- supersedes: None
- invalidates: None

## Success Criteria

- start from m272b_a0_01025
- use M270 source-balanced objective and M283 combined recovery/rejected trajectory anchor
- run exactly one small actor-coupling update before any repeat or PPO
- improve fixed and exact M270 objective versus M272
- preserve M183/M170 row16 terminal margin above the registered required floor
- preserve M267/M264 success drops at 17/17 before broader gates
- actor input contract remains unchanged

## Failure Criteria

- row16 terminal margin crosses the registered floor
- M267/M264 success drops are below 17/17
- objective improves but any required proof surface regresses
- PPO is run
- actor observation inputs change

## Evidence Gates

- fixed sampled and exact M270 objective improvement
- M183/M170 row16 terminal-margin hard gate
- M267/M264 current-family wrong-history success-drop retention
- remaining replay surfaces if first two gates pass
- old protected-key diagnostic if replay passes
- behavior seeds 9505 and 9506 if replay passes
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M284
- do not change actor inputs
- do not use old checkpoint hidden states
- do not skip M183/M170 row16 or M267/M264
- do not promote based only on objective improvement

## Failure Taxonomy

- proof_washout
- objective_overfit

## Scoreboard

- milestone: m284-rejected-trajectory-anchored-update
- type: driver_candidate
- checkpoint: runs/m284_m272_actor_coupling_m270_rejected_trajectory_anchor_s10_lr5e5_seed10078/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_rejected_trajectory_raw_update_old_surface_washout
- reason: M284 improves exact M270 objective and restores M267/M264 success drops to 17/17 but fails M183/M170 with normal success 3/17

## Next Blocker

m285-m284-interpolation-balance-probe
