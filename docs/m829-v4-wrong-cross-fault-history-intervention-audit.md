# M829 V4 Wrong-Cross-Fault History Intervention Audit

## Purpose

M829 audits the M828 hidden-only wrong-history intervention result before
continuing the route.

The audit question is:

```text
Did M828 fail because wrong-history injection is implemented incorrectly, or
because the matched pairs are too far from terminal boundary to reveal margin
sensitivity?
```

M829 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m828_v4_wrong_cross_fault_history_intervention/summary.json
runs/m828_v4_wrong_cross_fault_history_intervention/wrong_history_replay_rows.csv
runs/m828_v4_wrong_cross_fault_history_intervention/diversity_summary.json
runs/m828_v4_wrong_cross_fault_history_intervention/gate_summary.csv
docs/m828-v4-wrong-cross-fault-history-intervention-implementation.md
```

M828 result class:

```text
v4_wrong_cross_fault_history_intervention_history_insensitive
```

## Artifact Consistency

M828 produced complete implementation artifacts:

```text
raw_matched_pair_rows: 256
selected_pair_rows: 108
reconstructed_snapshot_rows: 15
reconstructed_pairs: 108
wrong_history_replay_rows: 756
rejected_pair_rows: 148
```

All rejected pairs were rejected by source-balancing:

```text
source_balance_limit: 148
```

There is no broad reconstruction failure.

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

This is not a contract violation.

## Boundary Audit

The decisive finding is that the matched pairs are not near boundary:

```text
normal margin min:    0.21766916668222658
normal margin p05:    0.21766916668222658
normal margin median: 1.0287735657138812
normal margin p95:    1.445581191589894
normal margin max:    1.6287021829635082
normal margin mean:   0.9101195474991486
normal margin <= 0.05: 0 / 108
normal margin <= 0.01: 0 / 108
```

This explains why margin effects are tiny. The pairs are action-divergent, but
they are too safe to make small action perturbations matter.

## Wrong-History Effect Audit

Wrong hidden state has a consistent direction but too little magnitude:

```text
wrong_history_closer_to_right_action: 108 / 108
wrong action L2 min:    0.004485107893901902
wrong action L2 median: 0.004707772050060773
wrong action L2 max:    0.006900976889874039
wrong action >= 0.014: 0 / 108
```

Wrong-history margin gaps:

```text
wrong gap min:    -0.000056051012100599706
wrong gap p05:    -0.000012590642987309053
wrong gap median: 0.000012457369753082759
wrong gap p95:    0.000016239678017893056
wrong gap max:    0.00002602146853414311
wrong gap mean:   0.00000457997085936248
wrong gap >= 0.01: 0 / 108
```

M828 therefore shows:

```text
wrong hidden affects action direction,
but hidden-only wrong-history injection is not enough on these wide-margin pairs.
```

## Variant Comparison

Maximum margin gaps:

```text
zero_command_obs:         0.004455360584227908
reset_hidden_each_step:   0.003792395652133518
reset_hidden_then_normal: 0.0010199475969434602
command_shift_obs:        0.0009262217984864485
wrong_cross_fault_hidden: 0.00002602146853414311
response_delay_obs:       0.000010002057777125373
```

No variant reaches the `0.01` primary margin-gap gate on the M828 pair set.
This is not zero-command dominance; it is pair-boundary slack.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. M828 selected action-divergent matched pairs, but not
near-boundary matched pairs. Normal margins are too high for wrong-history
injection to affect outcome.

### metric_artifact

The `108/108` closer-to-right action result is useful diagnostic evidence, but
it is not pass evidence because the action and margin gates are both below
threshold.

### not contract_violation

The actor and residual-head checksums are unchanged and no PPO or promotion
occurred.

## Supported Claims

M828 supports:

- wrong-cross-fault hidden injection is implemented;
- matched pairs reconstruct successfully;
- wrong hidden consistently moves the first action toward the matched
  different-fault action;
- the current pair set is too far from boundary for outcome evidence.

## Unsupported Claims

M828 does not support:

- strong wrong-history action sensitivity;
- wrong-history margin degradation;
- source-diverse self-ID evidence;
- PPO admission;
- checkpoint promotion.

## Decision

Decision:

```text
admit_near_boundary_wrong_history_pair_mining_design
```

Rationale:

```text
Full-history replay is not the first control variable because right.hidden is
already the encoded right command-response history. The immediate failure is
that matched pairs are wide-margin. The next route should mine matched
different-fault pairs near terminal boundary, then rerun wrong-history replay.
```

Next:

```text
m830-v4-near-boundary-wrong-history-pair-mining-design
```

PPO, checkpoint promotion, threshold relaxation, and learned gating remain
blocked.
