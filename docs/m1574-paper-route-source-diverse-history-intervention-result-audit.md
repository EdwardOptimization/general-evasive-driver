# M1574 Paper-Route Source-Diverse History-Intervention Result Audit

## Summary

M1574 audits M1573.

Decision:

```text
source_diverse_history_intervention_audit_admit_history_sensitive_active_set_mining_design
```

M1573 is a clean public-pass intervention implementation, but it is not
source-diverse history evidence. The history-positive signal is live and large,
yet it is concentrated in one already-known source family:

```text
t5_near_boundary_warmup
```

The high-speed third-source anchors and late-reveal diagnostics remain
history-null. The next route should therefore mine active-set rows using
history-sensitivity itself as a first-class criterion, rather than assuming
local forced-control flip anchors will also be history-sensitive.

## M1573 Evidence

Public gates passed:

```text
target_anchor_count: 14
diagnostic_late_anchor_count: 8
all_target_anchor_count: 22
target_source_family_count: 3
target_window_count: 4
high_speed_target_anchor_count: 4
donor_pair_count: 44
intervention_row_count: 484
anchor_replay_failure_count: 0
guardrail_violation_count: 0
passes_public_smoke_gates: true
```

Evidence-quality failed:

```text
passes_evidence_quality_targets: false
history_positive_source_family_count: 1
high_speed_history_positive_count: 0
late_reveal_history_positive_count: 0
```

Strong history effects exist:

```text
max_wrong_history_margin_gap: 0.388129872572502
max_donor_response_action_margin_gap: 0.3871693514623984
history_success_drop_count: 3
control_to_history_gap_ratio: 0.22588602706600497
```

But they are source-narrow:

```text
t5_near_boundary_warmup:
  max_history_margin_gap: 0.388129872572502
  max_control_margin_gap: 0.08767311490103724
  history_positive_count: 20
  control_positive_count: 30
  history_success_drop_count: 3
```

Null families:

```text
t5_high_speed_close_obstacle:
  max_history_margin_gap: 0.002529000222704525
  max_control_margin_gap: 0.011666837639857874
  history_positive_count: 0

late_reveal_boundary:
  max_history_margin_gap: 0.00015732624357789327
  max_control_margin_gap: 0.0005579428417092913
  history_positive_count: 0
```

## Donor-Mismatch Check

The high-speed null is not obviously caused by weak donor distance.

For `t5_high_speed_close_obstacle` history rows:

```text
hidden_l2 max: 10.402652278982844
hidden_l2 mean: 8.831279420286366
response/action l2 max: 1.401655541196979
response/action l2 mean: 0.9514382493727174
```

For comparison, `t5_near_boundary_warmup` positive rows have:

```text
hidden_l2 max: 8.850482442113453
hidden_l2 mean: 7.123111568944156
response/action l2 max: 0.7829622200497904
response/action l2 mean: 0.7499402975064241
```

The high-speed donors are at least as different in hidden/response space as the
positive near-boundary donors. The more likely interpretation is that M1570
high-speed anchors are locally flippable by forced control holds, but the policy
at those anchors is not sensitive to the tested history interventions.

## Supported Claims

M1573 supports these claims:

```text
the history-intervention harness is live over M1570 anchors;
wrong-history and donor-plus-hidden variants can produce large closed-loop outcome changes;
donor response/action stream alone is much weaker than donor plus hidden in the positive family;
current-frame controls are present and do not dominate the positive history signal globally;
M1570 local-control flip anchors are not automatically history-sensitive anchors.
```

## Unsupported Claims

M1573 does not support:

```text
source-diverse history necessity;
high-speed third-source history sensitivity;
late-reveal history sensitivity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification evidence;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

This is not a code failure. It is a sampling/evidence failure: the source set is
locally recoverable and intervention-live, but the history-sensitive subset is
source-narrow.

## Route Decision

Do not route to:

```text
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout;
another donor-pairing-only repair.
```

Admit one design-only milestone:

```text
m1575-paper-route-history-sensitive-active-set-mining-design
```

The next branch step should design a miner that treats history sensitivity as
the primary acceptance criterion:

```text
wrong-history or donor-plus-hidden terminal margin gap >= 0.02;
or history success drop / collision increase;
source-family count >= 2 before any corpus export;
high-speed positive target count tracked separately;
late-reveal null tracked separately;
current-frame controls included for every candidate.
```

This changes the active-set objective:

```text
from: local forced-control flip anchors
to: anchors where policy history surgery changes closed-loop outcome
```

The M1575 design must remain no-training and no-materialization. If it admits
implementation, that implementation should be a bounded public miner, not PPO.

## Guardrails

```text
history_interventions_executed: false in M1574
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
m1575-paper-route-history-sensitive-active-set-mining-design
```
