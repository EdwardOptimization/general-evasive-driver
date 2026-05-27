# m1089-v4-public-base-source-balanced-relocation-run-design Research Review

## Summary

- Generated at UTC: 20260527T171414Z
- Type: gate
- Gate tier: proof
- Promotion decision: source_balanced_relocation_design_route_to_runner_implementation
- Decision reason: M1089 designs relocation-time source balancing and routes to runner implementation because existing code cannot feed balanced candidates into relocation replay

## Hypothesis

A relocation-time source-balanced run design can convert M1088's adequate candidate budget into a concrete next step without weakening proof-surface robustness thresholds or using the old six-pair accepted export.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: runs/m1088_source_balanced_boundary_existing_artifact_smoke/summary.json, runs/m1088_source_balanced_boundary_existing_artifact_smoke/source_budget_summary.json, docs/m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke.md, docs/m1086-v4-public-base-source-balanced-boundary-tooling-implementation.md, docs/training-stage-discipline.md
- parent_config: experiments/manifests/m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke.json
- parent_objective: design a source-balanced relocation path after M1088 showed the existing candidate budget is ready but the old boundary export remains six-pair limited
- derived_from: m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke
- blocked_by: M1088 source budget is ready with 371 eligible physical pairs and 370 selected physical pairs, but accepted boundary export still has only six physical pairs
- supersedes: None
- invalidates: converting the old M1083 accepted rows directly into a protected or preference corpus, another post-filtering attempt over the six-pair accepted export, weakening the ten-physical-pair robustness threshold

## Success Criteria

- M1089 design artifact exists
- design states why post-filtering M1083 accepted rows is invalid
- design specifies how source-balanced selected candidates enter boundary relocation
- design preserves accepted wrong-history rows >= 80, physical pairs >= 10, left steps >= 5, checkpoints >= 3, targets >= 2, margin buckets >= 2, success_drop_fraction == 1.0, max rows per pair fraction <= 0.25
- design routes to an implementation milestone if current code cannot execute relocation-time source balancing
- no training, PPO, promotion, private holdout, or threshold weakening occurs

## Failure Criteria

- design relies on old six-pair accepted rows
- design weakens robustness thresholds
- design cannot identify whether implementation is needed
- training, PPO, promotion, or private holdout starts

## Evidence Gates

- M1089 must not train
- M1089 must not run PPO
- M1089 must not promote
- M1089 must not use private holdout
- M1089 must preserve existing robustness thresholds
- M1089 must design relocation-time source balancing rather than post-filtering old accepted rows
- M1089 must decide whether the next milestone is implementation or a run with existing code

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not convert M1083 six-pair accepted rows
- do not lower source-diversity or success-drop thresholds
- do not claim driver improvement from a design milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1089-v4-public-base-source-balanced-relocation-run-design
- type: gate
- checkpoint: docs/m1089-v4-public-base-source-balanced-relocation-run-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_relocation_design_route_to_runner_implementation
- reason: M1089 designs relocation-time source balancing and routes to runner implementation because existing code cannot feed balanced candidates into relocation replay

## Next Blocker

m1090-v4-public-base-source-balanced-relocation-runner-implementation
