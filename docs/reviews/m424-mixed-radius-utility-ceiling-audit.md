# m424-mixed-radius-utility-ceiling-audit Research Review

## Summary

- Generated at UTC: 20260523T173308Z
- Type: gate
- Gate tier: process
- Promotion decision: stop_radius_only_path_admit_m425_source_coupled_recovery_nullspace_design
- Decision reason: M424 classifies the mixed-radius path as a radius-only utility ceiling because M267 rows 6 and 15 plus old-key 10023 bind before recovery retention reaches 20 percent

## Hypothesis

The M423 proof-safe utility ceiling can be explained by specific active proof rows and recovery-target conflicts, deciding whether another per-row radius profile is justified or the radius-only path should stop.

## Lineage

- parent_checkpoint: runs/m423_mixed_a_projection_ltraj1e13_s40_seed10153/candidate_checkpoint.pt, runs/m423_mixed_b_projection_ltraj1e13_s40_seed10154/candidate_checkpoint.pt, runs/m423_mixed_c_projection_ltraj1e13_s40_seed10155/candidate_checkpoint.pt
- parent_dataset: runs/m422_mixed_radius_anchor/mixed_a_radius_anchor.npz, runs/m422_mixed_radius_anchor/mixed_b_radius_anchor.npz, runs/m422_mixed_radius_anchor/mixed_c_radius_anchor.npz, runs/m422_mixed_radius_anchor/radius_anchor_sources.csv
- parent_config: experiments/manifests/m423-mixed-radius-projection-probe.json
- parent_objective: mixed-radius no-PPO exact projection with active-set replay hinge anchors
- derived_from: m423-mixed-radius-projection-probe
- blocked_by: m423-mixed-radius-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- quantify recovery retention and proof failures across M420 conservative medium and M423 mixed_a mixed_b mixed_c
- identify whether M267 rows 6 and 15 or old-key 10023 are the binding constraints
- determine whether proof-safe utility below 0.20 is a radius-only limitation or an implementation artifact
- produce a concrete next blocker with no actor-contract change

## Failure Criteria

- audit cannot explain why mixed_b is proof-safe but below the utility threshold
- audit recommends a new projection without identifying the binding rows
- audit changes actor inputs or output contract
- audit uses private holdout or threshold changes

## Evidence Gates

- no PPO run
- no checkpoint promotion
- compare M420 conservative medium and M423 mixed_a mixed_b mixed_c
- identify active proof failures and recovery-retention ceiling
- recommend next residual or stop radius-only path

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- objective_overfit
- proof_washout
- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m424-mixed-radius-utility-ceiling-audit
- type: gate
- checkpoint: runs/m423_mixed_b_projection_ltraj1e13_s40_seed10154/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: stop_radius_only_path_admit_m425_source_coupled_recovery_nullspace_design
- reason: M424 classifies the mixed-radius path as a radius-only utility ceiling because M267 rows 6 and 15 plus old-key 10023 bind before recovery retention reaches 20 percent

## Next Blocker

m425-source-coupled-recovery-nullspace-design
