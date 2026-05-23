# m499-natural-belief-action-sensitive-selector-design Research Review

## Summary

- Generated at UTC: 20260523T235621Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m500_natural_action_sensitive_selector_implementation
- Decision reason: M499 designs a two-stage selector that screens first-action distance then short-horizon trajectory distance before another outcome gate

## Hypothesis

An action-sensitive selector can avoid M497's weak wrong-history trajectory signal by selecting natural matched-current rows where wrong-history changes the short-horizon closed-loop action trajectory before current-response correction dominates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m498_natural_belief_wrong_history_no_effect_audit/summary.json, runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv, runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m498-natural-belief-wrong-history-no-effect-audit.json
- parent_objective: action-sensitive natural wrong-history selector design
- derived_from: m498-natural-belief-wrong-history-no-effect-audit
- blocked_by: m498-natural-belief-wrong-history-no-effect-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define probe semantics for cheap action or short-horizon wrong-history scoring
- define selection metrics and diversity caps
- define outcome-gate admission thresholds
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design repeats target-z-only triage
- design requires privileged actor inputs
- design relies on hidden-hold as deployable proof
- training or checkpoint promotion is proposed

## Evidence Gates

- design an action-sensitive selector over the full M495 matched-current surface
- rank rows by wrong-history first-action and short-horizon trajectory distance before outcome gates
- preserve source diversity across seeds labels targets configs and offsets
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not repeat M496 target-z triage unchanged
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m499-natural-belief-action-sensitive-selector-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m500_natural_action_sensitive_selector_implementation
- reason: M499 designs a two-stage selector that screens first-action distance then short-horizon trajectory distance before another outcome gate

## Next Blocker

pending M499 natural belief action-sensitive selector design
