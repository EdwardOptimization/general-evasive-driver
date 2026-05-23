# m298-rejected-preference-objective-only-probe Research Review

## Summary

- Generated at UTC: 20260523T010040Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: admit_full_public_gate_for_m298pref_a020
- Decision reason: M298 raw preference update improves M297 and exact M270 but collapses replay; alpha 0.02 improves M297 by 0.002190 and exact M270 by 0.001332 while passing M183/M170 and M267/M264

## Hypothesis

The M297 rejected-history preference loss has a useful no-PPO update direction that can improve the proof-washout objective while retaining exact M270 and replay surfaces.

## Lineage

- parent_checkpoint: runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.csv, runs/m297_current_family_rejected_preference_objective/policy_summary.csv, runs/m297_current_family_rejected_preference_objective/focused_row_losses.csv
- parent_config: experiments/manifests/m297-current-family-rejected-preference-objective-implementation.json, docs/m297-current-family-rejected-preference-objective-implementation.md
- parent_objective: probe whether the M297 rejected-history preference loss has a useful no-PPO update direction
- derived_from: m297-current-family-rejected-preference-objective-implementation
- blocked_by: m297-current-family-rejected-preference-objective-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- objective-only update or projection improves exact M297 preference loss versus M290
- exact M270 does not regress versus M290
- M183/M170 and M267/M264 replay gates pass if reached
- no PPO or actor-input change occurs
- results are documented with artifacts and failure taxonomy

## Failure Criteria

- preference loss improves only by breaking exact M270
- preference loss improves but M183/M170 or M267/M264 replay gates fail
- no usable non-PPO update direction is found
- PPO is run

## Evidence Gates

- do not run PPO
- preserve human-view actor input contract
- run a small objective-only update or interpolation/projection probe from M290 using the M297 preference loss
- evaluate exact M297 preference loss and exact M270 before any replay promotion
- run M183/M170 and M267/M264 replay gates only if exact objectives are non-regressing

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M298
- do not promote based on M297 loss alone
- do not change actor inputs
- do not use hidden vehicle parameters as actor inputs
- do not skip exact M270 no-regression before replay gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m298-rejected-preference-objective-only-probe
- type: objective_sanity
- checkpoint: runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_full_public_gate_for_m298pref_a020
- reason: M298 raw preference update improves M297 and exact M270 but collapses replay; alpha 0.02 improves M297 by 0.002190 and exact M270 by 0.001332 while passing M183/M170 and M267/M264

## Next Blocker

m299-full-public-gate-for-m298-a020
