# m1179-v4-public-base-stronger-wrong-history-construction-synthesis Research Review

## Summary

- Generated at UTC: 20260528T022956Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1179 may only synthesize the M1171-M1178 branch and choose the next branch. It cannot run mining, run replay, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert failed surface rows.

## Hypothesis

The stronger_wrong_history_construction branch should pivot because action-divergent artifact-only construction improves old-active-set density but does not produce a broad source-diverse wrong-history surface.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1170-v4-public-base-row15-promoted-margin-slack-surface-refresh-synthesis.md, docs/m1172-v4-public-base-wrong-history-action-divergence-artifact-audit.md, docs/m1175-v4-public-base-action-divergent-candidate-export-run.md, docs/m1177-v4-public-base-action-divergent-bounded-relocation-run.md, docs/m1178-v4-public-base-action-divergent-relocation-scarcity-audit.md
- parent_config: experiments/manifests/m1178-v4-public-base-action-divergent-relocation-scarcity-audit.json
- parent_objective: synthesize the stronger_wrong_history_construction branch after artifact-only action-divergent relocation remains old-active-set dominated
- derived_from: m1178-v4-public-base-action-divergent-relocation-scarcity-audit
- blocked_by: M1178 confirms M1177 only expands the old two-pair active set
- supersedes: None
- invalidates: continuing artifact-only action-divergent relocation without synthesis, training from M1175/M1177 rows before a new branch decision, converting M1177 rows into a proof corpus

## Success Criteria

- synthesis artifact exists
- M1171-M1178 evidence is summarized
- supported claims are explicit
- falsified claims are explicit
- failure taxonomy is explicit
- public-gate overfit risk is explicit
- next branch decision is explicit
- no mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- synthesis artifact is missing
- branch decision is ambiguous
- artifact-only relocation expansion is continued without evidence
- next blocker is ambiguous
- mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1179 must synthesize M1171 through M1178
- M1179 must close or explicitly continue the stronger_wrong_history_construction branch
- M1179 must not run mining
- M1179 must not run replay
- M1179 must not train actor weights
- M1179 must not run PPO
- M1179 must not promote
- M1179 must not use private holdout
- M1179 must preserve actor inputs
- M1179 must not convert failed surface rows

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
- do not continue artifact-only relocation expansion without a new branch decision

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1179-v4-public-base-stronger-wrong-history-construction-synthesis
