# m1150-v4-public-base-row15-promoted-first-replay-failure-audit Research Review

## Summary

- Generated at UTC: 20260527T231724Z
- Type: gate
- Gate tier: process
- Promotion decision: repair
- Decision reason: M1150 may only audit the M1149 first-replay wrong-history-safe failure and route the next repair design. It cannot train actor weights, run PPO, run replay, mine rows, promote, use private holdout, change actor inputs, or continue to family-intersection replay.

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

- No scoreboard row recorded.

## Next Blocker

m1150-v4-public-base-row15-promoted-first-replay-failure-audit
