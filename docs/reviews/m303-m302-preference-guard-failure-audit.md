# m303-m302-preference-guard-failure-audit Research Review

## Summary

- Generated at UTC: 20260523T012154Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_with_exact_lexicographic_post_ppo_projection
- Decision reason: M303 finds M302 exact M297 regression is broad across 17 of 17 rows and sampled train metric is not a full-corpus gate; next repair should be exact lexicographic post-PPO projection

## Hypothesis

M302 failed because the sampled training-time auxiliary loss was too weak or misaligned with the exact full-corpus M297/M270 gates, so the next repair should enforce exact objectives lexicographically rather than relying on a small PPO coefficient.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt, runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m302_rejected_preference_guarded_smoke.json, experiments/manifests/m302-rejected-preference-guarded-ppo-smoke.json, docs/m302-rejected-preference-guarded-ppo-smoke.md
- parent_objective: audit why M302 training-time rejected-history preference auxiliary loss did not protect exact M297 or exact M270
- derived_from: m302-rejected-preference-guarded-ppo-smoke
- blocked_by: m302-rejected-preference-guarded-ppo-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- explain why train metric improved or looked acceptable while exact M297 regressed
- identify whether M297 and M270 regressions are row-local or broad
- recommend a next repair path before another PPO smoke
- record negative result and next milestone

## Failure Criteria

- audit cannot distinguish coefficient weakness from metric artifact
- audit requires hidden actor inputs
- PPO is run in M303

## Evidence Gates

- do not run PPO in M303
- preserve human-view actor input contract
- compare train-time sampled preference metric with exact M297 after PPO
- inspect focused rows 6, 11, 15, and 16
- decide whether the next repair is coefficient scaling, lexicographic projection, or post-PPO exact repair

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun PPO before classifying M302 failure
- do not tune from private holdouts
- do not change actor inputs
- do not promote any M302 interpolation

## Failure Taxonomy

- metric_artifact
- objective_overfit

## Scoreboard

- milestone: m303-m302-preference-guard-failure-audit
- type: gate
- checkpoint: runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: repair_with_exact_lexicographic_post_ppo_projection
- reason: M303 finds M302 exact M297 regression is broad across 17 of 17 rows and sampled train metric is not a full-corpus gate; next repair should be exact lexicographic post-PPO projection

## Next Blocker

m304-exact-lexicographic-post-ppo-repair-design
