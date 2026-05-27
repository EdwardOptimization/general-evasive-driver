# m1113-v4-public-base-materialized-actor-update-proof-washout-audit Research Review

## Summary

- Generated at UTC: 20260527T203958Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_actor_update_proof_washout_audit_route_to_failed_wrong_history_retention_design
- Decision reason: M1113 audits M1112 and finds all 47 lost success-drop events are wrong-history branches becoming safe with zero normal-lost events; route to failed wrong-history retention design

## Hypothesis

M1112 failed because the actor update made wrong-history replay branches safer while preserving normal behavior.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt
- parent_dataset: docs/m1112-v4-public-base-materialized-actor-update-full-public-gate.md, runs/m1112_materialized_actor_update_full_public_gate/summary.json, runs/m1112_materialized_actor_update_full_public_gate/proof_replay_summary.csv, runs/m1112_materialized_actor_update_full_public_gate/family_intersection_public_gate/replay_gate_summary.csv, runs/m1112_materialized_actor_update_full_public_gate/source_diverse_protected_diagnostic/replay_gate_summary.csv
- parent_config: experiments/manifests/m1112-v4-public-base-materialized-actor-update-full-public-gate.json
- parent_objective: audit why exact-improving materialized actor update washed out replay proof surfaces
- derived_from: m1112-v4-public-base-materialized-actor-update-full-public-gate
- blocked_by: M1112 rejects m1110_110901 as proof_washout
- supersedes: None
- invalidates: continuing actor updates without proof-washout audit, PPO from m1110_110901, promotion of m1110_110901

## Success Criteria

- audit artifact exists
- failed proof tiers are summarized
- normal-success versus wrong-history-success mode is classified
- next repair branch is explicit
- no actor training, PPO, replay, corpus build, mining, promotion, or private holdout occurs

## Failure Criteria

- audit artifact is missing
- failure mode remains ambiguous
- next route is ambiguous
- actor training, PPO, replay, corpus build, mining, promotion, or private holdout starts

## Evidence Gates

- M1113 must audit existing M1112 artifacts only
- M1113 must not train actor weights
- M1113 must not run PPO
- M1113 must not run replay
- M1113 must not build corpus or mine rows
- M1113 must not promote
- M1113 must not use private holdout
- M1113 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not build corpus
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not try backup M1110 candidates without audit

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1113-v4-public-base-materialized-actor-update-proof-washout-audit
- type: gate
- checkpoint: docs/m1113-v4-public-base-materialized-actor-update-proof-washout-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_actor_update_proof_washout_audit_route_to_failed_wrong_history_retention_design
- reason: M1113 audits M1112 and finds all 47 lost success-drop events are wrong-history branches becoming safe with zero normal-lost events; route to failed wrong-history retention design

## Next Blocker

m1114-v4-public-base-materialized-failed-wrong-history-retention-design
