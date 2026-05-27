# m1129-v4-public-base-row15-projection-promotion-audit Research Review

## Summary

- Generated at UTC: 20260527T220322Z
- Type: gate
- Gate tier: promotion
- Promotion decision: row15_projection_promote_public_gate_base
- Decision reason: M1129 promotes alpha_0_15 as the current public-gate base scoped strictly to public proof-base hardening; no PPO performance private-holdout paper-level real-vehicle or level3 self-ID claim

## Hypothesis

Alpha_0_15 has enough public evidence to be promoted as the current public-gate base for proof-base hardening, with no PPO or private-holdout claim.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1127-v4-public-base-row15-projection-full-public-gate.md, docs/m1128-v4-public-base-row15-projection-branch-synthesis.md, runs/m1127_row15_projection_full_public_gate/summary.json, runs/m1127_row15_projection_m1107_exact_eval/summary.json
- parent_config: experiments/manifests/m1128-v4-public-base-row15-projection-branch-synthesis.json
- parent_objective: audit whether alpha_0_15 should become the current public-gate base as proof-base hardening
- derived_from: m1127-v4-public-base-row15-projection-full-public-gate, m1128-v4-public-base-row15-projection-branch-synthesis
- blocked_by: promotion requires a separate audit after branch synthesis
- supersedes: None
- invalidates: starting PPO from alpha_0_15 before promotion decision, claiming private-holdout or paper-level evidence from public gates

## Success Criteria

- promotion audit artifact exists
- M1127 exact, proof, family, source-diverse, generalization, and behavior evidence is summarized
- promotion decision is explicit
- claim scope is limited to public proof-base hardening if promoted
- no actor training, PPO, replay, objective optimization, mining, private holdout, or actor-input change occurs

## Failure Criteria

- promotion audit artifact is missing
- promotion scope is ambiguous
- public and private evidence are conflated
- actor training, PPO, replay, objective optimization, mining, private holdout, or actor-input change starts

## Evidence Gates

- M1129 must audit M1127 exact, proof, family, source-diverse, generalization, and behavior gate evidence
- M1129 must decide whether alpha_0_15 is promotable only as public proof-base hardening
- M1129 may update current-status public-gate base only if the audit promotes
- M1129 must not train actor weights
- M1129 must not run PPO
- M1129 must not run replay
- M1129 must not run objective optimization
- M1129 must not mine rows
- M1129 must not use private holdout
- M1129 must preserve actor inputs

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
- do not claim medium-PPO performance improvement or paper-level generalization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1129-v4-public-base-row15-projection-promotion-audit
- type: gate
- checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_projection_promote_public_gate_base
- reason: M1129 promotes alpha_0_15 as the current public-gate base scoped strictly to public proof-base hardening; no PPO performance private-holdout paper-level real-vehicle or level3 self-ID claim

## Next Blocker

m1130-v4-public-base-row15-projection-post-promotion-synthesis
