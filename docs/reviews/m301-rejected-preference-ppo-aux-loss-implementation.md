# m301-rejected-preference-ppo-aux-loss-implementation Research Review

## Summary

- Generated at UTC: 20260523T011400Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m302_rejected_preference_guarded_ppo_smoke
- Decision reason: M301 adds train_ppo rejected-history preference aux-loss config validation loader metrics tests and registers M302 smoke config without running PPO

## Hypothesis

A small, explicit rejected-history preference auxiliary loss can be added to PPO training so the next smoke run penalizes the exact M267/M264 washout mode that M291 and M294 exposed.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m300-rejected-preference-ppo-guard-design.json, docs/m300-rejected-preference-ppo-guard-design.md
- parent_objective: implement the rejected-history preference auxiliary PPO guard designed in M300
- derived_from: m300-rejected-preference-ppo-guard-design
- blocked_by: m300-rejected-preference-ppo-guard-design
- supersedes: None
- invalidates: None

## Success Criteria

- train_ppo accepts rejected-history preference aux-loss config fields
- the loss is applied only when recurrent sequence training is active
- metrics report rejected-history preference loss during updates
- tests cover validation and a short smoke path without changing actor inputs
- M302 smoke PPO manifest is registered

## Failure Criteria

- implementation requires privileged actor inputs
- loss cannot be wired without destabilizing existing PPO tests
- PPO is run before implementation validation

## Evidence Gates

- do not run PPO in M301
- preserve human-view actor input contract
- add train_ppo config fields and validation for rejected-history preference auxiliary loss
- load M297 preference snippets using existing intervention_objectives helpers
- record rejected-preference loss metrics during PPO updates
- add focused tests for config validation and loss wiring

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M301
- do not change actor observation inputs
- do not load hidden vehicle parameters as actor inputs
- do not weaken existing outcome or anchor loss validation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m301-rejected-preference-ppo-aux-loss-implementation
- type: infrastructure
- checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m302_rejected_preference_guarded_ppo_smoke
- reason: M301 adds train_ppo rejected-history preference aux-loss config validation loader metrics tests and registers M302 smoke config without running PPO

## Next Blocker

m302-rejected-preference-guarded-ppo-smoke
