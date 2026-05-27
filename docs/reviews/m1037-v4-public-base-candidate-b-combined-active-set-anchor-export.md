# m1037-v4-public-base-candidate-b-combined-active-set-anchor-export Research Review

## Summary

- Generated at UTC: 20260527T001535Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: candidate_b_combined_active_set_anchor_export_pass_route_to_repair_projection_probe
- Decision reason: M1037 exports balanced row16x4 and row16x8 combined active-set anchors with 3957 rows source namespacing and family-normalized weights passing loader sanity

## Hypothesis

M293 rejected-history trajectory data and M1034 M183 row16 normal-trajectory data can be exported as source-namespaced family-normalized combined anchors without PPO, repair, promotion, private holdout, or actor-input change.

## Lineage

- parent_checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: docs/m1036-v4-public-base-candidate-b-combined-active-set-repair-design.md, runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz, runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz
- parent_config: experiments/manifests/m1036-v4-public-base-candidate-b-combined-active-set-repair-design.json
- parent_objective: materialize a source-namespaced family-normalized combined active-set anchor before repair/projection
- derived_from: m1036-v4-public-base-candidate-b-combined-active-set-repair-design
- blocked_by: M1036 rejects naive concatenation because source ids collide and M1034 row16 weight is diluted by M293
- supersedes: None
- invalidates: running exact repair with a naive concatenation of M293 and M1034 anchors, running repair before combined active-set anchor load/weight sanity passes

## Success Criteria

- balanced combined anchor exists
- row16x4 combined anchor exists
- row16x8 combined anchor exists
- summary json exists
- all combined anchors load with load_trajectory_action_anchor
- combined row count equals 3957
- M1034 source ids are offset and do not collide with M293
- family weight sums match declared variant totals
- no PPO repair promotion private holdout or actor-input change occurs

## Failure Criteria

- combined anchor cannot be loaded
- source ids collide
- family weights do not match declared variant totals
- combined row count is not 3957
- export runs repair or PPO
- actor inputs change

## Evidence Gates

- M1037 must run no PPO
- M1037 must not run repair or promote
- M1037 must not use private holdout
- M1037 must preserve P0 actor inputs
- combined anchors must load through load_trajectory_action_anchor
- M1034 source indices must be namespaced away from M293 source indices
- family-normalized weights must match declared variant totals

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not run exact repair
- do not promote
- do not change actor inputs
- do not use a naive concat with source collisions
- do not let M1034 row16 be diluted by M293 row count
- do not relax M997 thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1037-v4-public-base-candidate-b-combined-active-set-anchor-export
- type: infrastructure
- checkpoint: runs/m1037_candidate_b_combined_active_set_anchor_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_combined_active_set_anchor_export_pass_route_to_repair_projection_probe
- reason: M1037 exports balanced row16x4 and row16x8 combined active-set anchors with 3957 rows source namespacing and family-normalized weights passing loader sanity

## Next Blocker

m1038-v4-public-base-candidate-b-combined-active-set-repair-projection-probe
