# m980-v4-public-base-post-repair-surface-refresh-implementation Research Review

## Summary

- Generated at UTC: 20260526T115745Z
- Type: gate
- Gate tier: proof
- Promotion decision: post_repair_surface_refresh_source_narrow_route_to_expanded_source_refresh
- Decision reason: M980 finds 30 accepted wrong-history rows but only one left seed and two physical pairs so it is a source-narrow positive not a corpus pass

## Hypothesis

The M974 public-gate base will expose fresh normal-success wrong-history boundary rows under new public seed ranges, reducing public-row overfit risk before another PPO continuation.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m979-v4-public-base-post-repair-surface-refresh-design.md, docs/m978-v4-public-base-post-exact-repair-promotion-synthesis.md
- parent_config: experiments/manifests/m979-v4-public-base-post-repair-surface-refresh-design.json
- parent_objective: run no-PPO current-base wrong-history/preference surface refresh before another guarded PPO continuation
- derived_from: m979-v4-public-base-post-repair-surface-refresh-design, m978-v4-public-base-post-exact-repair-promotion-synthesis
- blocked_by: M978 synthesis requires fresh current-base proof/preference surfaces before another PPO continuation
- supersedes: None
- invalidates: starting new guarded PPO from M974 public base before surface refresh

## Success Criteria

- summary artifact exists
- near_boundary_preferred_snapshots is reported
- accepted_rows and diversity metrics are reported
- normal_success_boundary_corpus.npz is written
- actor parameters are unchanged
- PPO and promotion are not used
- route decision is explicit

## Failure Criteria

- miner crashes
- actor parameters change
- PPO or optimizer starts
- fresh seed ranges are not used
- thresholds are changed after seeing results
- route decision is missing

## Evidence Gates

- M980 must not run PPO
- M980 must not promote
- M980 must not use private holdout
- M980 must preserve P0 actor-input contract
- M980 must use fresh seed ranges rather than old M667 ranges
- M980 must report accepted row, source diversity, split, and target summaries

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change actor inputs
- do not train or optimize
- do not lower thresholds after seeing results
- do not use old public proof rows as fresh evidence
- do not promote from surface refresh

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m980-v4-public-base-post-repair-surface-refresh-implementation
- type: gate
- checkpoint: runs/m980_v4_public_base_post_repair_surface_refresh/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_repair_surface_refresh_source_narrow_route_to_expanded_source_refresh
- reason: M980 finds 30 accepted wrong-history rows but only one left seed and two physical pairs so it is a source-narrow positive not a corpus pass

## Next Blocker

m981-v4-public-base-post-repair-expanded-source-refresh
