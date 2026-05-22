# m285-m284-interpolation-balance-probe Research Review

## Summary

- Generated at UTC: 20260522T191510Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: archive_m285_a0_0002_boundary_diagnostic
- Decision reason: M285 alpha 0.0002 passes six replay surfaces protected key and behavior but exact M270 improves only 9.5e-7 while alpha 0.0005 fails row16

## Hypothesis

A smaller interpolation toward M284 may retain M267/M264 wrong-history success drops without crossing the M183/M170 normal-success cliff.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt, runs/m284_m272_actor_coupling_m270_rejected_trajectory_anchor_s10_lr5e5_seed10078/optimized_checkpoint.pt
- parent_dataset: runs/m284_m183_m170_replay_gate_seed9510/boundary_replay_rows.csv, runs/m284_m267_m264_replay_gate_seed10070/boundary_replay_rows.csv
- parent_config: experiments/manifests/m284-rejected-trajectory-anchored-update.json, docs/m284-rejected-trajectory-anchored-update.md
- parent_objective: no-training interpolation from M272 toward M284 to balance old-surface and current-family proof gates
- derived_from: m284-rejected-trajectory-anchored-update
- blocked_by: m284-rejected-trajectory-anchored-update
- supersedes: None
- invalidates: None

## Success Criteria

- write interpolation checkpoints from M272 to M284
- find the largest alpha that passes both M183/M170 and M267/M264 or document that none exists
- measure exact M270 loss for the best passing alpha
- no PPO or actor update is run

## Failure Criteria

- all nonzero alphas fail M183/M170 or M267/M264
- a checkpoint is promoted without both first proof gates
- PPO or actor update is run
- actor observation inputs change

## Evidence Gates

- interpolate from M272 toward rejected M284 without training
- evaluate exact M270 objective
- gate M183/M170 and M267/M264 first
- run broader replay only if both first gates pass
- run protected-key diagnostic and behavior seeds only after replay gates pass
- do not run PPO or actor update

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M285
- do not run a new actor update in M285
- do not skip M183/M170 or M267/M264
- do not promote an alpha that fails either first proof gate
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m285-m284-interpolation-balance-probe
- type: driver_candidate
- checkpoint: runs/m285_m272_to_m284_interpolation_balance/checkpoints/alpha_0_0002.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844096
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: archive_m285_a0_0002_boundary_diagnostic
- reason: M285 alpha 0.0002 passes six replay surfaces protected key and behavior but exact M270 improves only 9.5e-7 while alpha 0.0005 fails row16

## Next Blocker

m286-rejected-trajectory-anchor-balance-sweep
