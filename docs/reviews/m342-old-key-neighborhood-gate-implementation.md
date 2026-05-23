# m342-old-key-neighborhood-gate-implementation Research Review

## Summary

- Generated at UTC: 20260523T093254Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m343_old_key_neighborhood_gate_probe
- Decision reason: M342 implements the old-key neighborhood gate and reproduces M341 selected-alpha pass plus repaired-endpoint repair-needed classification with 9944 diagnostic visible

## Hypothesis

A reusable old-key neighborhood gate can replace singleton-veto dominance in the acceptance stack by checking the M341 compact corpus while preserving 9944 as a diagnostic row.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m341_old_key_neighborhood_mining/summary.json, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
- parent_config: experiments/manifests/m341-old-key-neighborhood-mining-run.json, docs/m341-old-key-neighborhood-mining-run.md
- parent_objective: implement a reusable gate for the M341 old-key neighborhood compact corpus
- derived_from: m341-old-key-neighborhood-mining-run
- blocked_by: m341-old-key-neighborhood-mining-run
- supersedes: None
- invalidates: None

## Success Criteria

- gate reproduces M341 compact corpus pass for selected alpha
- gate classifies M335 repaired endpoint repair-needed
- gate reports broad and compact diversity metrics
- gate keeps M133/9944 diagnostics visible
- focused tests cover threshold pass and failure cases
- research validation passes

## Failure Criteria

- gate ignores compact diversity thresholds
- gate hides 9944 diagnostics
- gate changes actor input contract
- gate allows PPO or promotion directly

## Evidence Gates

- do not run PPO
- implement old-key neighborhood gate wrapper or evaluator
- reproduce M341 selected-alpha pass and endpoint repair-needed classification
- keep 9944 diagnostic visible
- add focused tests for summary thresholds and CSV schema

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower 9944 floor ad hoc
- do not promote a checkpoint
- do not change actor inputs
- do not use M341 as private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m342-old-key-neighborhood-gate-implementation
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m343_old_key_neighborhood_gate_probe
- reason: M342 implements the old-key neighborhood gate and reproduces M341 selected-alpha pass plus repaired-endpoint repair-needed classification with 9944 diagnostic visible

## Next Blocker

m343-old-key-neighborhood-gate-probe
