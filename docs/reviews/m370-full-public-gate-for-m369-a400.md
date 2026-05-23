# m370-full-public-gate-for-m369-a400 Research Review

## Summary

- Generated at UTC: 20260523T121344Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m369_a400_hard_row_weighted_public_gate_base
- Decision reason: M370 promotes M369 alpha 0.4 after old-key source-diverse six replay and behavior gates pass; alpha 0.6 remains the first tested old-key gap-p10 failure

## Hypothesis

The M369 a400 hard-row weighted repaired candidate may pass the full public promotion gate after preserving exact, old-key, source-diverse, and first replay proof gates.

## Lineage

- parent_checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt, runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- parent_dataset: runs/m369_hard_row_interp_a400_old_key_replay_gate/summary.json, runs/m369_hard_row_a400_source_diverse_protected_gate/summary.json, runs/m369_hard_row_a400_m183_m170_first_replay/summary.json, runs/m369_hard_row_a400_m267_m264_first_replay/summary.json
- parent_config: experiments/manifests/m369-hard-row-weighted-repair-probe.json
- parent_objective: run full public gate for the hard-row weighted repaired alpha 0.4 candidate
- derived_from: m369-hard-row-weighted-repair-probe
- blocked_by: m369-hard-row-weighted-repair-probe
- supersedes: None
- invalidates: None

## Success Criteria

- all six replay surfaces pass
- behavior seeds 9505 and 9506 pass
- old-key and source-diverse proof results from M369 are cited
- candidate is promoted only if no proof or behavior regression is found
- research validation passes

## Failure Criteria

- any public replay surface fails
- behavior seeds regress
- actor input contract changes
- research validation fails

## Evidence Gates

- old-key replay for M369 a400 retained
- source-diverse protected pass from M369 retained
- M183/M170 and M267/M264 first replay pass from M369 retained
- all six public replay surfaces pass
- behavior seeds 9505 and 9506 pass
- no actor input contract change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote without all six replay surfaces
- do not ignore behavior regressions
- do not hide that a600 already fails old-key gap p10
- do not run PPO
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m370-full-public-gate-for-m369-a400
- type: driver_candidate
- checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844239
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m369_a400_hard_row_weighted_public_gate_base
- reason: M370 promotes M369 alpha 0.4 after old-key source-diverse six replay and behavior gates pass; alpha 0.6 remains the first tested old-key gap-p10 failure

## Next Blocker

m371-alpha06-old-key-gap-p10-audit
