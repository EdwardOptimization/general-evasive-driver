# m557-m556-route-screen-failure-audit Research Review

## Summary

- Generated at UTC: 20260524T045938Z
- Type: gate
- Gate tier: process
- Promotion decision: audit_admit_targeted_collision_margin_repair_design
- Decision reason: M557 classifies M556 as collision-dominated margin failure after binary success gain and blocks public diagnostics

## Hypothesis

The M556 failure audit can identify whether the new L3 variants are simply more collision-prone near the obstacle, or whether route-screen v2 exposed a narrower margin-retention issue that should guide the next repair design.

## Lineage

- parent_checkpoint: runs/m556_l3_repair_epoch1_clip01_seed3540/checkpoints/checkpoint_step_256.pt, runs/m556_l3_repair_longseq_epoch1_seed3540/checkpoints/checkpoint_step_512.pt, runs/m556_l3_repair_lowentropy_epoch1_seed3540/checkpoints/checkpoint_step_256.pt
- parent_dataset: runs/m556_l3_repair_v2_route_screen_selection/summary.json, runs/m556_l3_repair_v2_route_screen_selection/episodes.csv, runs/m556_l3_repair_v2_route_screen_selection/candidate_decisions.csv, docs/m556-l3-repair-v2-route-screen-selection.md
- parent_config: configs/ppo_m555_l3_repair_epoch1_clip01_4096.json, configs/ppo_m555_l3_repair_longseq_epoch1_4096.json, configs/ppo_m555_l3_repair_lowentropy_epoch1_4096.json
- parent_objective: audit why M556 candidates improve success over L0 but fail margin and collision route-screen checks
- derived_from: m556-l3-repair-v2-route-screen-selection
- blocked_by: m556-l3-repair-v2-route-screen-selection
- supersedes: None
- invalidates: None

## Success Criteria

- audit summarizes best family candidates versus L0/L2 on shared route-screen seeds
- audit classifies the failure mode before any new training
- audit recommends either targeted repair design or stopping the current L3 recipe family
- research validation passes

## Failure Criteria

- audit uses public frozen-source rows
- audit changes thresholds after seeing M556
- audit directly launches more training without diagnosing the gate failure

## Evidence Gates

- audit M556 route-screen terminal patterns before more training
- compare best M556 family candidates against L0/L2 on shared route seeds
- identify whether failure is margin-only, collision-dominated, or seed-clustered
- do not run public frozen-source diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use public frozen-source rows
- do not weaken route-screen v2 thresholds after failure
- do not promote or select a checkpoint from this audit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m557-m556-route-screen-failure-audit
- type: gate
- checkpoint: runs/m557_m556_route_screen_failure_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: audit_admit_targeted_collision_margin_repair_design
- reason: M557 classifies M556 as collision-dominated margin failure after binary success gain and blocks public diagnostics

## Next Blocker

m558-targeted-collision-margin-repair-design
