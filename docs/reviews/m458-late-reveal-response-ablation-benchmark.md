# m458-late-reveal-response-ablation-benchmark Research Review

## Summary

- Generated at UTC: 20260523T203055Z
- Type: gate
- Gate tier: generalization
- Promotion decision: weak_aggregate_admit_m459_matched_current_mining
- Decision reason: M458 late-reveal ablations show weak aggregate history necessity: zero-current success 0.802083 and no-action success 0.822917 so matched-current mining is next not training

## Hypothesis

The M457 late-reveal config may create more useful response/history ablation differences than the M451 robust configs, but this must be tested on source-diverse seeds before matched-current mining or training.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m457_late_reveal_reset_stress/summary.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m457-history-necessity-config-implementation.json
- parent_objective: late-reveal response/history ablation benchmark
- derived_from: m457-history-necessity-config-implementation
- blocked_by: m457-history-necessity-config-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- all planned ablation benchmarks complete without scenario sampling failure
- results cover at least three seed windows
- documentation reports whether ablation deltas are strong enough for matched-current mining
- no checkpoint is promoted

## Failure Criteria

- scenario sampling fails
- benchmark is only a single small smoke
- results are interpreted as self-ID proof without intervention/matched-current evidence
- actor contract changes

## Evidence Gates

- run M399 base reset zero-current and zero-action ablations on M457 config
- use source-diverse seed windows rather than a single 16-episode smoke
- report aggregate success return termination and clearance deltas
- decide whether to mine matched-current rows or redesign again
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not claim self-ID from aggregate success alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m458-late-reveal-response-ablation-benchmark
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: 0.812500
- termination_rate: 0.187500
- clearance_margin_mean: 2.107460
- reset_success: 0.817708
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: weak_aggregate_admit_m459_matched_current_mining
- reason: M458 late-reveal ablations show weak aggregate history necessity: zero-current success 0.802083 and no-action success 0.822917 so matched-current mining is next not training

## Next Blocker

m459-late-reveal-matched-current-mining
