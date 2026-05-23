# m338-old-key-gap-distribution-refresh-design Research Review

## Summary

- Generated at UTC: 20260523T073059Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_old_key_gap_distribution_corpus_refresh
- Decision reason: M338 designs source-diverse old-key gap distribution gate; keep 9944 diagnostic but replace singleton veto dominance before more PPO

## Hypothesis

Replacing the singleton old-key gap floor with a source-diverse old-key/gap distribution gate can retain old wrong-history evidence without forcing every PPO continuation through a single saturated scalar row.

## Lineage

- parent_checkpoint: runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt, runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
- parent_dataset: runs/m337_old_key_gap_floor_bottleneck_audit/summary.json, runs/m337_old_key_gap_floor_bottleneck_audit/old_key_gap_trend.csv, runs/m337_old_key_gap_floor_bottleneck_audit/source_diverse_trend.csv, runs/m337_m335_repaired_endpoint_source_diverse_gate/summary.json
- parent_config: experiments/manifests/m337-old-key-gap-floor-bottleneck-audit.json, docs/m337-old-key-gap-floor-bottleneck-audit.md
- parent_objective: design a source-diverse old-key gap distribution refresh to replace singleton 9944 gap-floor bottleneck before more PPO
- derived_from: m337-old-key-gap-floor-bottleneck-audit
- blocked_by: m337-old-key-gap-floor-bottleneck-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies how to mine or refresh old-key/gap rows
- design specifies source diversity and dominance limits
- design specifies distributional pass/fail metrics
- design keeps 9944 as diagnostic while preventing singleton veto dominance
- design admits a separate implementation or corpus-refresh milestone

## Failure Criteria

- design simply lowers the 0.09 floor
- design removes old-key diagnostics
- design does not define source diversity
- design allows PPO before the gate exists

## Evidence Gates

- do not run PPO in M338
- design a source-diverse old-key/gap distribution refresh
- preserve fixed 9944 as diagnostic but avoid singleton veto dominance
- pre-register candidate acceptance metrics before any new PPO
- admit a separate corpus-refresh or implementation milestone only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower the old-key floor ad hoc
- do not remove 9944 from diagnostics
- do not run PPO before the new gate is designed
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m338-old-key-gap-distribution-refresh-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_old_key_gap_distribution_corpus_refresh
- reason: M338 designs source-diverse old-key gap distribution gate; keep 9944 diagnostic but replace singleton veto dominance before more PPO

## Next Blocker

m339-old-key-gap-distribution-corpus-refresh
