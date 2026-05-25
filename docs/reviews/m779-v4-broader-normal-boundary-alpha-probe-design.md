# m779-v4-broader-normal-boundary-alpha-probe-design Research Review

## Summary

- Generated at UTC: 20260525T020549Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: normal_boundary_alpha_probe_design_admit_m780
- Decision reason: M779 pre-registers lower-alpha no-training replay alphas 0.0 0.05 0.1 0.125 0.15 0.175 0.2 to test whether M777 strict-retention failure is a narrow alpha boundary or residual objective blocker

## Hypothesis

M777's strict normal-retention failure may be a narrow alpha-threshold cliff around one near-boundary source; a pre-registered lower-alpha probe can test whether residual intervention sensitivity survives under strict normal retention.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m778-v4-limited-broader-residual-replay-audit.md, docs/m777-v4-limited-broader-residual-replay-implementation.md, runs/m777_v4_limited_broader_residual_replay/summary.json, runs/m777_v4_limited_broader_residual_replay/alpha_metrics.csv, runs/m777_v4_limited_broader_residual_replay/replay_rows.csv, runs/m773_v4_broader_source_holdout_corpus_export/summary.json, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m778-v4-limited-broader-residual-replay-audit.json, experiments/manifests/m777-v4-limited-broader-residual-replay-implementation.json, configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
- parent_objective: design a pre-registered no-training lower-alpha boundary probe after M777 strict normal-retention failure
- derived_from: m778-v4-limited-broader-residual-replay-audit
- blocked_by: m778-v4-limited-broader-residual-replay-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M779 fixes the probe inputs to M568 actor, M761 residual head, and M773 positive/contrast rows
- M779 pre-registers lower alphas before implementation
- M779 keeps alpha 0.2 as the failed reference point
- M779 requires strict normal_success_rate == 1.0 and normal_collision_rate == 0.0
- M779 requires intervention action-gap and margin-gap improvement versus base
- M779 requires source and duplicate-row stratification for seed 77025/source_index 12
- M779 blocks PPO training residual retraining and promotion

## Failure Criteria

- design runs replay instead of only designing it
- design trains actor or residual parameters
- design promotes a checkpoint
- design retroactively reclassifies M777 alpha 0.2 as strict pass
- design omits the normal-retention gate
- design hides source concentration

## Evidence Gates

- M779 designs a no-training lower-alpha boundary probe on M773 broader corpus
- M779 preserves alpha 0.2 strict-normal-retention failure as the blocker
- M779 pre-registers a lower-alpha ladder instead of retroactive tuning
- M779 requires strict normal-retention and intervention-sensitivity metrics
- M779 requires source 77025/source_index 12 stratification
- PPO training residual retraining and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not run the alpha probe in M779
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not erase or reinterpret M777 alpha 0.2 as a pass
- do not choose a lower alpha after seeing M780 results
- do not hide seed 77025/source_index 12 normal collisions
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m779-v4-broader-normal-boundary-alpha-probe-design
- type: infrastructure
- checkpoint: docs/m779-v4-broader-normal-boundary-alpha-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: normal_boundary_alpha_probe_design_admit_m780
- reason: M779 pre-registers lower-alpha no-training replay alphas 0.0 0.05 0.1 0.125 0.15 0.175 0.2 to test whether M777 strict-retention failure is a narrow alpha boundary or residual objective blocker

## Next Blocker

m780-v4-broader-normal-boundary-alpha-probe-implementation
