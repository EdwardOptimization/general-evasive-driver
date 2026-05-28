# m1171-v4-public-base-stronger-wrong-history-construction-design Research Review

## Summary

- Generated at UTC: 20260528T014814Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M1171 is design-only. It can design stronger wrong-history construction but cannot run mining, run replay, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert failed rows.

## Hypothesis

The next useful step is to design a wrong-history construction that intentionally pairs current scenes with histories that are action-divergent and terminal-margin-sensitive, because same-shape matched-history relocation only recovers two old physical pairs.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1170-v4-public-base-row15-promoted-margin-slack-surface-refresh-synthesis.md, docs/m1162-v4-public-base-row15-promoted-margin-slack-surface-refresh-failure-audit.md, docs/m1167-v4-public-base-row15-promoted-wrong-history-mechanism-audit.md, docs/m1169-v4-public-base-row15-promoted-relocation-target-microgrid-run.md
- parent_config: experiments/manifests/m1170-v4-public-base-row15-promoted-margin-slack-surface-refresh-synthesis.json
- parent_objective: design a stronger wrong-history construction after same-shape relocation exhausted
- derived_from: m1170-v4-public-base-row15-promoted-margin-slack-surface-refresh-synthesis
- blocked_by: M1170 closes row15_promoted_margin_slack_surface_refresh and opens stronger_wrong_history_construction
- supersedes: None
- invalidates: continuing same-shape relocation expansion without stronger intervention construction, PPO before a broader wrong-history proof surface exists, objective conversion from the two-pair microgrid surface

## Success Criteria

- design artifact exists
- new wrong-history construction criteria are explicit
- metrics for action divergence, terminal-margin sensitivity, and source diversity are explicit
- next audit or run is pre-registered
- no mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- intervention construction remains equivalent to same-shape relocation
- next route is ambiguous
- mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1171 is design-only
- M1171 must not run mining
- M1171 must not run replay
- M1171 must not train actor weights
- M1171 must not run PPO
- M1171 must not promote
- M1171 must not use private holdout
- M1171 must preserve actor inputs
- M1171 must not convert failed surface rows

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run mining
- do not run replay
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not convert failed surface rows
- do not reuse the two-pair microgrid surface as a broad proof corpus

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1171-v4-public-base-stronger-wrong-history-construction-design
