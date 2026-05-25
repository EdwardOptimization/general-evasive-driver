# m849-v4-pair-delta-focused-source-balanced-mining-design Research Review

## Summary

- Generated at UTC: 20260525T134554Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: pair_delta_focused_source_balanced_mining_design_admit_m850
- Decision reason: M849 designs pair-delta-first source-balanced mining with component rows excluded from primary gates and PPO still blocked

## Hypothesis

A pair-delta-focused source-balanced mining design can broaden M847's positive but concentrated pair-delta evidence before objective training.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m848-v4-cross-source-sequence-effective-pair-refresh-audit.md, runs/m847_v4_cross_source_sequence_effective_pair_refresh/summary.json, runs/m847_v4_cross_source_sequence_effective_pair_refresh/pair_candidate_rows.csv, runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_pair_delta_rows.csv, runs/m847_v4_cross_source_sequence_effective_pair_refresh/accepted_sequence_effective_rows.csv
- parent_config: experiments/manifests/m848-v4-cross-source-sequence-effective-pair-refresh-audit.json
- parent_objective: design pair-delta-focused source-balanced mining after M847 sparse pair-positive result
- derived_from: m848-v4-cross-source-sequence-effective-pair-refresh-audit
- blocked_by: M847 accepted pair-delta rows are positive but source/fault concentrated
- supersedes: None
- invalidates: None

## Success Criteria

- M849 writes a design document for pair-delta-focused source-balanced mining
- M849 defines pair-delta-only primary gates
- M849 defines source/fault/seed balance gates
- M849 specifies implementation artifacts and fallback to boundary expansion
- M849 keeps PPO and promotion blocked

## Failure Criteria

- M849 admits PPO or promotion
- M849 trains actor or residual parameters
- M849 accepts component-only positives as pair-delta positives
- M849 ignores M847 pair-delta concentration

## Evidence Gates

- M849 must remain design-only
- M849 must target pair-delta evidence rather than component-axis dominance
- M849 must define source-balanced pair-delta gates
- M849 must keep direct sequence evidence separate from learned self-ID proof
- M849 must keep PPO and promotion blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run replay in M849
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat M847 pair-delta overrides as learned self-ID proof
- do not accept a component-only corpus as a pair-delta corpus
- do not tune thresholds after seeing implementation results

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m849-v4-pair-delta-focused-source-balanced-mining-design
- type: infrastructure
- checkpoint: docs/m849-v4-pair-delta-focused-source-balanced-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pair_delta_focused_source_balanced_mining_design_admit_m850
- reason: M849 designs pair-delta-first source-balanced mining with component rows excluded from primary gates and PPO still blocked

## Next Blocker

M847 pair-delta evidence is positive but too source/fault concentrated for objective design
