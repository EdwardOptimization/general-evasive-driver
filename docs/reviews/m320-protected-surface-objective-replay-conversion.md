# m320-protected-surface-objective-replay-conversion Research Review

## Summary

- Generated at UTC: 20260523T060636Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: admit_m321_source_diverse_protected_gate_design
- Decision reason: M320 converts M319 surface into compact 17-row 13-pair corpora for m316 m314 and m316_repaired; all objective and replay sanity gates pass with 17 of 17 success drops

## Hypothesis

The M319 source-diverse protected surface can be converted into compact boundary-outcome corpora that are replay-aligned for the M317 current base and adjacent proposal-family checkpoints.

## Lineage

- parent_checkpoint: runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt, runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt, runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
- parent_dataset: runs/m319_m317_family_boundary_robustness_seed9520/accepted_wrong_history_rows.csv
- parent_config: experiments/manifests/m319-m317-family-protected-surface-refresh.json, docs/m319-m317-family-protected-surface-refresh.md
- parent_objective: convert refreshed M317-family protected surface into compact replay-aligned objective corpora before more PPO
- derived_from: m319-m317-family-protected-surface-refresh
- blocked_by: m319-m317-family-protected-surface-refresh
- supersedes: None
- invalidates: None

## Success Criteria

- build compact corpora for m316_a0_0025, m314_base, and m316_repaired
- each corpus keeps physical-pair diversity and at least two targets where possible
- objective sanity passes for each source checkpoint
- replay sanity preserves normal success and wrong-history failure
- no PPO or actor update is run

## Failure Criteria

- compact corpus is duplicate dominated
- objective sanity fails
- replay sanity does not reproduce wrong-history success drops
- M320 runs PPO or changes actor inputs

## Evidence Gates

- build compact protected-surface corpora only from M319 robustness-passing accepted wrong-history rows
- run objective sanity for current base and adjacent proposal-family checkpoints
- run replay sanity so rows reproduce normal-history success plus wrong-history failure
- do not run PPO
- do not change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use duplicate-dominated rows
- do not admit PPO from objective-only success without replay sanity
- do not change actor inputs
- do not tune from private holdout evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m320-protected-surface-objective-replay-conversion
- type: objective_sanity
- checkpoint: runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m321_source_diverse_protected_gate_design
- reason: M320 converts M319 surface into compact 17-row 13-pair corpora for m316 m314 and m316_repaired; all objective and replay sanity gates pass with 17 of 17 success drops

## Next Blocker

m321-source-diverse-protected-gate-design
