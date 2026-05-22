# m270-source-balanced-multi-surface-anchor-corpus Research Review

## Summary

- Generated at UTC: 20260522T173724Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_multi_surface_guarded_actor_update
- Decision reason: M270 builds a 99-row 7-source balanced corpus covering M183 M193 M212 M223 M267 and protected-key snippets with loader validation

## Hypothesis

A source-balanced combined snippet corpus covering old M183/M193, recent M212/M223/M267, and the protected-key diagnostic can provide the retention substrate that M268 lacked.

## Lineage

- parent_checkpoint: runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
- parent_dataset: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.npz, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
- parent_config: experiments/manifests/m269-m268-old-surface-proof-washout-audit.json, docs/m269-m268-old-surface-proof-washout-audit.md
- parent_objective: source-balanced old+current+protected-key snippet anchor corpus for actor-update retention
- derived_from: m269-m268-old-surface-proof-washout-audit
- blocked_by: m269-m268-old-surface-proof-washout-audit
- supersedes: None
- invalidates: None

## Success Criteria

- build one validated combined NPZ compatible with outcome_intervention_optimize
- retain rows from every required source surface
- record per-source row counts and weights
- validate observation hidden action and weight shapes
- validate all weights are finite and positive
- do not run actor update or PPO

## Failure Criteria

- combined corpus omits any required source surface
- source weights are aggregate-dominated by one surface
- loader validation fails
- M270 runs actor update, PPO, or changes actor inputs

## Evidence Gates

- combined corpus shape validation
- source-balanced row-count and weight validation
- old M183/M193 rows retained
- recent M212/M223/M267 rows retained
- protected key 9944 diagnostic retained
- loader validation for outcome_intervention_optimize

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M270
- do not run an actor update in M270
- do not drop old M183/M193 rows
- do not change actor inputs
- do not hide source imbalance behind aggregate row counts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m270-source-balanced-multi-surface-anchor-corpus
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_multi_surface_guarded_actor_update
- reason: M270 builds a 99-row 7-source balanced corpus covering M183 M193 M212 M223 M267 and protected-key snippets with loader validation

## Next Blocker

m271-m270-multi-surface-guarded-actor-update
