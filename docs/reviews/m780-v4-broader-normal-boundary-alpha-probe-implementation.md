# m780-v4-broader-normal-boundary-alpha-probe-implementation Research Review

## Summary

- Generated at UTC: 20260525T021742Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: v4_residual_alpha_0125_boundary_candidate
- Decision reason: M780 finds alpha 0.125 keeps normal success 1.0 collision 0.0 and improves intervention gap and margin over base while alpha 0.15 and above collide at the same seed 77025 source_index 12 near-boundary source

## Hypothesis

A lower residual alpha may preserve strict normal retention on the broader M773 corpus while retaining a measurable intervention action-gap and margin-gap improvement.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m779-v4-broader-normal-boundary-alpha-probe-design.md, docs/m778-v4-limited-broader-residual-replay-audit.md, runs/m777_v4_limited_broader_residual_replay/summary.json, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m779-v4-broader-normal-boundary-alpha-probe-design.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: run pre-registered lower-alpha normal-boundary probe without training or promotion
- derived_from: m779-v4-broader-normal-boundary-alpha-probe-design
- blocked_by: m779-v4-broader-normal-boundary-alpha-probe-design
- supersedes: None
- invalidates: None

## Success Criteria

- M780 runs the registered command with alphas 0.0 0.05 0.1 0.125 0.15 0.175 0.2
- M780 reconstructs at least 0.98 of M773 rows with no metadata misses
- M780 reports alpha-specific normal retention and intervention sensitivity
- M780 reports source 77025/source_index 12 normal boundary metrics
- M780 records actor/training/PPO/promotion flags as false

## Failure Criteria

- implementation changes the alpha ladder
- implementation trains actor or residual parameters
- implementation runs PPO
- implementation promotes a checkpoint
- implementation omits normal-retention metrics
- implementation hides alpha 0.2 failure

## Evidence Gates

- M780 runs the pre-registered lower-alpha ladder on M773 broader corpus
- M780 keeps alpha 0.2 as failed reference
- M780 reports strict normal-retention and intervention-sensitivity metrics
- M780 stratifies seed 77025/source_index 12 normal boundary source
- M780 does not train mutate actor or residual parameters run PPO or promote

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not add or remove alphas after seeing results
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not lower strict normal-retention criteria
- do not hide seed 77025/source_index 12
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m780-v4-broader-normal-boundary-alpha-probe-implementation
- type: generalization
- checkpoint: runs/m780_v4_broader_normal_boundary_alpha_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_residual_alpha_0125_boundary_candidate
- reason: M780 finds alpha 0.125 keeps normal success 1.0 collision 0.0 and improves intervention gap and margin over base while alpha 0.15 and above collide at the same seed 77025 source_index 12 near-boundary source

## Next Blocker

m781-v4-broader-normal-boundary-alpha-probe-audit
