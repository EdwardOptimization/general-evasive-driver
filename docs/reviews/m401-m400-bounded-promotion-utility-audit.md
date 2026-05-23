# m401-m400-bounded-promotion-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T152809Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m402_old_key_normal_recovery_alignment_audit
- Decision reason: M401 classifies M400 as proof-safe bounded promotion not driver improvement; first boundary remains old-key 9958 normal branch at alpha 0.10

## Hypothesis

M400 is likely another proof-safe bounded promotion with no meaningful behavior improvement, so the next task should be chosen by auditing utility and the first active boundary.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m400_full_public_gate_for_m399_s02a050/summary.json, runs/m400_full_public_gate_for_m399_s02a050/full_gates/summary.json, runs/m400_full_public_gate_for_m399_s02a050/behavior_summary.csv
- parent_config: experiments/manifests/m400-full-public-gate-for-m399-s02a050.json
- parent_objective: audit whether the M400 promotion is useful enough to chain repair or PPO
- derived_from: m400-full-public-gate-for-m399-s02a050
- blocked_by: m400-full-public-gate-for-m399-s02a050
- supersedes: None
- invalidates: None

## Success Criteria

- compare M400 behavior and exact/proof movement against the previous public base
- identify the first known failing alpha or active protected boundary when available
- classify whether M400 is useful enough to chain another repair or PPO step
- record the next blocker in docs and manifests

## Failure Criteria

- audit cannot locate M400 artifacts
- audit changes actor inputs or thresholds
- research validation fails

## Evidence Gates

- no PPO run
- audit proof-safe promotion utility
- identify the first known post-M400 boundary
- decide whether next task is repair, surface refresh, PPO smoke, or stop this direction

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

- milestone: m401-m400-bounded-promotion-utility-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m402_old_key_normal_recovery_alignment_audit
- reason: M401 classifies M400 as proof-safe bounded promotion not driver improvement; first boundary remains old-key 9958 normal branch at alpha 0.10

## Next Blocker

m402-old-key-normal-recovery-alignment-audit
