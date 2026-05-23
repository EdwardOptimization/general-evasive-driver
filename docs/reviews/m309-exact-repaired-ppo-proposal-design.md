# m309-exact-repaired-ppo-proposal-design Research Review

## Summary

- Generated at UTC: 20260523T050620Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m310_fresh_ppo_proposal_exact_repair_smoke
- Decision reason: M309 registers M310 PPO proposal config exact repair command and gate order without running PPO

## Hypothesis

After M307 promotion and M308 deterministic repair repeat, the next progress path is a fresh smoke-scale PPO proposal from M307 followed by exact repair projection and lexicographic exact gates.

## Lineage

- parent_checkpoint: runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m308-exact-repair-fresh-seed-repeat.json, docs/m308-exact-repair-fresh-seed-repeat.md
- parent_objective: design the next PPO-as-proposal smoke from M307 base followed by exact repair before replay gates
- derived_from: m308-exact-repair-fresh-seed-repeat
- blocked_by: m308-exact-repair-fresh-seed-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- specify the M310 PPO proposal config from M307 base
- specify the M310 exact repair command and acceptance order
- keep exact M297 and exact M270 no-regression before replay gates
- register the next runnable smoke milestone
- no PPO is run in M309

## Failure Criteria

- design promotes PPO raw directly
- design omits exact repair or exact no-regression gates
- design requires actor input contract changes
- PPO is run in M309

## Evidence Gates

- do not run PPO in M309
- preserve human-view actor input contract
- define PPO proposal config from M307 base
- define exact repair step after PPO raw proposal
- define exact M297/M270 gates before replay
- define first replay and full promotion escalation order

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not return to naked PPO promotion
- do not run replay for exact-regressing proposals
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m309-exact-repaired-ppo-proposal-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m310_fresh_ppo_proposal_exact_repair_smoke
- reason: M309 registers M310 PPO proposal config exact repair command and gate order without running PPO

## Next Blocker

m310-fresh-ppo-proposal-exact-repair-smoke
