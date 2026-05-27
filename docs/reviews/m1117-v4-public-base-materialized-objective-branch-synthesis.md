# m1117-v4-public-base-materialized-objective-branch-synthesis Research Review

## Summary

- Generated at UTC: 20260527T210452Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_objective_branch_synthesis_open_failed_wrong_history_retention_repair
- Decision reason: M1117 closes materialized_objective_corpus_sanity after M1107-M1116 and opens failed_wrong_history_retention_repair for a bounded retention-aware actor update without PPO replay promotion or private holdout

## Hypothesis

M1107-M1116 have completed enough evidence to close materialized_objective_corpus_sanity and open a failed_wrong_history_retention_repair branch.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1107-v4-public-base-materialized-objective-corpus-run.md, docs/m1108-v4-public-base-materialized-objective-result-audit.md, docs/m1109-v4-public-base-materialized-guarded-actor-update-design.md, docs/m1110-v4-public-base-materialized-guarded-actor-update-probe.md, docs/m1111-v4-public-base-materialized-actor-update-full-public-gate-design.md, docs/m1112-v4-public-base-materialized-actor-update-full-public-gate.md, docs/m1113-v4-public-base-materialized-actor-update-proof-washout-audit.md, docs/m1114-v4-public-base-materialized-failed-wrong-history-retention-design.md, docs/m1115-v4-public-base-materialized-failed-wrong-history-retention-export.md, docs/m1116-v4-public-base-failed-wrong-history-retention-actor-update-design.md
- parent_config: experiments/manifests/m1116-v4-public-base-failed-wrong-history-retention-actor-update-design.json
- parent_objective: synthesize materialized objective corpus branch before running failed wrong-history retention actor update
- derived_from: m1107-v4-public-base-materialized-objective-corpus-run, m1116-v4-public-base-failed-wrong-history-retention-actor-update-design
- blocked_by: workflow synthesis cadence reached after M1116
- supersedes: None
- invalidates: running the M1116-designed actor update before branch synthesis, continuing materialized_objective_corpus_sanity without synthesis, overclaiming M1107-M1116 as driver improvement evidence

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

- M1117 must synthesize M1107-M1116 branch evidence
- M1117 must not train actor weights
- M1117 must not run PPO
- M1117 must not run replay
- M1117 must not run objective optimization
- M1117 must not mine rows
- M1117 must not promote
- M1117 must not use private holdout
- M1117 must preserve actor inputs

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

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1117-v4-public-base-materialized-objective-branch-synthesis
- type: gate
- checkpoint: docs/m1117-v4-public-base-materialized-objective-branch-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_objective_branch_synthesis_open_failed_wrong_history_retention_repair
- reason: M1117 closes materialized_objective_corpus_sanity after M1107-M1116 and opens failed_wrong_history_retention_repair for a bounded retention-aware actor update without PPO replay promotion or private holdout

## Next Blocker

m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe
