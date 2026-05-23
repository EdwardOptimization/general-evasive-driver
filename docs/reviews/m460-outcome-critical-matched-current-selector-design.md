# m460-outcome-critical-matched-current-selector-design Research Review

## Summary

- Generated at UTC: 20260523T203949Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m461_outcome_critical_selector_implementation
- Decision reason: M460 designs an outcome-critical selector that preserves matched-current similarity and rejects action-only rows without continuation degradation

## Hypothesis

M459 found source-diverse matched-current response/action ambiguity but weak continuation outcomes, so the next useful step is to make continuation margin and success degradation first-class selection criteria.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m459_late_reveal_matched_current_seed9600/matched_pairs.csv, runs/m459_late_reveal_matched_history_action_gate/variant_summary.csv, runs/m459_late_reveal_matched_history_outcome_gate/outcome_summary.csv, runs/m459_late_reveal_matched_current_analysis/summary.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m459-late-reveal-matched-current-mining.json
- parent_objective: outcome-critical matched-current selector design
- derived_from: m459-late-reveal-matched-current-mining
- blocked_by: m459-late-reveal-matched-current-mining
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies outcome-critical filtering metrics
- design keeps matched-current similarity constraints
- design includes source-diverse compact corpus rules
- next implementation task is preregistered
- no checkpoint is promoted

## Failure Criteria

- design selects pairs only by future response target z-delta
- design ignores outcome gate negative result
- design jumps directly to training
- actor contract changes

## Evidence Gates

- design an outcome-critical selector for matched-current pairs
- require continuation margin or success degradation under at least one history intervention
- preserve matched-current response/context similarity and source-diverse caps
- define implementation and pass/fail thresholds
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not treat M459 action-only signal as closed-loop proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m460-outcome-critical-matched-current-selector-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m461_outcome_critical_selector_implementation
- reason: M460 designs an outcome-critical selector that preserves matched-current similarity and rejects action-only rows without continuation degradation

## Next Blocker

m461-outcome-critical-matched-current-selector-implementation
