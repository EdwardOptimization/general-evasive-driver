# m526-history-value-event-audit Research Review

## Summary

- Generated at UTC: 20260524T023347Z
- Type: gate
- Gate tier: proof
- Promotion decision: source_diverse_history_value_events_admit_m527_matched_history_baseline_design
- Decision reason: M526 audits 18 M524 natural event rows as obstacle-completion drops across 2 surfaces 5 seeds and 2 targets with no projected rows and full-key duplicate share zero

## Hypothesis

M524 natural history-value event rows survive source-diversity and duplicate audits and represent real L3-vs-L0 obstacle-completion differences.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m524_natural_history_value_ablation/history_value_rows.csv, runs/m524_natural_history_value_ablation/history_value_summary.csv, runs/m524_natural_history_value_ablation/summary.json
- parent_config: experiments/manifests/m525-history-value-event-audit-design.json
- parent_objective: history-value event-row audit
- derived_from: m525-history-value-event-audit-design
- blocked_by: m525-history-value-event-audit-design
- supersedes: None
- invalidates: None

## Success Criteria

- event rows are exported
- source and duplicate summaries are written
- event semantics are reported explicitly
- audit classification is explicit
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- event rows are source-narrow or duplicated
- event semantics are inconsistent with M524 summaries
- audit mixes projected and natural rows
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- audit M524 natural L3-vs-L0 event rows
- report event semantics, source diversity, and duplicate rate
- preserve projected-vs-natural provenance
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not hide duplicate or source concentration
- do not relabel obstacle-completion drops as collisions or success drops

## Failure Taxonomy

- none

## Scoreboard

- milestone: m526-history-value-event-audit
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_diverse_history_value_events_admit_m527_matched_history_baseline_design
- reason: M526 audits 18 M524 natural event rows as obstacle-completion drops across 2 surfaces 5 seeds and 2 targets with no projected rows and full-key duplicate share zero

## Next Blocker

M527 should design matched history baselines because M526 supports source-diverse event rows but only for a reset-hidden diagnostic.
