# m523-multisurface-history-value-ablation-design Research Review

## Summary

- Generated at UTC: 20260524T022249Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m524_multisurface_history_value_ablation_runner
- Decision reason: M523 designs configurable variant mapping and multisurface projected/natural provenance before stronger history-value claims

## Hypothesis

M522's runner can be turned into a more useful history-value diagnostic by supporting configurable variant mappings and multiple recent projected/natural outcome surfaces.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m522_history_value_ablation_runner/summary.json, runs/m522_history_value_ablation_runner/history_value_summary.csv, runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv, runs/m487_critical_window_tail_aligned_outcome_summary/combined_tail_outcomes.csv
- parent_config: experiments/manifests/m522-history-value-ablation-runner.json
- parent_objective: multisurface history-value ablation design
- derived_from: m522-history-value-ablation-runner
- blocked_by: m522-history-value-ablation-runner
- supersedes: None
- invalidates: None

## Success Criteria

- define configurable level-to-variant mapping
- define initial projected and natural surfaces for M524
- define per-surface and combined metrics
- define classification and guardrails
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design keeps the runner hard-coded to projected variants only
- design hides surface provenance
- design treats source-narrow M522 signal as strong proof
- design requires training before multisurface diagnostics
- training or checkpoint promotion is performed

## Evidence Gates

- design configurable history-level variant mappings
- extend history-value diagnostics from M520 projected rows to natural recent outcome surfaces
- preserve projected-vs-natural surface provenance
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not hide surfaces where variant mapping fails
- do not claim projected mechanism rows prove natural scenario generalization
- do not overclaim L1/L2 unless those variants are implemented

## Failure Taxonomy

- none

## Scoreboard

- milestone: m523-multisurface-history-value-ablation-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m524_multisurface_history_value_ablation_runner
- reason: M523 designs configurable variant mapping and multisurface projected/natural provenance before stronger history-value claims

## Next Blocker

M524 should implement a configurable multisurface history-value ablation runner.
