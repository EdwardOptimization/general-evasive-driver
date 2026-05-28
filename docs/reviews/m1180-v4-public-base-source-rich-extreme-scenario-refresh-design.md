# m1180-v4-public-base-source-rich-extreme-scenario-refresh-design Research Review

## Summary

- Generated at UTC: 20260528T023426Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1180 may only design the source-rich extreme scenario refresh route. It cannot run mining, run replay, train actor weights, run PPO, promote, use private holdout, change actor inputs, or convert rows into a proof corpus.

## Hypothesis

A source-rich extreme scenario refresh design can address M1179's artifact-only limitations by generating current-base data with explicit obstacle geometry, fault/onset/warmup metadata, and separated fidelity classes.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1179-v4-public-base-stronger-wrong-history-construction-synthesis.md, docs/m824-v4-extreme-hidden-dynamics-data-route-design.md, docs/m826-v4-extreme-hidden-dynamics-data-route-audit.md, docs/m831-v4-low-margin-new-data-route-second-branch-synthesis.md, configs/cross_fault_hidden_condition_scenarios.json
- parent_config: experiments/manifests/m1179-v4-public-base-stronger-wrong-history-construction-synthesis.json
- parent_objective: design source-rich extreme scenario surface refresh for current public base
- derived_from: m1179-v4-public-base-stronger-wrong-history-construction-synthesis
- blocked_by: artifact-only wrong-history construction repeatedly returns to the same old active set and lacks source obstacle geometry
- supersedes: None
- invalidates: continuing M1161 artifact-only candidate rescoring, new PPO before source-rich proof-surface refresh, claiming wheel-level fault evidence from current single-track proxy faults

## Success Criteria

- design artifact exists
- source-rich schema is specified
- fault fidelity boundary is specified
- current-model supported axes and future-only axes are separated
- next route is explicit
- no mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- design conflates proxy faults with current-model evidence
- design lacks source obstacle geometry requirements
- next blocker is ambiguous
- mining, replay, actor training, PPO, promotion, private holdout, conversion, or actor-input change starts

## Evidence Gates

- M1180 may design source-rich extreme scenario refresh only
- M1180 must not run mining
- M1180 must not run replay
- M1180 must not train actor weights
- M1180 must not run PPO
- M1180 must not promote
- M1180 must not use private holdout
- M1180 must preserve actor inputs
- M1180 must not convert failed rows into a proof corpus

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
- do not convert failed rows
- do not mix current_model_fault, current_model_proxy, and future_only evidence claims

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1180-v4-public-base-source-rich-extreme-scenario-refresh-design
