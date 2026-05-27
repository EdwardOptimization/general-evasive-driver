# m1150-v4-public-base-row15-promoted-first-replay-failure-audit Research Review

## Summary

- Generated at UTC: 20260527T232338Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_first_replay_failure_audit_route_to_branch_synthesis
- Decision reason: M1150 audits M1149 and finds all materialized failed geometries were covered by M1144 but low-weight near-boundary braking rows crossed wrong-history terminal margin so unsafe-margin projection is the next branch after synthesis

## Hypothesis

M1149 failed because the M1147 exact-objective actor update improves the deduplicated M1144 objective but does not preserve closed-loop wrong-history unsafe margins on the promoted materialized surface.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt, runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
- parent_dataset: runs/m1149_row15_promoted_actor_update_first_replay/summary.json, runs/m1149_row15_promoted_actor_update_first_replay/first_replay_summary.csv, runs/m1149_row15_promoted_actor_update_first_replay/lost_success_drop_rows.csv, runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz, runs/m1144_row15_promoted_objective_corpus/corpus_summary.json, runs/m1147_row15_promoted_actor_update_exact_eval/summary.json, runs/m1147_row15_promoted_actor_update_parameter_audit/summary.json
- parent_config: experiments/manifests/m1149-v4-public-base-row15-promoted-actor-update-first-replay-run.json
- parent_objective: audit why M1147 exact objective improvement makes M267 and row15-promoted materialized wrong-history branches safe
- derived_from: m1149-v4-public-base-row15-promoted-actor-update-first-replay-run
- blocked_by: M1149 rejects m1147_114602 first replay through 76 wrong-history-safe lost success-drop events
- supersedes: None
- invalidates: family-intersection replay before M1149 failure audit, behavior gates before M1149 failure audit, full public gate before M1149 failure audit, PPO from m1147_114602, promotion of m1147_114602

## Success Criteria

- audit artifact exists
- M1149 failed rows are grouped by surface, target, physical pair, and source label
- M1144 objective coverage of M1149 failed rows is classified
- wrong-history terminal-margin crossing is separated from normal-history regression
- next repair route is explicit
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- audit artifact is missing
- failure concentration remains ambiguous
- M1144 objective coverage remains ambiguous
- next route is ambiguous
- actor training, PPO, replay, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1150 must audit existing M1144, M1147, and M1149 artifacts only
- M1150 must not train actor weights
- M1150 must not run PPO
- M1150 must not run replay
- M1150 must not mine new rows
- M1150 must not promote
- M1150 must not use private holdout
- M1150 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not continue to family-intersection replay before audit
- do not weaken replay thresholds

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1150-v4-public-base-row15-promoted-first-replay-failure-audit
- type: gate
- checkpoint: runs/m1150_row15_promoted_first_replay_failure_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_first_replay_failure_audit_route_to_branch_synthesis
- reason: M1150 audits M1149 and finds all materialized failed geometries were covered by M1144 but low-weight near-boundary braking rows crossed wrong-history terminal margin so unsafe-margin projection is the next branch after synthesis

## Next Blocker

m1151-v4-public-base-row15-promoted-target-materialization-synthesis
