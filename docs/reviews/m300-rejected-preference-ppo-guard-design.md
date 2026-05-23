# m300-rejected-preference-ppo-guard-design Research Review

## Summary

- Generated at UTC: 20260523T010814Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: implement_rejected_preference_ppo_aux_loss
- Decision reason: M300 designs a train-time rejected-history preference PPO auxiliary loss plus exact M297 and exact M270 no-regression gates before another smoke PPO

## Hypothesis

The next PPO attempt should not merely restart from M299; it needs an explicit rejected-history preference guard so PPO cannot again make M267/M264 wrong-history rollouts safe.

## Lineage

- parent_checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m297-current-family-rejected-preference-objective-implementation.json, experiments/manifests/m298-rejected-preference-objective-only-probe.json, experiments/manifests/m299-full-public-gate-for-m298-a020.json
- parent_objective: design a PPO guard path that uses the rejected-history preference signal before another smoke PPO
- derived_from: m299-full-public-gate-for-m298-a020
- blocked_by: m299-full-public-gate-for-m298-a020
- supersedes: None
- invalidates: None

## Success Criteria

- write a concrete PPO guard design using the M297 preference corpus and exact M270 retention
- identify required train_ppo or post-PPO projection changes
- define first-gate and full-gate criteria for the next smoke PPO
- register the next implementation or smoke milestone
- no PPO is run and actor inputs remain unchanged

## Failure Criteria

- design cannot protect both exact M270 and M267/M264 wrong-history rows
- design would require privileged actor inputs
- PPO is run in M300

## Evidence Gates

- do not run PPO in M300
- preserve human-view actor input contract
- specify how M297 preference loss gates or regularizes PPO
- specify exact M270 and M297 no-regression checks before replay gates
- define the next smoke PPO manifest only after the guard design is explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run another PPO smoke before designing the rejected-preference guard
- do not promote based on exact objectives alone
- do not change actor inputs
- do not tune against private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m300-rejected-preference-ppo-guard-design
- type: infrastructure
- checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: implement_rejected_preference_ppo_aux_loss
- reason: M300 designs a train-time rejected-history preference PPO auxiliary loss plus exact M297 and exact M270 no-regression gates before another smoke PPO

## Next Blocker

m301-rejected-preference-ppo-aux-loss-implementation
