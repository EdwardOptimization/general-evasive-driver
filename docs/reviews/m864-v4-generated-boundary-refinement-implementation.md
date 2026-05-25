# m864-v4-generated-boundary-refinement-implementation Research Review

## Summary

- Generated at UTC: 20260525T170955Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_generated_boundary_refinement_sparse_useful
- Decision reason: M864 refines M860 generated brackets into 42 accepted refined rows and 59 combined boundary-new-to-M844 rows with 365 primary pairability projections passing sparse generated-boundary gate but not strong gate

## Hypothesis

No-training refinement of M860 generated wide/negative brackets can lift combined generated-boundary coverage to sparse gate before pair-delta mining.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m863-v4-pair-delta-boundary-expansion-branch-synthesis.md, docs/m862-v4-generated-boundary-refinement-design.md, runs/m860_v4_closer_obstacle_source_generation/summary.json, runs/m860_v4_closer_obstacle_source_generation/generation_plan_rows.csv, runs/m860_v4_closer_obstacle_source_generation/generated_replay_rows.csv, runs/m860_v4_closer_obstacle_source_generation/accepted_generated_boundary_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
- parent_config: experiments/manifests/m863-v4-pair-delta-boundary-expansion-branch-synthesis.json
- parent_objective: implement no-training refinement of M860 generated wide/negative brackets
- derived_from: m863-v4-pair-delta-boundary-expansion-branch-synthesis
- blocked_by: M860 generated brackets have not yet been refined into accepted boundary rows
- supersedes: None
- invalidates: None

## Success Criteria

- M864 implements bracket selection from M860 generated replay rows
- M864 writes refined and combined boundary artifacts
- M864 verifies actor and residual-head checksums unchanged
- M864 classifies refined and combined generated-boundary coverage without pair-delta replay
- M864 keeps PPO and promotion blocked

## Failure Criteria

- M864 trains actor or residual-head parameters
- M864 runs PPO
- M864 promotes a checkpoint
- M864 runs pair-delta sequence replay
- M864 mutates actor input contract

## Evidence Gates

- M864 must implement no-training generated-boundary refinement only
- M864 must select M860 same-source same-axis wide/negative brackets
- M864 must write refined and combined accepted boundary artifacts
- M864 must preserve actor and residual-head checksums
- M864 must not run pair-delta sequence replay train or promote

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not add hidden fault labels or oracle fields to actor input
- do not replay pair-delta sequences in M864
- do not count M860 duplicate accepted rows as new refined coverage

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- milestone: m864-v4-generated-boundary-refinement-implementation
- type: infrastructure
- checkpoint: runs/m864_v4_generated_boundary_refinement/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_generated_boundary_refinement_sparse_useful
- reason: M864 refines M860 generated brackets into 42 accepted refined rows and 59 combined boundary-new-to-M844 rows with 365 primary pairability projections passing sparse generated-boundary gate but not strong gate

## Next Blocker

M864 sparse generated-boundary result has not yet been audited before pair-delta refresh
