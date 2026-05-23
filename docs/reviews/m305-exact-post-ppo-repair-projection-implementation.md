# m305-exact-post-ppo-repair-projection-implementation Research Review

## Summary

- Generated at UTC: 20260523T044726Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m306_exact_repair_probe
- Decision reason: M305 implements exact_post_ppo_repair with deterministic full-batch M297/M270 summaries and a real-corpus steps0 smoke; no PPO and no promotion

## Hypothesis

A deterministic exact post-PPO repair or projection tool can generate candidates and exact M297/M270 summaries so M306 can test whether the rejected M302 PPO proposal is recoverable without relying on sampled auxiliary metrics.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt, runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m304-exact-lexicographic-post-ppo-repair-design.json, docs/m304-exact-lexicographic-post-ppo-repair-design.md
- parent_objective: implement deterministic exact full-corpus repair or projection after M302 exact objective regression
- derived_from: m304-exact-lexicographic-post-ppo-repair-design
- blocked_by: m302-rejected-preference-guarded-ppo-smoke, m303-m302-preference-guard-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- add a repair or projection CLI that can load M299 base M302 raw M297 corpus and M270 corpus
- compute full-batch exact M297 and M270 losses before and after candidate generation
- include trust-region or anchor terms to M299 base
- write summary and CSV artifacts suitable for M306 exact gating
- run focused tests and research validation
- no PPO is run and no checkpoint is promoted

## Failure Criteria

- implementation only exposes sampled losses
- implementation cannot compare candidates against M299 exact baselines
- implementation requires privileged actor inputs
- M305 runs PPO or promotes a checkpoint

## Evidence Gates

- do not run PPO in M305
- preserve human-view actor input contract
- implement deterministic full-batch M297 loss for repair candidates
- implement deterministic full-batch M270 loss for repair candidates
- report lexicographic exact no-regression before replay gates
- write focused tests for exact repair loss and config validation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use sampled training loss as a promotion gate
- do not promote any repaired checkpoint in M305
- do not change actor inputs
- do not run closed-loop replay before exact objective summaries exist

## Failure Taxonomy

- none

## Scoreboard

- milestone: m305-exact-post-ppo-repair-projection-implementation
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m306_exact_repair_probe
- reason: M305 implements exact_post_ppo_repair with deterministic full-batch M297/M270 summaries and a real-corpus steps0 smoke; no PPO and no promotion

## Next Blocker

m306-repair-m302-raw-exact-projection-probe
