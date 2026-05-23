# m341-old-key-neighborhood-mining-run Research Review

## Summary

- Generated at UTC: 20260523T092430Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_m342_old_key_neighborhood_gate_implementation
- Decision reason: M341 mines 179 broad rows and a 40-row compact corpus across 5 seed blocks; selected alpha has 0 accepted regressions while repaired endpoint has 15, so replacement gate is ready

## Hypothesis

Wider current-base old-key-neighborhood mining can produce a source-diverse compact old-gap corpus that distinguishes M335 repaired endpoint from M335 alpha without relying on singleton 9944 dominance.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m339_old_key_gap_distribution_refresh/summary.json, runs/m339_m133_all_old_key_guard/guard_results.csv
- parent_config: experiments/manifests/m340-old-key-neighborhood-mining-design.json, docs/m340-old-key-neighborhood-mining-design.md
- parent_objective: execute wider old-key neighborhood mining and aggregation without PPO
- derived_from: m340-old-key-neighborhood-mining-design
- blocked_by: m340-old-key-neighborhood-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- broad pool has at least 80 rows
- broad pool covers at least 4 seed blocks
- compact corpus has 20-40 rows
- compact corpus covers at least 4 seed blocks and 15 physical pairs or keys
- max compact seed-block dominance <= 25%
- max compact physical-pair dominance <= 15%
- M335 repaired endpoint is classified repair-needed by pre-registered thresholds
- M335 alpha 0.0075 passes selected-alpha thresholds
- 9944 and M133 all-key rows remain diagnostics

## Failure Criteria

- mined rows remain too source dominated
- M335 endpoint cannot be distinguished from selected alpha
- selected alpha fails the proposed replacement gate
- the run requires PPO or actor changes

## Evidence Gates

- do not run PPO
- mine current-base old-key neighborhood seed blocks
- evaluate m333_base m335_a0075 and m335_repaired on mined cases
- export broad pool compact corpus and summary
- report whether diversity targets pass before any gate replacement

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower 9944 floor
- do not use M339 compact draft as replacement gate
- do not promote any checkpoint
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m341-old-key-neighborhood-mining-run
- type: gate
- checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m342_old_key_neighborhood_gate_implementation
- reason: M341 mines 179 broad rows and a 40-row compact corpus across 5 seed blocks; selected alpha has 0 accepted regressions while repaired endpoint has 15, so replacement gate is ready

## Next Blocker

m342-old-key-neighborhood-gate-implementation
