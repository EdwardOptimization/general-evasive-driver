# m304-exact-lexicographic-post-ppo-repair-design Research Review

## Summary

- Generated at UTC: 20260523T043934Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_exact_repair_projection_implementation
- Decision reason: M304 selects exact full-corpus lexicographic post-PPO repair with M297 then M270 no-regression before replay and admits M305 implementation

## Hypothesis

A post-PPO exact full-corpus repair/projection step is needed because scalar sampled PPO auxiliary loss did not preserve exact M297 or M270 objectives.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt, runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m303-m302-preference-guard-failure-audit.json, docs/m303-m302-preference-guard-failure-audit.md
- parent_objective: design exact lexicographic post-PPO repair or projection after M302 sampled PPO guard failed
- derived_from: m303-m302-preference-guard-failure-audit
- blocked_by: m303-m302-preference-guard-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- specify exact full-batch M297 and M270 repair objective
- specify trust-region or anchor terms to avoid M183/M170 replay collapse
- define whether repair starts from M302 raw or M299 base
- register the next implementation or repair-probe milestone
- no PPO is run and actor inputs remain unchanged

## Failure Criteria

- design cannot preserve exact M297 and M270 simultaneously
- design requires privileged actor inputs
- PPO is run in M304

## Evidence Gates

- do not run PPO in M304
- preserve human-view actor input contract
- design full-batch exact M297 and exact M270 repair objective
- make exact objective no-regression lexicographic before replay gates
- define the next repair probe and acceptance criteria

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use sampled training loss as a promotion gate
- do not promote M302 raw or interpolation
- do not change actor inputs
- do not run another PPO smoke before exact repair design

## Failure Taxonomy

- none

## Scoreboard

- milestone: m304-exact-lexicographic-post-ppo-repair-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_exact_repair_projection_implementation
- reason: M304 selects exact full-corpus lexicographic post-PPO repair with M297 then M270 no-regression before replay and admits M305 implementation

## Next Blocker

m305-exact-post-ppo-repair-projection-implementation
