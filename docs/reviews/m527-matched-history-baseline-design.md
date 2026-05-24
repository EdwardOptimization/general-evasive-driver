# m527-matched-history-baseline-design Research Review

## Summary

- Generated at UTC: 20260524T023347Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: admit_m528_matched_history_baseline_plumbing
- Decision reason: M527 designs matched L0/L1/L2/L3 baseline plumbing before training so reset-hidden diagnostics are not overclaimed

## Hypothesis

After M526 validates source-diverse L3-vs-L0 diagnostic event rows, the next evidence layer should compare matched deployable history baselines rather than continuing reset-hidden diagnostics.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m526_history_value_event_audit/summary.json, runs/m526_history_value_event_audit/event_rows.csv
- parent_config: experiments/manifests/m526-history-value-event-audit.json
- parent_objective: matched history baseline design
- derived_from: m526-history-value-event-audit
- blocked_by: m526-history-value-event-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define L0/L1/L2/L3 baseline levels
- define training and evaluation discipline
- define first plumbing milestone
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- design adds hidden or oracle inputs
- design launches long training before plumbing and smoke validation
- design treats reset-hidden diagnostic as final matched baseline evidence
- training or checkpoint promotion is performed

## Evidence Gates

- design matched L0/L1/L2/L3 baselines after source-diverse diagnostic history-value events
- preserve P0 no-wheel no-oracle input contract
- preflight before long training
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not claim reset-hidden diagnostic equals a trained feedforward baseline
- do not overclaim L1/L2 before implementation

## Failure Taxonomy

- none

## Scoreboard

- milestone: m527-matched-history-baseline-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m528_matched_history_baseline_plumbing
- reason: M527 designs matched L0/L1/L2/L3 baseline plumbing before training so reset-hidden diagnostics are not overclaimed

## Next Blocker

M528 should implement matched history baseline plumbing.
