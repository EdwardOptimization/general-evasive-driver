# m348-exact-source-diverse-probe-for-m335-a010 Research Review

## Summary

- Generated at UTC: 20260523T101510Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m349_full_public_gate_for_m335_a010
- Decision reason: M348 alpha 0.01 passes exact M297/M270 versus current base source-diverse protected gate old-key neighborhood gate and first replay gates; no promotion

## Hypothesis

M335 alpha 0.01 may pass the exact and source-diverse proof gates after passing the replayable old-key neighborhood gate, making it eligible for a later full public gate.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- parent_dataset: runs/m347_old_key_alpha_sweep/summary.json, runs/m347_old_key_alpha_sweep/alpha_sweep_summary.csv
- parent_config: experiments/manifests/m347-old-key-neighborhood-alpha-sweep-run.json, docs/m347-old-key-neighborhood-alpha-sweep-run.md
- parent_objective: probe exact and source-diverse proof gates for the largest old-key-passing alpha
- derived_from: m347-old-key-neighborhood-alpha-sweep-run
- blocked_by: m347-old-key-neighborhood-alpha-sweep-run
- supersedes: None
- invalidates: None

## Success Criteria

- exact M297 and M270 do not regress versus m335_a0_0075
- source-diverse protected gates pass
- first replay gates pass
- old-key replay gate result is cited from M347
- research validation passes

## Failure Criteria

- exact M297 or M270 regresses
- source-diverse protected gate fails
- first replay gate fails
- gate result depends on changing actor inputs
- checkpoint is promoted directly

## Evidence Gates

- exact M297 rejected-history preference no-regression versus M336 base
- exact M270 source-balanced outcome no-regression versus M336 base
- source-diverse protected gate pass
- old-key neighborhood replay gate pass from M347 retained
- first replay gates pass before any full public gate
- do not run PPO or promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from M347 alpha sweep alone
- do not skip exact objectives
- do not skip source-diverse protected gates
- do not hide 9944 diagnostic
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m348-exact-source-diverse-probe-for-m335-a010
- type: gate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m349_full_public_gate_for_m335_a010
- reason: M348 alpha 0.01 passes exact M297/M270 versus current base source-diverse protected gate old-key neighborhood gate and first replay gates; no promotion

## Next Blocker

m349-full-public-gate-for-m335-a010
