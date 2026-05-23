# m426-source-coupled-nullspace-implementation Research Review

## Summary

- Generated at UTC: 20260523T174414Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m427_source_coupled_nullspace_projection_probe
- Decision reason: M426 implements per-source trajectory losses projected recovery-gradient helper optional exact-repair path and a 197-row hard-guard anchor with no-update exact smoke passing

## Hypothesis

The exact repair tool can support source-coupled projected recovery gradients and per-source hard guard reporting without changing actor inputs or running a projection experiment.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m422_mixed_radius_anchor/mixed_b_radius_anchor.npz, runs/m422_mixed_radius_anchor/radius_anchor_sources.csv
- parent_config: experiments/manifests/m425-source-coupled-recovery-nullspace-design.json
- parent_objective: implement source-coupled projected recovery tooling for exact repair
- derived_from: m425-source-coupled-recovery-nullspace-design
- blocked_by: m424-mixed-radius-utility-ceiling-audit
- supersedes: None
- invalidates: None

## Success Criteria

- implement per-source trajectory guard loss reporting
- implement projected recovery-gradient helper with deterministic tests
- wire optional source-coupled projection config without changing default behavior
- run a no-update smoke proving existing exact repair behavior remains unchanged

## Failure Criteria

- default exact repair behavior changes
- projection helper cannot keep hard-guard first-order loss from increasing in tests
- implementation changes actor inputs or outputs
- milestone runs PPO or promotes a checkpoint

## Evidence Gates

- focused unit tests for per-source guard losses
- focused unit tests for projected recovery gradient
- no-update exact repair smoke with projected recovery disabled
- no PPO run
- no checkpoint promotion
- no actor input/output change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m426-source-coupled-nullspace-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m427_source_coupled_nullspace_projection_probe
- reason: M426 implements per-source trajectory losses projected recovery-gradient helper optional exact-repair path and a 197-row hard-guard anchor with no-update exact smoke passing

## Next Blocker

m427-source-coupled-nullspace-projection-probe
