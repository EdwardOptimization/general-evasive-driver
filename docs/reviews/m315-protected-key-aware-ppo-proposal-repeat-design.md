# m315-protected-key-aware-ppo-proposal-repeat-design Research Review

## Summary

- Generated at UTC: 20260523T053406Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m316_protected_key_aware_ppo_proposal_smoke
- Decision reason: M315 registers M316 PPO proposal config exact repair protected-key alpha sweep and gate order without running PPO

## Hypothesis

After M314 promotion, the next repeat should generate a fresh PPO proposal from the new base and treat protected-key-bounded interpolation as a required acceptance layer, not an after-the-fact repair.

## Lineage

- parent_checkpoint: runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv
- parent_config: experiments/manifests/m314-full-public-gate-for-m313-a140.json, docs/m314-full-public-gate-for-m313-a140.md
- parent_objective: design the next PPO proposal repeat using M314 base with exact repair and protected-key-bounded acceptance
- derived_from: m314-full-public-gate-for-m313-a140
- blocked_by: m314-full-public-gate-for-m313-a140
- supersedes: None
- invalidates: None

## Success Criteria

- specify the next PPO proposal config from M314 base
- specify exact repair and protected-key-bounded interpolation commands
- register the next runnable smoke milestone
- no PPO is run in M315

## Failure Criteria

- design promotes PPO raw directly
- design omits exact repair or protected-key-bounded acceptance
- design requires actor input contract changes
- PPO is run in M315

## Evidence Gates

- do not run PPO in M315
- preserve human-view actor input contract
- define fresh PPO proposal from M314 base
- define exact repair step after PPO raw proposal
- define protected-key-bounded acceptance before replay
- define first replay and promotion escalation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not return to naked PPO promotion
- do not run replay for exact-regressing or protected-key-failing proposals
- do not change actor inputs
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m315-protected-key-aware-ppo-proposal-repeat-design
- type: infrastructure
- checkpoint: not_applicable_infrastructure_task
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m316_protected_key_aware_ppo_proposal_smoke
- reason: M315 registers M316 PPO proposal config exact repair protected-key alpha sweep and gate order without running PPO

## Next Blocker

m316-protected-key-aware-ppo-proposal-smoke
