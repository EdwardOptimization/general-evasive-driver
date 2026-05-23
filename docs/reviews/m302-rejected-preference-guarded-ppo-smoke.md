# m302-rejected-preference-guarded-ppo-smoke Research Review

## Summary

- Generated at UTC: 20260523T011852Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_m302_exact_objective_regression
- Decision reason: M302 raw PPO regresses exact M297 by 0.000700 and exact M270 by 0.000443; every nonzero interpolation also regresses both so replay gates were not reached

## Hypothesis

Adding the M297 rejected-history preference auxiliary loss to smoke PPO from M299 will reduce M267/M264 wrong-history washout without regressing exact M270 or public replay surfaces.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: configs/ppo_m302_rejected_preference_guarded_smoke.json, experiments/manifests/m301-rejected-preference-ppo-aux-loss-implementation.json, docs/m301-rejected-preference-ppo-aux-loss-implementation.md
- parent_objective: run one smoke-scale PPO continuation from M299 with M297 rejected-history preference auxiliary loss
- derived_from: m301-rejected-preference-ppo-aux-loss-implementation
- blocked_by: m301-rejected-preference-ppo-aux-loss-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- raw PPO or a non-micro interpolation improves or retains exact M297 and exact M270 versus M299
- M183/M170 and M267/M264 first replay gates pass
- full public replay protected-key and behavior gates pass before promotion
- actor input contract remains unchanged

## Failure Criteria

- exact M297 or exact M270 regresses for every nonzero candidate
- M183/M170 loses any normal-success row
- M267/M264 success drops fall below 17 / 17
- safe interpolation collapses to a micro-alpha
- PPO is lengthened beyond smoke scale

## Evidence Gates

- smoke-scale PPO only: 1024 steps
- preserve human-view actor input contract
- exact M297 rejected-preference no-regression before replay promotion
- exact M270 no-regression before replay promotion
- M183/M170 first replay gate
- M267/M264 first replay gate
- full replay protected-key and behavior gates only after first gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run medium or long PPO in M302
- do not promote if exact M297 or exact M270 regresses
- do not loosen M183/M170 or M267/M264 replay gates
- do not change actor inputs

## Failure Taxonomy

- objective_overfit

## Scoreboard

- milestone: m302-rejected-preference-guarded-ppo-smoke
- type: driver_candidate
- checkpoint: runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m302_exact_objective_regression
- reason: M302 raw PPO regresses exact M297 by 0.000700 and exact M270 by 0.000443; every nonzero interpolation also regresses both so replay gates were not reached

## Next Blocker

m303-m302-preference-guard-failure-audit
