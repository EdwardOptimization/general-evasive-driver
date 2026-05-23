# m402-old-key-normal-recovery-alignment-audit Research Review

## Summary

- Generated at UTC: 20260523T153158Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m403_old_key_normal_recovery_weight_sweep
- Decision reason: M402 finds M398 target is valid but M399 repair action barely moves toward it and slightly opposite; classify recovery residual underweighted against closed-loop boundary

## Hypothesis

The M398 one-step normal-margin recovery residual may not fully align with the closed-loop old-key 9958 terminal-margin boundary, so the next repair should be chosen only after auditing action and replay alignment.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_targets.csv, runs/m399_s02a050_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m399_s02a100_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m399_s02a050_exact_eval/summary.json
- parent_config: experiments/manifests/m401-m400-bounded-promotion-utility-audit.json
- parent_objective: audit alignment between M398 normal-margin recovery residual and closed-loop old-key replay
- derived_from: m401-m400-bounded-promotion-utility-audit
- blocked_by: m401-m400-bounded-promotion-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- quantify target action versus policy action differences for the 9958 boundary
- quantify old-key replay margin movement from alpha 0.05 to alpha 0.10
- classify whether the recovery target is too weak, the residual weight is wrong, or the one-step residual misses trajectory drift
- pre-register the next no-PPO repair or infrastructure milestone

## Failure Criteria

- audit cannot locate M398/M399/M400 artifacts
- audit changes actor inputs or thresholds
- research validation fails

## Evidence Gates

- no PPO run
- compare M398 target actions against M400/M399 alpha actions on case 9958
- compare exact recovery loss movement against old-key replay terminal margins
- classify whether next task should be target refresh, residual reweighting, trajectory residual, or repair stop

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m402-old-key-normal-recovery-alignment-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m403_old_key_normal_recovery_weight_sweep
- reason: M402 finds M398 target is valid but M399 repair action barely moves toward it and slightly opposite; classify recovery residual underweighted against closed-loop boundary

## Next Blocker

m403-old-key-normal-recovery-weight-sweep
