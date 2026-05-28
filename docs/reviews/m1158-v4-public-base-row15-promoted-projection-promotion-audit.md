# m1158-v4-public-base-row15-promoted-projection-promotion-audit Research Review

## Summary

- Generated at UTC: 20260528T000524Z
- Type: gate
- Gate tier: promotion
- Promotion decision: row15_promoted_projection_promote_public_gate_base
- Decision reason: M1158 promotes alpha_0_05 as current public-gate base scoped strictly to public proof-base hardening with no PPO private-holdout paper-level or driver-performance claim

## Hypothesis

Alpha_0_05 has enough public evidence to be promoted as the current public-gate base for proof-base hardening, with no PPO, private-holdout, or driver-performance claim.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run.md, docs/m1156-v4-public-base-row15-promoted-projection-family-behavior-run.md, docs/m1157-v4-public-base-row15-promoted-projection-diagnostic-result-audit.md, runs/m1156_row15_promoted_projection_m1144_exact_eval/summary.json, runs/m1156_row15_promoted_projection_expanded_public_diagnostic/summary.json
- parent_config: experiments/manifests/m1157-v4-public-base-row15-promoted-projection-diagnostic-result-audit.json
- parent_objective: audit whether alpha_0_05 should replace alpha_0_15 as the current public-gate base for proof-base hardening
- derived_from: m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run, m1156-v4-public-base-row15-promoted-projection-family-behavior-run, m1157-v4-public-base-row15-promoted-projection-diagnostic-result-audit
- blocked_by: promotion requires an explicit audit after M1156 all-pass diagnostics and M1157 result audit
- supersedes: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- invalidates: starting PPO from alpha_0_05 before promotion decision, claiming private-holdout or paper-level evidence from public gates, claiming driver performance improvement from proof-base hardening

## Success Criteria

- promotion audit artifact exists
- M1154 first replay, M1156 expanded public diagnostics, and M1157 caveat audit are summarized
- promotion decision is explicit
- claim scope is limited to public proof-base hardening if promoted
- near-zero margin caveat is preserved
- no actor training, PPO, replay, objective optimization, mining, private holdout, or actor-input change occurs

## Failure Criteria

- promotion audit artifact is missing
- promotion scope is ambiguous
- near-zero margin caveat is omitted
- public and private evidence are conflated
- actor training, PPO, replay, objective optimization, mining, private holdout, or actor-input change starts

## Evidence Gates

- M1158 must audit existing M1154, M1156, and M1157 evidence only
- M1158 must decide whether alpha_0_05 is promotable only as public proof-base hardening
- M1158 may update current-status public-gate base only if the audit promotes
- M1158 must not train actor weights
- M1158 must not run PPO
- M1158 must not run replay
- M1158 must not run objective optimization
- M1158 must not mine rows
- M1158 must not use private holdout
- M1158 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not use private holdout
- do not change actor inputs
- do not promote beyond public proof-base hardening scope
- do not claim medium-PPO performance improvement, paper-level generalization, or level3 self-identification
- do not hide the near-zero row15-promoted wrong-history margin caveat

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1158-v4-public-base-row15-promoted-projection-promotion-audit
- type: gate
- checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_projection_promote_public_gate_base
- reason: M1158 promotes alpha_0_05 as current public-gate base scoped strictly to public proof-base hardening with no PPO private-holdout paper-level or driver-performance claim

## Next Blocker

m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis
