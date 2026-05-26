# m981-v4-public-base-post-repair-expanded-source-refresh Research Review

## Summary

- Generated at UTC: 20260526T120358Z
- Type: gate
- Gate tier: proof
- Promotion decision: post_repair_expanded_source_refresh_empty_route_to_targeted_ood_pocket_audit
- Decision reason: M981 expands fresh/OOD seeds and finds zero accepted rows despite 29959 action-threshold rows and candidate max margin gap 0.00449

## Hypothesis

Expanding fresh public seed coverage around the M974 public base while keeping M980 thresholds fixed will turn the M980 source-narrow accepted pocket into a source-diverse surface or prove that it is a narrow OOD artifact.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m980-v4-public-base-post-repair-surface-refresh-implementation.md, runs/m980_v4_public_base_post_repair_surface_refresh/summary.json, runs/m980_v4_public_base_post_repair_surface_refresh/candidate_scores.csv, runs/m980_v4_public_base_post_repair_surface_refresh/normal_success_boundary_rows.csv
- parent_config: experiments/manifests/m980-v4-public-base-post-repair-surface-refresh-implementation.json
- parent_objective: expand source coverage after M980 found a narrow accepted wrong-history pocket
- derived_from: m980-v4-public-base-post-repair-surface-refresh-implementation, m979-v4-public-base-post-repair-surface-refresh-design
- blocked_by: M980 accepted rows are source-narrow: 30 rows from one left seed and two physical pairs
- supersedes: None
- invalidates: training from M980 source-narrow corpus, lowering thresholds to force M980 corpus pass

## Success Criteria

- summary artifact exists
- accepted_rows and source diversity are reported
- thresholds match M980
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

- M981 must not run PPO
- M981 must not promote
- M981 must not use private holdout
- M981 must preserve P0 actor-input contract
- M981 must keep M980 thresholds unchanged
- M981 must expand seed/source coverage rather than lowering thresholds

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

- milestone: m981-v4-public-base-post-repair-expanded-source-refresh
- type: gate
- checkpoint: runs/m981_v4_public_base_post_repair_expanded_source_refresh/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_repair_expanded_source_refresh_empty_route_to_targeted_ood_pocket_audit
- reason: M981 expands fresh/OOD seeds and finds zero accepted rows despite 29959 action-threshold rows and candidate max margin gap 0.00449

## Next Blocker

m982-v4-public-base-post-repair-ood-pocket-expansion-audit
