# m961-v4-public-base-direction-target-export-actor-fit-objective-design Research Review

## Summary

- Generated at UTC: 20260526T033317Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: direction_target_export_actor_fit_design_admit_m962
- Decision reason: M961 designs no-training branch-separated export for M960 accepted targets and constrained actor-fit objective before any actor update PPO or promotion

## Hypothesis

M960 accepted direction-target candidates can be exported into a branch-separated target corpus and used to design a constrained actor-fit objective before any training.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m960-v4-public-base-low-tail-direction-family-target-audit-implementation.md, runs/m960_v4_public_base_low_tail_direction_family_target_audit/summary.json, runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_family_summary.csv, runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_rows.csv, runs/m960_v4_public_base_low_tail_direction_family_target_audit/normal_retention_metrics.csv, runs/m960_v4_public_base_low_tail_direction_family_target_audit/m267_direction_target_preflight.csv
- parent_config: experiments/manifests/m960-v4-public-base-low-tail-direction-family-target-audit-implementation.json
- parent_objective: design export and actor-fit objective for M960 accepted direction-target candidates
- derived_from: m960-v4-public-base-low-tail-direction-family-target-audit-implementation
- blocked_by: M960 found joint direction target candidates but no export format or actor-fit objective has been designed
- supersedes: None
- invalidates: actor fitting on M960 targets without branch-separated target export and exact replay gates

## Success Criteria

- design document exists
- accepted target filtering is explicit
- target export schema is explicit
- actor-fit objective terms are explicit
- normal-retention and M267/M264 replay gates remain explicit
- training, PPO, and promotion remain blocked

## Failure Criteria

- design recommends actor fitting before export filtering
- design changes actor inputs
- design omits branch-separated wrong-history handling
- design omits exact target-fit or replay gates
- design promotes a checkpoint

## Evidence Gates

- M961 must not train
- M961 must not run PPO
- M961 must not promote
- M961 must preserve the P0 actor-input contract
- M961 must design a target export format for M960 accepted candidates
- M961 must specify exact target-fit and M267/M264 proof gates before actor fitting

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update model weights
- do not change actor inputs
- do not use private holdout
- do not promote
- do not train directly on all M960 rows without export filtering
- do not move wrong-history branches toward normal safe targets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m961-v4-public-base-direction-target-export-actor-fit-objective-design
- type: infrastructure
- checkpoint: docs/m961-v4-public-base-direction-target-export-actor-fit-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: direction_target_export_actor_fit_design_admit_m962
- reason: M961 designs no-training branch-separated export for M960 accepted targets and constrained actor-fit objective before any actor update PPO or promotion

## Next Blocker

direction target export and actor-fit objective have not been designed
