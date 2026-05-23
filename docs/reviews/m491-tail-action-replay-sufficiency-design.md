# m491-tail-action-replay-sufficiency-design Research Review

## Summary

- Generated at UTC: 20260523T231644Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m492_tail_action_replay_sufficiency_gate_implementation
- Decision reason: M491 defines observer-hidden action replay to test whether M490 hidden-hold events come from wrong physical actions or persistent wrong hidden state

## Hypothesis

M490 hidden-hold events may be caused either by the wrong physical action sequence or by the artificially persistent wrong hidden state; a K-step action-replay diagnostic can separate these mechanisms.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m490_tail_action_sequence_amplification_summary/combined_summary.json, runs/m490_tail_action_sequence_amplification_summary/combined_tail_amplification_outcomes.csv
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m490-tail-action-sequence-amplification-gate-implementation.json
- parent_objective: tail action replay sufficiency diagnostic design
- derived_from: m490-tail-action-sequence-amplification-gate-implementation
- blocked_by: m490-tail-action-sequence-amplification-gate-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- define action-replay rollout semantics and hidden resume semantics
- define comparison against wrong_tail_once and wrong_tail_hidden_hold_K
- define event/proof/source-diversity thresholds for implementation
- classify action replay rows as diagnostic only
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design cannot separate action-sequence sufficiency from persistent hidden-state forcing
- design treats forced action replay as deployable proof
- design omits hidden-hold and natural wrong-tail controls
- actor contract changes
- training or checkpoint promotion is proposed before the diagnostic

## Evidence Gates

- design a diagnostic that replays K-step wrong-tail physical action sequences without holding wrong hidden afterward
- separate wrong action sufficiency from persistent wrong-hidden sufficiency
- define observer-hidden resume semantics before implementation
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not claim action replay as deployable self-ID proof
- do not add privileged actor inputs
- do not skip natural wrong_tail_once and hidden-hold controls

## Failure Taxonomy

- none

## Scoreboard

- milestone: m491-tail-action-replay-sufficiency-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m492_tail_action_replay_sufficiency_gate_implementation
- reason: M491 defines observer-hidden action replay to test whether M490 hidden-hold events come from wrong physical actions or persistent wrong hidden state

## Next Blocker

m492-tail-action-replay-sufficiency-gate-implementation
