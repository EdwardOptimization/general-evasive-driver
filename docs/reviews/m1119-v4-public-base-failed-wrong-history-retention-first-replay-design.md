# m1119-v4-public-base-failed-wrong-history-retention-first-replay-design Research Review

## Summary

- Generated at UTC: 20260527T211444Z
- Type: gate
- Gate tier: proof
- Promotion decision: failed_wrong_history_retention_first_replay_design_admit_target_base_first_replay
- Decision reason: M1119 designs strict target-base first replay for old-public and source-diverse M1112 failed surfaces before family replay full replay PPO or promotion

## Hypothesis

The M1118 best pre-replay candidate can be evaluated with a first replay gate that targets the exact old-public and source-diverse surfaces that failed in M1112 before any full replay or promotion.

## Lineage

- parent_checkpoint: runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
- parent_dataset: runs/m1118_failed_wrong_history_retention_actor_update_probe/summary.json, docs/m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe.md
- parent_config: experiments/manifests/m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe.json
- parent_objective: design first replay gates for the M1118 best pre-replay candidate
- derived_from: m1118-v4-public-base-failed-wrong-history-retention-actor-update-probe
- blocked_by: M1118 passed only pre-replay exact and anchor gates
- supersedes: None
- invalidates: running full replay without first-replay design, promoting M1118 without replay, running PPO before M1118 replay gates

## Success Criteria

- old public first replay surfaces are listed
- source-diverse first replay surfaces are listed
- family-intersection rows remain mandatory diagnostics but not training anchors
- candidate checkpoint and base checkpoint are fixed
- no replay, actor training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design skips M1112 failed target-base surfaces
- design allows replay promotion directly
- design uses short-family hidden states as training anchors
- replay, actor training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1119 may design first replay gates for the M1118 best candidate
- M1119 must not run replay
- M1119 must not train actor weights
- M1119 must not run PPO
- M1119 must not promote
- M1119 must not use private holdout
- M1119 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run replay
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip old public or source-diverse first replay
- do not treat M1118 pre-replay pass as driver improvement

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1119-v4-public-base-failed-wrong-history-retention-first-replay-design
- type: gate
- checkpoint: docs/m1119-v4-public-base-failed-wrong-history-retention-first-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: failed_wrong_history_retention_first_replay_design_admit_target_base_first_replay
- reason: M1119 designs strict target-base first replay for old-public and source-diverse M1112 failed surfaces before family replay full replay PPO or promotion

## Next Blocker

m1120-v4-public-base-failed-wrong-history-retention-first-replay-run
