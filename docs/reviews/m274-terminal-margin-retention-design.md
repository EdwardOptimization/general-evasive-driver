# m274-terminal-margin-retention-design Research Review

## Summary

- Generated at UTC: 20260522T180734Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: implement_terminal_margin_retention_surface_export
- Decision reason: M274 selects a two-layer retention design: hard simulator terminal-margin gate plus trajectory-anchor proxy with inverse-margin fragile-row weights before any further update

## Hypothesis

Adding an explicit terminal-margin retention layer for fragile closed-loop rows can prevent M271-style objective improvements from crossing near-zero normal-history clearance margins.

## Lineage

- parent_checkpoint: runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
- parent_dataset: runs/m273_m272_boundary_trust_region_audit/row16_alpha_audit.csv, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m273-m272-boundary-trust-region-audit.json, docs/m273-m272-boundary-trust-region-audit.md
- parent_objective: design terminal-margin retention for fragile closed-loop proof rows
- derived_from: m273-m272-boundary-trust-region-audit
- blocked_by: m273-m272-boundary-trust-region-audit
- supersedes: None
- invalidates: None

## Success Criteria

- specify how terminal-margin rows are represented and weighted
- define the loss or gate that protects near-zero normal-history margins
- identify required code changes or explain why existing tools are sufficient
- pre-register the first guarded actor-update attempt that uses the retention layer
- no PPO is run

## Failure Criteria

- retention design only anchors first actions and ignores terminal margin
- design requires actor privileged inputs
- design permits a candidate that fails M183/M170 row16
- PPO or actor update is run before design validation

## Evidence Gates

- design a terminal-margin retention objective or harness
- preserve actor input contract
- include M183/M170 row16 as a hard retention row
- do not run PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M274
- do not run a new actor update before the retention design is validated
- do not loosen M183/M170 row16
- do not use hidden params or privileged actor inputs
- do not claim promotion

## Failure Taxonomy

- none

## Scoreboard

- milestone: m274-terminal-margin-retention-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: implement_terminal_margin_retention_surface_export
- reason: M274 selects a two-layer retention design: hard simulator terminal-margin gate plus trajectory-anchor proxy with inverse-margin fragile-row weights before any further update

## Next Blocker

m275-terminal-margin-retention-surface-export
