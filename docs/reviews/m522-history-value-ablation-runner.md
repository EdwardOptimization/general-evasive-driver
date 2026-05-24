# m522-history-value-ablation-runner Research Review

## Summary

- Generated at UTC: 20260524T022249Z
- Type: gate
- Gate tier: proof
- Promotion decision: margin_only_history_value_signal_admit_m523_multisurface_history_value_design
- Decision reason: M522 implements L3-vs-L0 diagnostic summary on M520 projected outcomes; L0 has 8 margin candidates across 2 seeds and zero event rows

## Hypothesis

A diagnostic history-level ablation can measure whether the M399 online GRU recurrent belief state adds near-boundary control value beyond reset-hidden current-feedback rollouts.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m520_valid_offset_projection_outcome_gate/summary.json, runs/m520_valid_offset_projection_outcome_gate/projected_outcomes.csv
- parent_config: experiments/manifests/m521-history-value-ablation-design.json
- parent_objective: history-value ablation runner
- derived_from: m521-history-value-ablation-design
- blocked_by: m521-history-value-ablation-design
- supersedes: None
- invalidates: None

## Success Criteria

- history-value ablation runner is implemented
- L3 versus L0 diagnostic runs on at least one recent proof surface
- per-row outcomes and summary tables are written
- surface provenance and ablation limitations are documented
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- runner changes actor inputs
- runner trains or promotes a checkpoint
- runner cannot reproduce normal L3 baseline outcomes
- summary omits surface provenance
- L1/L2 approximations are overclaimed

## Evidence Gates

- run a diagnostic history-value ablation without training
- compare at least L3 normal recurrent rollout against L0 reset-hidden-each-step
- report limitations of L1/L2 if not implemented yet
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim feedforward baseline parity without training a matched baseline
- do not hide projected-vs-natural surface provenance

## Failure Taxonomy

- none

## Scoreboard

- milestone: m522-history-value-ablation-runner
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_only_history_value_signal_admit_m523_multisurface_history_value_design
- reason: M522 implements L3-vs-L0 diagnostic summary on M520 projected outcomes; L0 has 8 margin candidates across 2 seeds and zero event rows

## Next Blocker

M523 should design a multisurface history-value ablation because M522 is only a source-narrow projected-surface diagnostic.
