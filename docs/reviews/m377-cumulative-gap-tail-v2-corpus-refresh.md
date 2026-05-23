# m377-cumulative-gap-tail-v2-corpus-refresh Research Review

## Summary

- Generated at UTC: 20260523T124734Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m378_cumulative_gap_tail_v2_repair_probe
- Decision reason: M377 exports a v2 old-key corpus with one hard row and four current gap-tail rows and verifies no-update exact repair integration

## Hypothesis

Refreshing the old-key overlay/corpus with M376 alpha 0.2 gap-tail rows can make the current cumulative boundary visible to exact repair without changing actor inputs.

## Lineage

- parent_checkpoint: runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt, runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_2.pt
- parent_dataset: runs/m376_alpha02_cumulative_old_key_boundary_audit/gap_tail_rows.csv, runs/m376_alpha02_cumulative_old_key_boundary_audit/worst_gap_rows.csv, docs/m376-m374-alpha02-cumulative-old-key-boundary-audit.md
- parent_config: experiments/manifests/m376-m374-alpha02-cumulative-old-key-boundary-audit.json
- parent_objective: refresh the old-key feedback overlay/corpus for the current M375 cumulative gap-tail boundary
- derived_from: m376-m374-alpha02-cumulative-old-key-boundary-audit
- blocked_by: m376-m374-alpha02-cumulative-old-key-boundary-audit
- supersedes: None
- invalidates: None

## Success Criteria

- v2 overlay records the M376 gap-tail rows and branch weights
- v2 old-key preference corpus is exported from the M375 base
- no-update exact repair smoke reads the v2 corpus
- research validation passes

## Failure Criteria

- v2 overlay changes actor inputs
- corpus export fails
- no-update exact repair smoke fails
- research validation fails

## Evidence Gates

- infrastructure/corpus refresh only; no PPO run
- keep M375 alpha 0.1 as current promoted base
- export v2 overlay from M376 gap-tail rows
- export old-key preference corpus from the current M375 base
- verify no-update exact repair smoke reads the v2 corpus
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m377-cumulative-gap-tail-v2-corpus-refresh
- type: infrastructure
- checkpoint: runs/m374_gap_tail_final_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m378_cumulative_gap_tail_v2_repair_probe
- reason: M377 exports a v2 old-key corpus with one hard row and four current gap-tail rows and verifies no-update exact repair integration

## Next Blocker

m378-cumulative-gap-tail-v2-repair-probe
