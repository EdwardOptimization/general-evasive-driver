# m365-full-public-gate-for-m364-alpha01 Research Review

## Summary

- Generated at UTC: 20260523T114708Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m364_alpha01_old_key_aware_public_gate_base
- Decision reason: M365 promotes alpha 0.1 after old-key source-diverse six replay and behavior gates pass; alpha 0.2 remains first failing tested old-key interpolation

## Hypothesis

The M364 alpha 0.1 candidate may pass the full public promotion gate after preserving exact, old-key, source-diverse, and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt, runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m364_old_key_aware_repair_probe/summary.json, runs/m364_alpha01_source_diverse_protected_gate/summary.json
- parent_config: experiments/manifests/m364-old-key-aware-repair-probe.json
- parent_objective: run full public gate for M364 alpha 0.1 after proof-gate pass
- derived_from: m364-old-key-aware-repair-probe
- blocked_by: m364-old-key-aware-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six replay surfaces pass
- behavior seeds 9505 and 9506 do not regress versus current public base
- accepted-alpha limitation is documented
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior seeds regress
- actor input contract changes
- accepted-alpha limitation is omitted

## Evidence Gates

- exact and old-key surrogate from M364 retained
- old-key neighborhood pass from M364 retained
- source-diverse protected pass from M364 retained
- all six public replay surfaces pass
- behavior seeds 9505 and 9506 do not regress
- promote only if full gate passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from partial proof gates
- do not skip behavior seeds
- do not hide that alpha 0.2 already fails old-key replay
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m365-full-public-gate-for-m364-alpha01
- type: driver_candidate
- checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844538
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m364_alpha01_old_key_aware_public_gate_base
- reason: M365 promotes alpha 0.1 after old-key source-diverse six replay and behavior gates pass; alpha 0.2 remains first failing tested old-key interpolation

## Next Blocker

m366-alpha02-old-key-regression-audit
