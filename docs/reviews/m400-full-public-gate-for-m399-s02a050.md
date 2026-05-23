# m400-full-public-gate-for-m399-s02a050 Research Review

## Summary

- Generated at UTC: 20260523T152553Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m399_s02a050_public_gate_base
- Decision reason: M400 promotes M399 alpha 0.05 after six public replay surfaces and behavior seeds pass; proof-safe bounded promotion with unchanged behavior success

## Hypothesis

The M399 alpha 0.05 proof-gate candidate can pass the full public promotion gate while preserving behavior seeds and all public replay surfaces.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m399_s02a050_exact_eval/summary.json, runs/m399_s02a050_old_key_replay_gate/summary.json, runs/m399_s02a050_m267_m264_first_replay/summary.json, runs/m399_s02a050_m183_m170_first_replay/summary.json, runs/m399_s02a050_source_diverse_protected_gate/summary.json
- parent_config: experiments/manifests/m399-old-key-normal-margin-recovery-repair-probe.json
- parent_objective: run full public gate for M399 alpha 0.05 proof-gate candidate
- derived_from: m399-old-key-normal-margin-recovery-repair-probe
- blocked_by: m399-old-key-normal-margin-recovery-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six public replay surfaces pass
- behavior seeds 9505 and 9506 do not regress versus the current public base
- old-key compact replay remains pass
- scoreboard records promotion decision and behavior metrics
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior success or termination regresses outside tolerance
- actor contract changes
- research validation fails

## Evidence Gates

- six public replay surfaces pass
- cumulative old-key compact gate remains passed
- behavior seeds 9505 and 9506 retain success and termination
- no actor input/output contract change
- promotion only if full public gate passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not lower replay thresholds
- do not add hidden or oracle actor inputs
- do not promote if behavior or replay proof regresses

## Failure Taxonomy

- none

## Scoreboard

- milestone: m400-full-public-gate-for-m399-s02a050
- type: driver_candidate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844040
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m399_s02a050_public_gate_base
- reason: M400 promotes M399 alpha 0.05 after six public replay surfaces and behavior seeds pass; proof-safe bounded promotion with unchanged behavior success

## Next Blocker

m401-m400-bounded-promotion-utility-audit
