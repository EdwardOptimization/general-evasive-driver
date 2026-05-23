# m331-m330-old-key-gap-floor-failure-audit Research Review

## Summary

- Generated at UTC: 20260523T065509Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m332_m330_old_key_gap_bounded_interpolation_probe
- Decision reason: M331 classifies M330 as old-key local gap erosion not source-diverse washout; keep 0.09 floor and probe gap-bounded interpolation from M328 to M330

## Hypothesis

M330 passes exact and source-diverse gates but fails the old-key margin-gap floor, so the next task should audit whether the old-key floor is detecting real proof erosion or over-constraining a source-diverse-retained candidate.

## Lineage

- parent_checkpoint: runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt, runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
- parent_dataset: runs/m330_source_diverse_protected_gate/summary.json, runs/m330_critical_key_seed9944/guard_results.csv, runs/m328_full_public_gate_for_m327_repaired/full_gates/critical_key_seed9944/guard_results.csv
- parent_config: experiments/manifests/m330-source-diverse-ppo-fresh-seed-repeat.json, docs/m330-source-diverse-ppo-fresh-seed-repeat.md
- parent_objective: audit whether M330 old-key margin-gap floor failure is true proof erosion, stale threshold, or candidate-specific trajectory artifact
- derived_from: m330-source-diverse-ppo-fresh-seed-repeat
- blocked_by: m330-source-diverse-ppo-fresh-seed-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- audit compares M328 and M330 old-key normal/wrong/gap values
- audit compares old-key result with source-diverse gate result
- audit classifies the failure cause
- audit decides whether to repair, reject, or redesign the old-key diagnostic floor
- no PPO is run

## Failure Criteria

- audit ignores old-key gap floor
- audit promotes M330
- audit changes actor inputs
- audit runs PPO

## Evidence Gates

- do not run PPO
- do not promote M330
- compare M328 and M330 old-key margins and wrong-history branch behavior
- compare old-key diagnostic against source-diverse protected pass
- classify whether the 0.09 floor remains valid
- define next safe milestone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower the old-key floor without audit
- do not promote M330 from exact/source-diverse pass alone
- do not run first replay retroactively before deciding whether the old-key stop was valid
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m331-m330-old-key-gap-floor-failure-audit
- type: gate
- checkpoint: runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m332_m330_old_key_gap_bounded_interpolation_probe
- reason: M331 classifies M330 as old-key local gap erosion not source-diverse washout; keep 0.09 floor and probe gap-bounded interpolation from M328 to M330

## Next Blocker

m332-m330-old-key-gap-bounded-interpolation-probe
