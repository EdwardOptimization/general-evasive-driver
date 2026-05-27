# m1090-v4-public-base-source-balanced-relocation-runner-implementation Research Review

## Summary

- Generated at UTC: 20260527T174322Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_balanced_relocation_runner_implementation_admit_m1091_run
- Decision reason: M1090 implements full source-balanced relocation runner plus process-v5 self-ID evidence discipline with 48 focused tests passing; no PPO training promotion private holdout or expensive run

## Hypothesis

A tested source-balanced relocation runner can route M1086-selected candidates into boundary relocation replay while preserving artifact-smoke behavior and current robustness thresholds.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1089-v4-public-base-source-balanced-relocation-run-design.md, docs/m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke.md, src/autodrift/source_balanced_boundary_relocation_surface.py, src/autodrift/wrong_history_boundary_relocation_surface.py
- parent_config: experiments/manifests/m1089-v4-public-base-source-balanced-relocation-run-design.json
- parent_objective: implement a full source-balanced boundary relocation runner before running another surface refresh
- derived_from: m1089-v4-public-base-source-balanced-relocation-run-design
- blocked_by: M1089 found existing code can either rerun source-unaware relocation or existing-artifact smoke, but cannot route balanced candidates into relocation replay
- supersedes: None
- invalidates: running old wrong_history_boundary_relocation_surface as the next source-balanced run, calling the existing-artifact smoke a full relocation run, using M1083 six-pair accepted rows as corpus input

## Success Criteria

- source-balanced full-run implementation exists
- selected candidates are passed into relocation replay instead of global top-K
- source-budget failure fails closed before replay
- raw and balanced artifacts are written
- existing artifact-smoke path still works
- self-identification evidence discipline is documented and validator-enforced for M1090+ manifests
- focused tests pass
- research validation passes
- no training, PPO, promotion, private holdout, expensive M1091 run, or threshold weakening occurs

## Failure Criteria

- implementation only post-filters old boundary rows
- implementation reruns source-unaware relocation
- source budget failure can still replay
- artifact-smoke path breaks
- training, PPO, promotion, private holdout, or expensive relocation run starts

## Evidence Gates

- M1090 must not train
- M1090 must not run PPO
- M1090 must not promote
- M1090 must not use private holdout
- M1090 must preserve existing robustness thresholds
- M1090 must keep the existing artifact-smoke path working
- M1090 must not run the expensive M1091 relocation experiment

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not weaken robustness thresholds
- do not implement a post-filter-only path
- do not use old six-pair accepted rows as a corpus

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1090-v4-public-base-source-balanced-relocation-runner-implementation
- type: infrastructure
- checkpoint: docs/m1090-v4-public-base-source-balanced-relocation-runner-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_relocation_runner_implementation_admit_m1091_run
- reason: M1090 implements full source-balanced relocation runner plus process-v5 self-ID evidence discipline with 48 focused tests passing; no PPO training promotion private holdout or expensive run

## Next Blocker

m1091-v4-public-base-source-balanced-boundary-relocation-run
