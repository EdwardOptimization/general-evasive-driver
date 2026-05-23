# m337-old-key-gap-floor-bottleneck-audit Research Review

## Summary

- Generated at UTC: 20260523T072740Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_old_key_gap_distribution_refresh_design
- Decision reason: M337 classifies current blocker as singleton old-key gap-floor bottleneck not source-diverse washout; source-diverse endpoint passes while old-key endpoint gap collapses to 0.065360

## Hypothesis

The fixed old-key 9944 margin-gap floor has become the active bottleneck for PPO continuation: source-diverse proof remains intact, but repaired PPO endpoints erode the singleton gap and force micro-alpha promotions.

## Lineage

- parent_checkpoint: runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt, runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m335_old_key_gap_sweep/guard_results.csv, runs/m336_full_public_gate_for_m335_a0075/full_gates/critical_key_seed9944/guard_results.csv, runs/m335_a0075_source_diverse_protected_gate/summary.json, runs/m336_full_public_gate_for_m335_a0075/source_diverse_protected_gate/summary.json, runs/m335_m333_to_repaired_exact_line_search/line_search_summary.csv
- parent_config: experiments/manifests/m336-full-public-gate-for-m335-a0075.json, docs/m336-full-public-gate-for-m335-a0075.md
- parent_objective: audit whether the fixed old-key 9944 gap floor has become the bottleneck before any further PPO escalation
- derived_from: m336-full-public-gate-for-m335-a0075
- blocked_by: m336-full-public-gate-for-m335-a0075
- supersedes: None
- invalidates: None

## Success Criteria

- audit quantifies old-key gap trends for recent bases and repaired endpoints
- audit compares those trends against source-diverse protected gates
- audit classifies the bottleneck using the failure taxonomy
- audit recommends the next no-PPO design step before further PPO escalation

## Failure Criteria

- audit cannot reproduce old-key gap values
- audit cannot distinguish singleton old-key saturation from source-diverse washout
- audit recommends PPO continuation without a gate or objective change

## Evidence Gates

- do not run PPO
- compare old-key gap trends across M328/M333/M335 endpoint/M335 alpha
- compare source-diverse protected gate trends against old-key floor trends
- classify whether the blocker is single-key floor saturation, broad source-diverse washout, or objective-design gap erosion
- decide whether to keep fixed 0.09 floor, refresh a source-diverse gap-floor distribution, or design an old-key gap-retention objective

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower the 0.09 floor without an audit
- do not run more PPO before the audit
- do not promote from an audit milestone
- do not change actor inputs

## Failure Taxonomy

- protected_key_window_failure

## Scoreboard

- milestone: m337-old-key-gap-floor-bottleneck-audit
- type: gate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_old_key_gap_distribution_refresh_design
- reason: M337 classifies current blocker as singleton old-key gap-floor bottleneck not source-diverse washout; source-diverse endpoint passes while old-key endpoint gap collapses to 0.065360

## Next Blocker

m338-old-key-gap-distribution-refresh-design
