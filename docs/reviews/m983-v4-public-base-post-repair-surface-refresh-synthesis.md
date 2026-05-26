# m983-v4-public-base-post-repair-surface-refresh-synthesis Research Review

## Summary

- Generated at UTC: 20260526T121008Z
- Type: gate
- Gate tier: process
- Promotion decision: pivot_to_extreme_scenario_family_generation
- Decision reason: M983 synthesizes M979-M982 and pivots from same-family seed mining to richer extreme scenario-family generation before any training

## Hypothesis

M979-M982 provide enough evidence to close the same-family post-repair surface-refresh branch and pivot to richer hidden-dynamics scenario-family generation before training.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m979-v4-public-base-post-repair-surface-refresh-design.md, docs/m980-v4-public-base-post-repair-surface-refresh-implementation.md, docs/m981-v4-public-base-post-repair-expanded-source-refresh.md, docs/m982-v4-public-base-post-repair-ood-pocket-expansion-audit.md
- parent_config: experiments/manifests/m979-v4-public-base-post-repair-surface-refresh-design.json, experiments/manifests/m980-v4-public-base-post-repair-surface-refresh-implementation.json, experiments/manifests/m981-v4-public-base-post-repair-expanded-source-refresh.json, experiments/manifests/m982-v4-public-base-post-repair-ood-pocket-expansion-audit.json
- parent_objective: synthesize the post-repair surface-refresh branch before extending it into new scenario families
- derived_from: m979-v4-public-base-post-repair-surface-refresh-design, m980-v4-public-base-post-repair-surface-refresh-implementation, m981-v4-public-base-post-repair-expanded-source-refresh, m982-v4-public-base-post-repair-ood-pocket-expansion-audit
- blocked_by: M980/M982 accepted rows remain isolated to one OOD left seed and two physical pairs, M981 expanded seed coverage finds zero accepted rows
- supersedes: None
- invalidates: continuing same-family seed mining as the main branch, training from the isolated M980/M982 rows, claiming source-diverse current-base proof-surface evidence from M980/M982

## Success Criteria

- synthesis artifact exists
- supported and falsified claims are explicit
- failure taxonomy is explicit
- public gate overfit risk is updated
- next branch decision is explicit
- no training or promotion occurs

## Failure Criteria

- synthesis artifact is missing
- route decision is missing
- thresholds are lowered retroactively
- training or PPO starts
- unsupported per-wheel failure claims are made under the single-track model

## Evidence Gates

- M983 must synthesize M979-M982 before opening a new branch
- M983 must not run PPO
- M983 must not promote
- M983 must not use private holdout
- M983 must preserve P0 actor-input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train or optimize
- do not lower thresholds retroactively
- do not treat the M980/M982 isolated pocket as source-diverse evidence
- do not claim unsupported per-wheel failure coverage under the current single-track dynamics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m983-v4-public-base-post-repair-surface-refresh-synthesis
- type: gate
- checkpoint: docs/m983-v4-public-base-post-repair-surface-refresh-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pivot_to_extreme_scenario_family_generation
- reason: M983 synthesizes M979-M982 and pivots from same-family seed mining to richer extreme scenario-family generation before any training

## Next Blocker

m984-v4-public-base-extreme-scenario-family-config-smoke
