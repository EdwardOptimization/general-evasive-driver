# m359-m354-best-step-micro-alpha-proof-gate Research Review

## Summary

- Generated at UTC: 20260523T111325Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m360_full_public_gate_for_m354_micro_alpha
- Decision reason: M359 alpha 0.00025 passes source-diverse 5/5 and both first replay gates 17/17 after exact and old-key proof passed in M358

## Hypothesis

The M358 selected alpha 0.00025 may preserve source-diverse and first replay proof gates after passing exact objectives and old-key neighborhood replay.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- parent_dataset: runs/m358_m354_best_step_bounded_interpolation_probe/summary.json, runs/m358_m354_best_step_old_key_micro_a00025_gate/summary.json, runs/m358_m354_best_step_alpha00025_exact_eval/summary.json
- parent_config: experiments/manifests/m358-m354-best-step-bounded-interpolation-probe.json, docs/m358-m354-best-step-bounded-interpolation-probe.md
- parent_objective: run source-diverse and first replay gates for the bounded M354 best-step micro alpha
- derived_from: m358-m354-best-step-bounded-interpolation-probe
- blocked_by: m358-m354-best-step-bounded-interpolation-probe
- supersedes: None
- invalidates: None

## Success Criteria

- source-diverse protected gates pass
- M183/M170 and M267/M264 first replay gates pass
- exact and old-key results from M358 are cited
- research validation passes

## Failure Criteria

- source-diverse protected gate fails
- first replay gate fails
- actor input contract changes
- checkpoint is promoted directly

## Evidence Gates

- no PPO run
- selected alpha exact M297/M270 no-regression retained
- selected alpha old-key neighborhood pass retained
- source-diverse protected gate pass
- M183/M170 and M267/M264 first replay gates pass
- do not promote directly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from proof gate alone
- do not skip source-diverse protected gates
- do not skip first replay gates
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m359-m354-best-step-micro-alpha-proof-gate
- type: gate
- checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m360_full_public_gate_for_m354_micro_alpha
- reason: M359 alpha 0.00025 passes source-diverse 5/5 and both first replay gates 17/17 after exact and old-key proof passed in M358

## Next Blocker

m360-full-public-gate-for-m358-a00025
