# m873-v4-boundary-preserving-missing-seed-pair-delta-refresh-implementation Research Review

## Summary

- Generated at UTC: 20260525T182014Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: M873 may only produce a no-training diagnostic classification. It must not train, run PPO, promote, or admit objective conversion. M874 must synthesize before another narrow implementation.

## Hypothesis

Boundary-preserving retarget refinement can construct accepted normal-window rows for missing seeds and test whether those rows produce source-diverse pair-delta outcome sensitivity.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m872-v4-boundary-preserving-missing-seed-pair-delta-refresh-design.md, runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/target_weak_seed_rows.csv, runs/m870_v4_generated_boundary_pair_delta_coverage_expansion/pair_delta_sequence_rows.csv, runs/m864_v4_generated_boundary_refinement/combined_generated_boundary_rows.csv, runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
- parent_config: experiments/manifests/m872-v4-boundary-preserving-missing-seed-pair-delta-refresh-design.json
- parent_objective: implement no-training normal-boundary search before pair-delta replay for missing seeds
- derived_from: m872-v4-boundary-preserving-missing-seed-pair-delta-refresh-design
- blocked_by: M870 retarget grid skipped the accepted normal-margin window for all retarget replay rows
- supersedes: None
- invalidates: None

## Success Criteria

- M873 implements normal-boundary search with original point and bracket refinement
- M873 only runs pair-delta replay on accepted normal-window candidates
- M873 writes normal-boundary trace candidate and rejected artifacts
- M873 writes pair-delta sequence accepted balanced and split artifacts
- M873 preserves actor and residual-head checksums
- M873 keeps objective training PPO and promotion blocked

## Failure Criteria

- M873 trains actor or residual-head parameters
- M873 runs PPO
- M873 promotes a checkpoint
- M873 counts colliding-normal rows as accepted evidence
- M873 lowers accepted-row thresholds
- M873 skips branch synthesis as the next route

## Evidence Gates

- M873 must implement normal-boundary search before pair-delta replay
- M873 must keep actor and residual-head checksums unchanged
- M873 must write separate normal-boundary and pair-delta artifacts
- M873 must not lower accepted-row thresholds
- M873 must not run PPO or promote
- M873 must route next to branch synthesis

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor parameters
- do not train M761 residual-head parameters
- do not run PPO
- do not promote a checkpoint
- do not lower accepted-row thresholds
- do not replay pair-delta rows unless normal branch is in accepted window
- do not count component-control rows as primary pair-delta evidence
- do not create another narrow implementation after M873 before synthesis

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- contract_violation

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

Boundary-preserving missing-seed refresh has not yet been implemented
