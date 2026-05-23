# m340-old-key-neighborhood-mining-design Research Review

## Summary

- Generated at UTC: 20260523T074929Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m341_old_key_neighborhood_mining_run
- Decision reason: M340 designs five seed-block old-key neighborhood mining with explicit broad and compact diversity targets; no PPO and 9944 floor remains active

## Hypothesis

A wider old-key-neighborhood mining plan can produce source-diverse old gap-retention rows around M133 and 9944-like cases, avoiding both singleton veto dominance and M133-only overfitting before further PPO.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m339_old_key_gap_distribution_refresh/summary.json, runs/m339_old_key_gap_distribution_refresh/old_key_gap_candidate_pool.csv, runs/m339_old_key_gap_distribution_refresh/old_key_gap_compact_corpus.csv, runs/m339_m133_all_old_key_guard/guard_results.csv
- parent_config: experiments/manifests/m339-old-key-gap-distribution-corpus-refresh.json, docs/m339-old-key-gap-distribution-corpus-refresh.md
- parent_objective: design a wider old-key neighborhood mining stage because existing corpora produce a severity draft dominated by M133 historical keys and duplicated M183 rows
- derived_from: m339-old-key-gap-distribution-corpus-refresh
- blocked_by: m339-old-key-gap-distribution-corpus-refresh
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies seed ranges, source steps, target distances, lateral offsets, and widths to mine
- design specifies how M333, M335 alpha, and M335 endpoint will be compared
- design requires at least 80 broad rows and 20-40 compact rows before replacement-gate implementation
- design enforces max source-family dominance <= 25%
- design keeps singleton 9944 active until a replacement corpus passes diversity targets
- design admits a separate implementation or mining-run milestone only

## Failure Criteria

- design lowers the 9944 floor ad hoc
- design treats the M339 compact draft as sufficient despite source dominance
- design allows PPO before mining
- design changes actor input contract

## Evidence Gates

- do not run PPO
- do not lower the 9944 floor
- design a wider old-key neighborhood miner before any gate replacement
- pre-register source-diversity and dominance targets for the mined corpus
- keep 9944 and all M133 all-key rows as diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use M339 insufficient compact draft as a promotion gate
- do not remove 9944 diagnostics
- do not run PPO before the replacement corpus exists
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m340-old-key-neighborhood-mining-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m341_old_key_neighborhood_mining_run
- reason: M340 designs five seed-block old-key neighborhood mining with explicit broad and compact diversity targets; no PPO and 9944 floor remains active

## Next Blocker

m341-old-key-neighborhood-mining-run
