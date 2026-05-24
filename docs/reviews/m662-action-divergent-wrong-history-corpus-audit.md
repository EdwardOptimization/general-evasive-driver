# m662-action-divergent-wrong-history-corpus-audit Research Review

## Summary

- Generated at UTC: 20260524T140708Z
- Type: gate
- Gate tier: proof
- Promotion decision: action_divergent_wrong_history_corpus_audit_admit_action_critical_source_mining_design
- Decision reason: M662 classifies M661 as implementation pass but corpus gate fail and selects broader action-critical wrong-history source mining

## Hypothesis

M661 failed because the M586/M636 matched-current surfaces are not action-divergent under BC5660 wrong-history replay, not because the corpus writer or actor checksum guard failed.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m661_action_divergent_wrong_history_corpus/summary.json, runs/m661_action_divergent_wrong_history_corpus/candidate_scores.csv, runs/m661_action_divergent_wrong_history_corpus/action_divergent_corpus.npz, docs/m661-action-divergent-wrong-history-corpus-implementation.md
- parent_config: experiments/manifests/m661-action-divergent-wrong-history-corpus-implementation.json
- parent_objective: audit negative action-divergent wrong-history corpus mining result
- derived_from: m661-action-divergent-wrong-history-corpus-implementation
- blocked_by: m661-action-divergent-wrong-history-corpus-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- audit records candidate_rows and accepted_rows
- audit records max wrong-history first-action and sequence action distances
- audit records max margin gap and threshold pass counts
- audit selects the next source-mining or objective branch explicitly
- actor coupling and PPO remain blocked
- research validation passes

## Failure Criteria

- audit ignores the zero accepted rows
- audit weakens thresholds inside the original M661 gate
- audit admits actor coupling or PPO
- audit omits no-training and actor checksum evidence

## Evidence Gates

- classify why M661 accepted zero rows
- separate weak wrong-history action divergence from implementation failure
- decide whether the next branch should broaden source mining or change objectives
- keep actor coupling, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not weaken M661 thresholds after seeing the negative result
- do not treat hidden-distance-only rows as action-divergent supervision

## Failure Taxonomy

- none

## Scoreboard

- milestone: m662-action-divergent-wrong-history-corpus-audit
- type: gate
- checkpoint: docs/m662-action-divergent-wrong-history-corpus-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_divergent_wrong_history_corpus_audit_admit_action_critical_source_mining_design
- reason: M662 classifies M661 as implementation pass but corpus gate fail and selects broader action-critical wrong-history source mining

## Next Blocker

m663-action-critical-wrong-history-source-mining-design
