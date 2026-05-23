# m396-m395-micro-promotion-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T150252Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m397_m395_alpha02_old_key_boundary_audit
- Decision reason: M396 classifies M395 as proof-safe bounded promotion not meaningful driver improvement; alpha 0.2 first fails old-key case 9958 by normal-branch terminal-margin cliff

## Hypothesis

M395 is likely another proof-safe bounded promotion rather than meaningful driver improvement, so the next blocker should be decided by active-boundary utility rather than immediately chaining PPO.

## Lineage

- parent_checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt, runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- parent_dataset: docs/m395-full-public-gate-for-m394-s02a010.md, runs/m395_full_public_gate_for_m394_s02a010/summary.json, runs/m394_s02a010_exact_eval/summary.json
- parent_config: experiments/manifests/m395-full-public-gate-for-m394-s02a010.json
- parent_objective: audit whether the M395 public-gate promotion is meaningful enough to chain another repair or PPO step
- derived_from: m395-full-public-gate-for-m394-s02a010
- blocked_by: m395-full-public-gate-for-m394-s02a010
- supersedes: None
- invalidates: None

## Success Criteria

- quantify exact objective deltas and behavior deltas versus the previous public base
- record the first known failing alpha or boundary after M395
- classify whether M395 is meaningful progress or only proof-safe retention
- pre-register the next highest-leverage milestone

## Failure Criteria

- audit cannot identify a next blocker
- audit relies on unregistered private holdout tuning
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- compare M395 movement size against M391 base
- identify first known failing boundary after M395
- decide whether next step should be utility audit, objective redesign, full gate, or PPO block

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in the utility audit
- do not treat a micro promotion as behavior improvement without evidence
- do not lower proof thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m396-m395-micro-promotion-utility-audit
- type: gate
- checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m397_m395_alpha02_old_key_boundary_audit
- reason: M396 classifies M395 as proof-safe bounded promotion not meaningful driver improvement; alpha 0.2 first fails old-key case 9958 by normal-branch terminal-margin cliff

## Next Blocker

m397-m395-alpha02-old-key-boundary-audit
