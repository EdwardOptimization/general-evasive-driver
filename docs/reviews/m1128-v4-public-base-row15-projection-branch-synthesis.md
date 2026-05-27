# m1128-v4-public-base-row15-projection-branch-synthesis Research Review

## Summary

- Generated at UTC: 20260527T220014Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_projection_branch_synthesis_route_to_promotion_audit
- Decision reason: M1128 closes failed_wrong_history_retention_repair and opens row15_projection_promotion_audit; alpha_0_15 is ready for public proof-base hardening promotion audit but not PPO performance or private-holdout claims

## Hypothesis

M1118-M1127 have completed enough evidence to close failed_wrong_history_retention_repair and decide whether alpha_0_15 should route to promotion audit or another proof-refresh branch.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe.md, docs/m1119-v4-public-base-failed-wrong-history-retention-first-replay-design.md, docs/m1120-v4-public-base-failed-wrong-history-retention-first-replay-run.md, docs/m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit.md, docs/m1122-v4-public-base-row15-unsafe-margin-retention-design.md, docs/m1123-v4-public-base-row15-unsafe-margin-projection-probe.md, docs/m1124-v4-public-base-row15-projection-family-replay-design.md, docs/m1125-v4-public-base-row15-projection-family-replay.md, docs/m1126-v4-public-base-row15-projection-full-public-gate-design.md, docs/m1127-v4-public-base-row15-projection-full-public-gate.md
- parent_config: experiments/manifests/m1127-v4-public-base-row15-projection-full-public-gate.json
- parent_objective: synthesize failed_wrong_history_retention_repair after alpha_0_15 passes the expanded full public gate
- derived_from: m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe, m1127-v4-public-base-row15-projection-full-public-gate
- blocked_by: workflow synthesis cadence reached after M1127
- supersedes: None
- invalidates: promoting alpha_0_15 before branch synthesis, running PPO from alpha_0_15 before branch synthesis, using private holdout before branch synthesis

## Success Criteria

- synthesis artifact exists
- evidence summary is explicit
- supported claims are explicit
- falsified or unsupported claims are explicit
- failure taxonomy summary is explicit
- public-gate overfit risk is explicit
- next branch decision is explicit
- no actor training, PPO, replay, objective optimization, mining, promotion, or private holdout occurs

## Failure Criteria

- synthesis artifact is missing
- supported and unsupported claims are conflated
- next branch decision is ambiguous
- actor training, PPO, replay, objective optimization, mining, promotion, or private holdout starts

## Evidence Gates

- M1128 must synthesize M1118-M1127 branch evidence
- M1128 must decide whether alpha_0_15 should route to promotion audit, further proof refresh, or stop
- M1128 must not train actor weights
- M1128 must not run PPO
- M1128 must not run replay
- M1128 must not run objective optimization
- M1128 must not mine rows
- M1128 must not promote
- M1128 must not use private holdout
- M1128 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip evidence synthesis after the 10-milestone cadence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1128-v4-public-base-row15-projection-branch-synthesis
- type: gate
- checkpoint: docs/m1128-v4-public-base-row15-projection-branch-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_projection_branch_synthesis_route_to_promotion_audit
- reason: M1128 closes failed_wrong_history_retention_repair and opens row15_projection_promotion_audit; alpha_0_15 is ready for public proof-base hardening promotion audit but not PPO performance or private-holdout claims

## Next Blocker

m1129-v4-public-base-row15-projection-promotion-audit
