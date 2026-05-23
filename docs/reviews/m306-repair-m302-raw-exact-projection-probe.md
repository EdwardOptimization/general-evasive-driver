# m306-repair-m302-raw-exact-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T045220Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: admit_m307_full_public_gate_for_m306_raw_s40
- Decision reason: M306 raw-start exact repair improves M297/M270 and passes M183/M170 plus M267/M264 first replay gates but is not promoted before full public gate

## Hypothesis

The rejected M302 raw PPO proposal may contain useful movement that can be recovered by exact full-corpus repair while preserving M297 and M270 before replay gates.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt, runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m305-exact-post-ppo-repair-projection-implementation.json, docs/m305-exact-post-ppo-repair-projection-implementation.md
- parent_objective: test whether M302 raw PPO proposal can be repaired by exact full-corpus projection without exact M297 or exact M270 regression
- derived_from: m305-exact-post-ppo-repair-projection-implementation
- blocked_by: m302-rejected-preference-guarded-ppo-smoke, m303-m302-preference-guard-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- produce at least one repaired candidate from M302 raw or M299 base
- candidate exact M297 loss is no worse than M299 plus tolerance
- candidate exact M270 loss is no worse than M299 plus tolerance
- if exact gates pass then M183/M170 and M267/M264 first replay gates are evaluated
- document whether M302 raw has recoverable value or collapses back to M299

## Failure Criteria

- all repaired candidates regress exact M297 or exact M270
- candidate exact gates pass but first replay gates fail
- repair produces only negligible base-equivalent movement
- actor input contract is changed

## Evidence Gates

- preserve human-view actor input contract
- run exact_post_ppo_repair from M302 raw and M299 base starts
- exact M297 candidate loss must not regress versus M299
- exact M270 candidate loss must not regress versus M299
- only if exact gates pass run M183/M170 first replay
- only if exact gates pass run M267/M264 first replay
- do not promote unless full public gate stack later passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not accept weighted repair loss without exact M297/M270 no-regression
- do not run replay gates for exact-regressing candidates
- do not use sampled training metrics as proof
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m306-repair-m302-raw-exact-projection-probe
- type: driver_candidate
- checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m307_full_public_gate_for_m306_raw_s40
- reason: M306 raw-start exact repair improves M297/M270 and passes M183/M170 plus M267/M264 first replay gates but is not promoted before full public gate

## Next Blocker

m307-full-public-gate-for-m306-raw-s40
