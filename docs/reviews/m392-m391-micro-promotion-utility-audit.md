# m392-m391-micro-promotion-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T143023Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m393_current_family_rejected_boundary_target_export
- Decision reason: M392 classifies M391 as proof-safe micro retention not meaningful driver improvement; row15 remains active boundary and needs rejected-branch local collision-side targets

## Hypothesis

M391 is likely another proof-safe micro promotion rather than meaningful driver improvement, so the next blocker should be decided by active-boundary utility rather than immediately chaining PPO.

## Lineage

- parent_checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt, runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- parent_dataset: docs/m391-full-public-gate-for-m390-a005.md, runs/m390_step17_a005_exact_eval/summary.json, runs/m391_full_public_gate_for_m390_a005/summary.json
- parent_config: experiments/manifests/m391-full-public-gate-for-m390-a005.json
- parent_objective: audit whether the M391 public-gate promotion is useful enough to chain another repair or PPO step
- derived_from: m391-full-public-gate-for-m390-a005
- blocked_by: m391-full-public-gate-for-m390-a005
- supersedes: None
- invalidates: None

## Success Criteria

- quantify exact objective deltas and behavior deltas versus the previous public base
- record the first known failing alpha or boundary after M391
- classify whether M391 is meaningful progress or only proof-safe retention
- pre-register the next highest-leverage milestone

## Failure Criteria

- audit cannot identify a next blocker
- audit relies on unregistered private holdout tuning
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- compare M391 movement size against M386 base
- identify active first failing boundary
- decide whether next step should be full-gate promotion continuation, objective redesign, or PPO block

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

- milestone: m392-m391-micro-promotion-utility-audit
- type: gate
- checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m393_current_family_rejected_boundary_target_export
- reason: M392 classifies M391 as proof-safe micro retention not meaningful driver improvement; row15 remains active boundary and needs rejected-branch local collision-side targets

## Next Blocker

m393-current-family-rejected-boundary-target-export
