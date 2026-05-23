# m493-natural-belief-decision-window-redesign Research Review

## Summary

- Generated at UTC: 20260523T232716Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m494_natural_belief_decision_config_implementation
- Decision reason: M493 closes the artificial tail-forcing branch and redirects to natural short-reveal and warm-up capability-evidence decision-window configs

## Hypothesis

The M486-M492 surface is useful for mechanism diagnosis but not deployable self-ID proof; the next path should create natural matched-current decision windows where command-response belief matters before current observations can correct wrong hidden state.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m492_tail_action_replay_sufficiency_summary/combined_summary.json
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m492-tail-action-replay-sufficiency-gate-implementation.json
- parent_objective: natural belief decision-window task redesign
- derived_from: m492-tail-action-replay-sufficiency-gate-implementation
- blocked_by: m492-tail-action-replay-sufficiency-gate-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- summarize why the tail-forcing branch is closed
- define a new task/pair-selection path with warm-up belief formation and short decision window
- define reset/zero-current/wrong-history gates and source-diversity thresholds
- define sampling stress before proof mining
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design continues artificial hidden or action forcing without a natural proof path
- design requires privileged actor inputs
- design proposes training before sampling and gate validation
- design cannot separate belief timing from task difficulty

## Evidence Gates

- close the M486-M492 artificial tail-forcing branch without promoting proof
- design a natural decision-window task where history-formed belief affects action before current-response correction dominates
- define sampling and smoke-validation criteria before implementation
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not count hidden-hold or action-replay rows as deployable proof
- do not keep adding artificial forcing on the same M486 surface without a new task rationale

## Failure Taxonomy

- none

## Scoreboard

- milestone: m493-natural-belief-decision-window-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m494_natural_belief_decision_config_implementation
- reason: M493 closes the artificial tail-forcing branch and redirects to natural short-reveal and warm-up capability-evidence decision-window configs

## Next Blocker

m494-natural-belief-decision-config-implementation
