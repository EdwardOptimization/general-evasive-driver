# m358-m354-best-step-bounded-interpolation-probe Research Review

## Summary

- Generated at UTC: 20260523T110952Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m359_m354_best_step_micro_alpha_probe
- Decision reason: M358 bounds the M356 direction to alpha 0.00025; it passes exact M297/M270 and old-key neighborhood while alpha 0.0005 is the first accepted-case failure

## Hypothesis

The M356 best-step repair is a useful but too-large direction; a small interpolation from the M352 base may preserve old-key neighborhood proof and become eligible for exact/source-diverse/first replay probing.

## Lineage

- parent_checkpoint: runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt, runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
- parent_dataset: runs/m357_m354_best_step_source_diverse_protected_gate/summary.json, runs/m357_m354_best_step_old_key_replay_gate/summary.json, runs/m357_m354_best_step_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m357-m354-best-step-repair-proof-gate.json, docs/m357-m354-best-step-repair-proof-gate.md
- parent_objective: bound the M356 best-step repair direction after direct proof-gate washout
- derived_from: m357-m354-best-step-repair-proof-gate
- blocked_by: m357-m354-best-step-repair-proof-gate
- supersedes: None
- invalidates: None

## Success Criteria

- interpolation checkpoints are generated from M352 base to M356 best-step candidate
- old-key neighborhood replay gate evaluates each registered alpha
- largest passing alpha and first failing alpha are reported
- research validation passes

## Failure Criteria

- no alpha including zero reproduces the old-key baseline
- old-key replay cannot cover all 40 compact rows
- actor input contract changes
- PPO or promotion is attempted

## Evidence Gates

- no PPO run
- interpolate only from M352 base to M356 best-step candidate
- run old-key neighborhood targeted replay for interpolation alphas
- select the largest old-key-neighborhood-passing nonzero alpha if one exists
- do not promote directly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote from interpolation alone
- do not relax old-key neighborhood thresholds
- do not change actor inputs
- do not run longer PPO before bounded proof probe

## Failure Taxonomy

- none

## Scoreboard

- milestone: m358-m354-best-step-bounded-interpolation-probe
- type: gate
- checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m359_m354_best_step_micro_alpha_probe
- reason: M358 bounds the M356 direction to alpha 0.00025; it passes exact M297/M270 and old-key neighborhood while alpha 0.0005 is the first accepted-case failure

## Next Blocker

m359-m354-best-step-micro-alpha-proof-gate
