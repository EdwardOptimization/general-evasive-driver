# m360-full-public-gate-for-m358-a00025 Research Review

## Summary

- Generated at UTC: 20260523T111840Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m358_a00025_old_key_neighborhood_public_gate_base
- Decision reason: M360 promotes alpha 0.00025 after exact old-key source-diverse six replay and behavior gates pass; this is a proof-safe micro-step with first failing alpha 0.0005

## Hypothesis

The M358 alpha 0.00025 candidate may pass the full public gate after preserving exact, old-key, source-diverse, and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- parent_dataset: runs/m358_m354_best_step_bounded_interpolation_probe/summary.json, runs/m359_m354_best_step_micro_alpha_proof_gate/summary.json
- parent_config: experiments/manifests/m359-m354-best-step-micro-alpha-proof-gate.json, docs/m359-m354-best-step-micro-alpha-proof-gate.md
- parent_objective: run full public gate for alpha 0.00025 after proof-gate pass
- derived_from: m359-m354-best-step-micro-alpha-proof-gate
- blocked_by: m359-m354-best-step-micro-alpha-proof-gate
- supersedes: None
- invalidates: None

## Success Criteria

- all six replay surfaces pass
- behavior seeds 9505 and 9506 do not regress versus M352 public base
- accepted alpha limitation is documented
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior seeds regress
- actor input contract changes
- accepted micro-alpha limitation is omitted

## Evidence Gates

- exact M297/M270 no-regression from M358 retained
- old-key neighborhood pass from M358 retained
- source-diverse protected pass from M359 retained
- all six public replay surfaces pass
- behavior seeds 9505 and 9506 do not regress
- promote only if full gate passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from partial proof gates
- do not skip behavior seeds
- do not change actor inputs
- do not hide that accepted alpha is only 0.00025

## Failure Taxonomy

- none

## Scoreboard

- milestone: m360-full-public-gate-for-m358-a00025
- type: driver_candidate
- checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844538
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m358_a00025_old_key_neighborhood_public_gate_base
- reason: M360 promotes alpha 0.00025 after exact old-key source-diverse six replay and behavior gates pass; this is a proof-safe micro-step with first failing alpha 0.0005

## Next Blocker

m361-micro-alpha-utility-audit
