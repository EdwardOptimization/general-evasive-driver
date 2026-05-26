# m982-v4-public-base-post-repair-ood-pocket-expansion-audit Research Review

## Summary

- Generated at UTC: 20260526T121008Z
- Type: gate
- Gate tier: proof
- Promotion decision: post_repair_ood_pocket_isolated_route_to_synthesis
- Decision reason: M982 increases candidate coverage on the M980 OOD range but still finds only the same 30 rows from one left seed and two physical pairs

## Hypothesis

The M980 accepted pocket may be source-narrow because the original OOD pass capped candidate-pair coverage; increasing candidate coverage on the same OOD seed range will either expose more source-diverse rows or prove the pocket is isolated.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m980-v4-public-base-post-repair-surface-refresh-implementation.md, docs/m981-v4-public-base-post-repair-expanded-source-refresh.md, runs/m980_v4_public_base_post_repair_surface_refresh/summary.json, runs/m981_v4_public_base_post_repair_expanded_source_refresh/summary.json
- parent_config: experiments/manifests/m980-v4-public-base-post-repair-surface-refresh-implementation.json, experiments/manifests/m981-v4-public-base-post-repair-expanded-source-refresh.json
- parent_objective: audit whether the M980 OOD accepted pocket is a candidate-limit artifact or an isolated source pocket
- derived_from: m980-v4-public-base-post-repair-surface-refresh-implementation, m981-v4-public-base-post-repair-expanded-source-refresh
- blocked_by: M980 accepted rows are source-narrow, M981 expanded fresh/OOD seed coverage finds zero accepted rows
- supersedes: None
- invalidates: training from M980 source-narrow rows, claiming M980 as a source-diverse proof surface, lowering thresholds after M981

## Success Criteria

- summary artifact exists
- thresholds match M980/M981
- accepted_rows and source diversity are reported
- actor parameters are unchanged
- PPO and promotion are not used
- route decision is explicit

## Failure Criteria

- miner crashes
- thresholds are lowered
- actor parameters change
- PPO or optimizer starts
- route decision is missing

## Evidence Gates

- M982 must not run PPO
- M982 must not promote
- M982 must not use private holdout
- M982 must preserve P0 actor-input contract
- M982 must keep M980/M981 acceptance thresholds unchanged
- M982 must expand candidate coverage around the M980 OOD seed range rather than lowering thresholds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change actor inputs
- do not train or optimize
- do not lower min action or margin thresholds
- do not train from M980 source-narrow rows
- do not use private holdout
- do not promote

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m982-v4-public-base-post-repair-ood-pocket-expansion-audit
- type: gate
- checkpoint: runs/m982_v4_public_base_post_repair_ood_pocket_expansion_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_repair_ood_pocket_isolated_route_to_synthesis
- reason: M982 increases candidate coverage on the M980 OOD range but still finds only the same 30 rows from one left seed and two physical pairs

## Next Blocker

m983-v4-public-base-post-repair-surface-refresh-synthesis
