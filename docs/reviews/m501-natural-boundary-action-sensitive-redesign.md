# m501-natural-boundary-action-sensitive-redesign Research Review

## Summary

- Generated at UTC: 20260524T001338Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m502_natural_boundary_pressure_config_implementation
- Decision reason: M501 rejects direct selector repair because strict boundary rows have too few action-sensitive trajectory cases and admits boundary-pressure config validation before further mining

## Hypothesis

M500 failed because the selector optimized action trajectory distance without enough terminal boundary sensitivity; the next proof path should require both one-shot wrong-history action sensitivity and near-boundary or low-slack outcome sensitivity.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m500_natural_action_sensitive_selector/summary.json, runs/m500_natural_action_sensitive_selector/action_sensitive_candidates.csv, runs/m500_natural_action_sensitive_selector/targeted_pairs.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m500-natural-action-sensitive-selector-implementation.json
- parent_objective: natural boundary action-sensitive redesign
- derived_from: m500-natural-action-sensitive-selector-implementation
- blocked_by: m500-natural-action-sensitive-selector-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- summarize M500 high-margin and source-balance failure modes
- define a boundary-action-sensitive selection or task-redesign path
- include explicit admission thresholds for near-boundary rows and source diversity
- state whether the next step should be selector repair or config redesign
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- redesign repeats M496 target-z triage or M500 action-only triage unchanged
- redesign admits outcome gates on high-margin rows
- redesign relies on hidden-hold or persistent wrong-history as deployable proof
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- audit why M500 action-sensitive rows are high-margin and warmup-dominated
- design a next selector or task change that jointly requires wrong-history action sensitivity and terminal boundary sensitivity
- pre-register admission criteria before any outcome gate
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not relax M500 thresholds after seeing the result just to force an outcome gate
- do not count high-margin action differences as self-ID outcome proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m501-natural-boundary-action-sensitive-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m502_natural_boundary_pressure_config_implementation
- reason: M501 rejects direct selector repair because strict boundary rows have too few action-sensitive trajectory cases and admits boundary-pressure config validation before further mining

## Next Blocker

M502 should implement and sampling-validate boundary-pressured natural belief configs before any mining or outcome gate.
