# m1163-v4-public-base-row15-promoted-relocation-expansion-design Research Review

## Summary

- Generated at UTC: 20260528T003148Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1163 may only design the relocation-expansion diagnostic. It cannot run mining, relocation, actor training, PPO, promotion, private holdout, actor-input changes, threshold weakening, or failed-surface conversion.

## Hypothesis

A bounded relocation expansion over existing M1161 outcomes can test whether the failed margin-slack surface was caused by too narrow a relocation search rather than absent wrong-history sensitivity.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit.md, runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv, runs/m1161_row15_promoted_margin_slack_surface_seed116100/summary.json
- parent_config: experiments/manifests/m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit.json
- parent_objective: design a relocation-expansion diagnostic that reuses M1161 outcomes without weakening margin-slack acceptance thresholds
- derived_from: m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit
- blocked_by: M1162 classifies M1161 as relocation active-set collapse with wrong-history intervention scarcity
- supersedes: None
- invalidates: rerunning full mining before relocation failure audit route, weakening thresholds before relocation expansion, converting M1161 failed surface

## Success Criteria

- design artifact exists
- relocation-expansion command is explicit
- M1160 acceptance thresholds are preserved
- next run uses existing M1161 outcome CSV
- resource bounds are explicit
- no actor training, PPO, relocation run, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- threshold preservation is ambiguous
- next run route is ambiguous
- actor training, PPO, relocation run, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1163 must design the relocation-expansion diagnostic only
- M1163 must reuse existing M1161 outcome rows for the next run
- M1163 must preserve M1160 acceptance thresholds
- M1163 must not run mining
- M1163 must not run relocation
- M1163 must not train actor weights
- M1163 must not run PPO
- M1163 must not promote
- M1163 must not use private holdout
- M1163 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run mining
- do not run relocation
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken M1160 acceptance thresholds
- do not convert the M1161 failed surface

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1163-v4-public-base-row15-promoted-relocation-expansion-design
