# m524-multisurface-history-value-ablation-runner Research Review

## Summary

- Generated at UTC: 20260524T022842Z
- Type: gate
- Gate tier: proof
- Promotion decision: event_history_value_signal_admit_m525_history_value_event_audit_design
- Decision reason: M524 finds projected surface remains margin-only but natural M497/M487 surfaces have 480 L0 candidates and 18 obstacle-completion event rows across 12 seeds

## Hypothesis

A configurable multisurface history-value runner can reveal whether L3-vs-L0 diagnostic history value remains margin-only/source-narrow or becomes stronger on natural recent outcome surfaces.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m522_history_value_ablation_runner/summary.json, runs/m520_valid_offset_projection_outcome_gate/projected_outcomes.csv, runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv, runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv
- parent_config: experiments/manifests/m523-multisurface-history-value-ablation-design.json
- parent_objective: multisurface history-value ablation runner
- derived_from: m523-multisurface-history-value-ablation-design
- blocked_by: m523-multisurface-history-value-ablation-design
- supersedes: None
- invalidates: None

## Success Criteria

- runner supports configurable level variants
- runner evaluates at least two surfaces
- combined summary preserves surface provenance
- invalid mappings are reported explicitly
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- runner remains hard-coded to projected variants
- runner silently drops incompatible surfaces
- runner changes actor inputs
- runner trains or promotes a checkpoint
- summary omits surface provenance

## Evidence Gates

- support configurable L3/L0 variant mappings
- run history-value diagnostics on at least M520 projected and one natural surface
- write per-surface and combined summaries
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not hide invalid variant mappings
- do not merge projected and natural claims without provenance

## Failure Taxonomy

- none

## Scoreboard

- milestone: m524-multisurface-history-value-ablation-runner
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: event_history_value_signal_admit_m525_history_value_event_audit_design
- reason: M524 finds projected surface remains margin-only but natural M497/M487 surfaces have 480 L0 candidates and 18 obstacle-completion event rows across 12 seeds

## Next Blocker

M525 should audit the natural event rows before stronger history-value claims or matched baseline training.
