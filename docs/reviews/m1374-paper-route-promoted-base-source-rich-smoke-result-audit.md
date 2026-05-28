# m1374-paper-route-promoted-base-source-rich-smoke-result-audit Research Review

## Summary

- Generated at UTC: 20260528T213445Z
- Type: gate
- Gate tier: process
- Promotion decision: promoted_base_source_rich_smoke_audit_admit_public_wave
- Decision reason: M1374 classifies M1373 as sparse wrong-history positives plus broad reset sensitivity and admits larger public source-rich wave

## Hypothesis

M1373 can be audited as a structurally passing source-rich smoke with sparse wrong-history positives and broad reset sensitivity before choosing the next public source-rich route.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1373_promoted_base_source_rich_smoke/summary.json, docs/m1373-paper-route-promoted-base-source-rich-smoke.md, configs/m990_capability_step_fault_scenarios.json
- parent_config: experiments/manifests/m1373-paper-route-promoted-base-source-rich-smoke.json
- parent_objective: audit sparse wrong-history positives and broad reset-only sensitivity from promoted-base source-rich smoke
- derived_from: m1373-paper-route-promoted-base-source-rich-smoke
- blocked_by: M1373 smoke passes structurally but source-positive cross-fault evidence remains sparse
- supersedes: routing directly from smoke to training, treating sparse accepted rows as source-positive proof, ignoring broad reset-only signal
- invalidates: None

## Success Criteria

- docs/m1374-paper-route-promoted-base-source-rich-smoke-result-audit.md exists
- audit summarizes M1373 scenario, snapshot, matched-pair, accepted, reset-only, rejected, and fidelity results
- audit classifies sparse accepted rows and reset-only rows separately
- audit chooses a next route without private holdout, training, PPO, promotion, actor-input change, or high-fidelity overclaim

## Failure Criteria

- audit document is missing
- audit overclaims sparse accepted rows as source-diverse proof
- audit treats reset-only rows as cross-fault wrong-history proof
- audit routes directly to training, PPO, promotion, private holdout, or high-fidelity claims

## Evidence Gates

- M1374 must audit M1373 artifacts before larger public source-rich waves
- M1374 must classify accepted-row sparsity and reset-only sensitivity separately
- M1374 must choose the next source-rich route without private holdout, training, PPO, or promotion
- M1374 must keep high-fidelity proxy claim boundaries intact

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run new evaluation
- do not promote
- do not use private holdout
- do not add actor inputs
- do not claim source-diverse cross-fault proof from two accepted rows
- do not claim true high-fidelity per-wheel physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1374-paper-route-promoted-base-source-rich-smoke-result-audit
- type: gate
- checkpoint: docs/m1374-paper-route-promoted-base-source-rich-smoke-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promoted_base_source_rich_smoke_audit_admit_public_wave
- reason: M1374 classifies M1373 as sparse wrong-history positives plus broad reset sensitivity and admits larger public source-rich wave

## Next Blocker

m1375-paper-route-promoted-base-source-rich-public-wave
