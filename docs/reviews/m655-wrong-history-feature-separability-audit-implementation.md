# m655-wrong-history-feature-separability-audit-implementation Research Review

## Summary

- Generated at UTC: 20260524T133443Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: wrong_history_feature_separability_audit_implementation_fusion_washout_admit_m656
- Decision reason: M655 classifies wrong-history separability as fusion_washout with raw hidden signal present but fused feature/action gaps much weaker than delayed-history

## Hypothesis

The M652 wrong-history contrast failure can be localized by measuring whether normal-vs-wrong differences survive from stored recurrent hidden state into next hidden state fused actor features and actor actions.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz, runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv, runs/m652_bc_v2_wrong_history_contrast/summary.json, docs/m654-wrong-history-feature-separability-audit-design.md
- parent_config: experiments/manifests/m654-wrong-history-feature-separability-audit-design.json
- parent_objective: implement no-training wrong-history frozen-feature separability audit
- derived_from: m654-wrong-history-feature-separability-audit-design
- blocked_by: m654-wrong-history-feature-separability-audit-design
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json is written
- row_feature_separability.csv is written
- all required group summaries are written
- actor checksum remains unchanged
- no checkpoint is written
- implementation doc records the collapse classification
- research validation passes

## Failure Criteria

- audit trains any model parameter
- audit writes a checkpoint
- audit omits wrong-history or delayed-history breakdowns
- audit changes actor input contract
- audit claims promotion or self-ID proof

## Evidence Gates

- compute row-level raw hidden next-hidden fused-feature and actor-action distances
- write variant split source source-split-variant target and surface summaries
- separate wrong_matched_history from delayed_history
- verify actor checksum unchanged and no checkpoint written
- classify where the normal-vs-wrong signal appears to collapse

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor parameters
- do not write checkpoint
- do not use metadata as actor input
- do not treat feature distance alone as self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m655-wrong-history-feature-separability-audit-implementation
- type: infrastructure
- checkpoint: runs/m655_wrong_history_feature_separability_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_feature_separability_audit_implementation_fusion_washout_admit_m656
- reason: M655 classifies wrong-history separability as fusion_washout with raw hidden signal present but fused feature/action gaps much weaker than delayed-history

## Next Blocker

m656-wrong-history-separability-audit
