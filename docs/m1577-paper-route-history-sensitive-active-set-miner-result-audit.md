# M1577 Paper-Route History-Sensitive Active-Set Miner Result Audit

## Summary

M1577 audits M1576.

Decision:

```text
history_sensitive_active_set_miner_audit_admit_high_speed_late_history_source_repair_design
```

M1576 is a valid implementation result:

```text
the miner is live;
guardrails are clean;
control-substitution share is low overall;
clean history-sensitive anchors exist across two families and five windows.
```

But M1576 is not source-diverse enough for the paper route because the
high-speed and late-reveal families remain history-null:

```text
high_speed_history_sensitive_count: 0
late_reveal_history_sensitive_count: 0
```

The next route is one design-only high-speed/late history-source repair. It must
create candidate sources where high-speed or late-reveal anchors have actual
history ambiguity before the decision point. It must not relax M1576 gates or
route directly to materialization, corpus export, training, PPO, or promotion.

## M1576 Evidence

M1576 public smoke:

```text
source_spec_count: 360
anchor_candidate_count: 512
replay_ok_anchor_count: 407
target_anchor_count: 256
donor_pair_count: 512
intervention_row_count: 5632
history_positive_pair_count: 44
clean_history_sensitive_pair_count: 40
history_sensitive_anchor_count: 32
clean_history_sensitive_anchor_count: 30
history_sensitive_source_family_count: 2
history_sensitive_window_count: 5
non_near_family_history_sensitive_count: 11
high_speed_history_sensitive_count: 0
late_reveal_history_sensitive_count: 0
control_substitution_dominated_share: 0.083984375
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
null_result_classification: high_speed_late_null
guardrail_violation_count: 0
```

Clean positive families:

```text
t5_near_boundary_warmup:
  clean anchors: 19
  max primary history gap: 0.13233165969655536

t5_boundary_axis_retarget:
  clean anchors: 11
  max primary history gap: 0.27718254452797986
```

Null families:

```text
t5_high_speed_close_obstacle:
  clean anchors: 0
  max primary history gap: 0.006224602548898783
  max control gap: 0.31220594475079233

late_reveal_boundary:
  clean anchors: 0
  max primary history gap: 0.009707924566951132
  max control gap: 0.2646042118514824

curved_boundary_obstacle:
  clean anchors: 0
  max primary history gap: 0.008609975555096128
  max control gap: 0.0674681106989774
```

## Donor-Mismatch Check

The high-speed and late-reveal nulls are not obviously explained by weak donor
distance.

High-speed pairs:

```text
pair_count: 100
target_donor_hidden_l2 max: 7.682628223977744
target_donor_hidden_l2 mean: 3.312873592697166
target_donor_response_action_l2 max: 1.2856702400548787
target_donor_response_action_l2 mean: 0.6286386193907447
primary_history_gap max: 0.006224602548898783
best_control_gap max: 0.31220594475079233
hidden_specific_gap max: 0.007520362444509043
```

Late-reveal pairs:

```text
pair_count: 102
target_donor_hidden_l2 max: 7.962133429757393
target_donor_hidden_l2 mean: 3.573199527574554
target_donor_response_action_l2 max: 1.6955861788038136
target_donor_response_action_l2 mean: 0.8518580962081143
primary_history_gap max: 0.009707924566951132
best_control_gap max: 0.2646042118514824
hidden_specific_gap max: 0.009095010722120378
```

Positive comparison families:

```text
t5_boundary_axis_retarget:
  target_donor_hidden_l2 mean: 5.517739628662029
  target_donor_response_action_l2 mean: 0.3810216700008459
  primary_history_gap max: 0.27718254452797986
  hidden_specific_gap max: 0.22036055188987191

t5_near_boundary_warmup:
  target_donor_hidden_l2 mean: 4.936553064478564
  target_donor_response_action_l2 mean: 0.45559502398792356
  primary_history_gap max: 0.13233165969655536
  hidden_specific_gap max: 0.13002778179757302
```

The high-speed/late donors are not identical to targets in hidden or
response/action space. The more likely interpretation is:

```text
the current high-speed and late-reveal candidate sources are current-frame
control-sensitive, but not hidden-history-sensitive under the fixed P0 actor.
```

## Supported Claims

M1576 supports:

```text
history-sensitive active-set mining works as an implementation;
M1576 improves over M1573 by finding clean positives in t5_boundary_axis_retarget;
clean positives span five temporal windows;
current-frame controls do not globally dominate the accepted clean set;
the high-speed/late null is a real blocker under the current source generator.
```

## Unsupported Claims

M1576 does not support:

```text
high-speed history sensitivity;
late-reveal history sensitivity;
curved-source history sensitivity;
source-diverse paper-level history necessity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

This is a source-design failure, not an implementation failure. The implementation
found clean history-sensitive anchors, but the high-speed and late-reveal source
families did not contain anchors where the fixed actor's continuation outcome
depended on wrong history.

## Route Decision

Do not route to:

```text
threshold relaxation;
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout.
```

Admit one design-only milestone:

```text
m1578-paper-route-high-speed-late-history-source-repair-design
```

The design must target high-speed and late-reveal history ambiguity directly:

```text
pre-anchor warmup evidence;
matched-current high-speed scenes;
source-diverse donor histories;
history-sensitive acceptance before local-control flip acceptance;
current-frame controls for every accepted row.
```

If M1578 cannot define a concrete repair without chasing one public gate, route
to branch synthesis instead.

## Guardrails

```text
history_interventions_executed: false in M1577
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1578-paper-route-high-speed-late-history-source-repair-design
```
