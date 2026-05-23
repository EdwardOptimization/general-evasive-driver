# m481-critical-window-history-necessity-design Research Review

## Summary

- Generated at UTC: 20260523T222611Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m482_tail_aligned_wrong_history_gate_implementation
- Decision reason: M481 selects tail-aligned one-shot wrong-history swaps at left_step+S and right_step+S before any new critical-window config or training

## Hypothesis

Because late one-shot wrong history creates only margin-only source-narrow degradation while clamped hold variants create event rows, the next useful test is a critical-window task or gate that reduces recovery time after a natural wrong-history perturbation.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m480_late_once_wrong_history_intervention_gate/summary.json, runs/m480_late_once_wrong_history_intervention_gate/late_once_summary.json, runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m480-late-once-wrong-history-implementation.json
- parent_objective: critical-window history-necessity task or gate design
- derived_from: m480-late-once-wrong-history-implementation
- blocked_by: m480-late-once-wrong-history-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- document why M480 did not pass the natural-late proof gate
- define a critical-window task or gate family that shortens the recovery horizon after wrong-history injection
- define diagnostic variants and thresholds before implementation
- preserve the P0 human-view actor-input contract
- pre-register the next implementation or run manifest
- no checkpoint is promoted

## Failure Criteria

- design treats clamped hidden-state evidence as deployable proof
- design proposes training before a critical-window diagnostic is specified
- design changes actor inputs
- design loosens source-diversity or event-proof thresholds to fit M480

## Evidence Gates

- treat M480 late-one-shot rows as margin-only source-narrow timing evidence
- do not count clamped wrong_hold rows as deployable proof
- design a shorter or more critical emergency-window task/gate
- define how recovery time after wrong-history injection will be reduced
- define pass/fail criteria before running any new diagnostic or training
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not relax source-diversity gates
- do not claim margin-only source-narrow late-once rows as deployable proof
- do not count clamped hidden-state rows as natural wrong-history evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m481-critical-window-history-necessity-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m482_tail_aligned_wrong_history_gate_implementation
- reason: M481 selects tail-aligned one-shot wrong-history swaps at left_step+S and right_step+S before any new critical-window config or training

## Next Blocker

m482-tail-aligned-wrong-history-gate-implementation
