# M765 V4 Residual Closed-Loop Replay Audit

## Purpose

M765 audits the M764 closed-loop residual replay result before any source
holdout replay, PPO, checkpoint promotion, or simulator-fidelity claim.

The question is:

```text
Is M764 a clean closed-loop mechanism positive, and what evidence is still
missing before claiming generalization?
```

This audit is process-only:

```text
no actor training
no residual retraining
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M764 result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0

replay_rows: 9704
objective_rows: 4852
candidate_alphas:
  0.2
  0.5
  1.0

actor_backbone_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
```

Key alpha comparison:

```text
base alpha 0.0:
  normal_success_rate: 1.0
  intervention_action_gap_mean/p10: 0.041716 / 0.026395
  margin_gap_mean: 0.028754

alpha 0.2:
  normal_success_rate: 1.0
  normal_collision_rate: 0.0
  normal_first_action_drift_mean/p95: 0.000480 / 0.000939
  intervention_action_gap_mean/p10: 0.047937 / 0.028594
  margin_gap_mean: 0.032770
  intervention_collision_rate: 0.0

alpha 0.5:
  normal_success_rate: 1.0
  normal_collision_rate: 0.0
  normal_first_action_drift_mean/p95: 0.001200 / 0.002348
  intervention_action_gap_mean/p10: 0.057721 / 0.031984
  margin_gap_mean: 0.039159
  intervention_collision_rate: 0.000824

alpha 1.0:
  normal_success_rate: 1.0
  normal_collision_rate: 0.0
  normal_first_action_drift_mean/p95: 0.002401 / 0.004697
  intervention_action_gap_mean/p10: 0.074868 / 0.038011
  margin_gap_mean: 0.050751
  intervention_collision_rate: 0.003298
```

M764 is clean as a mechanism replay result: normal behavior is retained on the
registered public corpus, and wrong/ablated-history branches become more
action-divergent and margin-sensitive as residual alpha increases.

## Intervention Collision Audit

Alpha `1.0` creates `4/1213` intervention-branch collisions. They are
concentrated:

```text
variant: zero_command_obs
horizon: 6 or 8
seed: 76030
preferred_fault_family: front_lateral_authority_drop
wrong_fault_family: combined_fault
fault_family_pair: front_lateral_authority_drop->combined_fault
terminal_reason: collision
```

These are not normal driver branch regressions. They are wrong/ablated-history
branch failures, which can be useful mechanism sensitivity evidence. Still,
the concentration means alpha `1.0` should be treated as aggressive diagnostic
alpha, not the conservative next candidate.

Conservative next alpha:

```text
alpha 0.2
```

Reason:

```text
It passes closed-loop gates, improves intervention action gap and margin gap,
keeps normal first-action drift very small, and creates no intervention
collisions on the public replay.
```

## Supported Claims

M765 supports:

```text
1. M764 is a clean closed-loop mechanism positive on the public M755/M761
   replay corpus.

2. M761's exact residual signal survives rollout; it is not only a first-action
   metric artifact.

3. Normal behavior is retained on the registered public corpus for all tested
   residual alphas.

4. Alpha 0.2 is the conservative candidate for the next no-PPO source-holdout
   replay.
```

## Falsified Claims

M765 falsifies:

```text
1. The residual head cannot be evaluated in closed loop without mutating the
   base actor.

2. The M761 signal disappears under rollout.

3. Any residual alpha that increases intervention sensitivity must immediately
   degrade normal branch success on the public corpus.
```

M765 does not prove:

```text
1. Generalization to fresh source rows or fresh seeds.

2. PPO safety.

3. Driver checkpoint promotability.

4. True single-wheel / tire blowout / axle-break / four-wheel physics.
```

## Holdout Contamination Note

M755 positive rows contain:

```text
assigned_split=train: 1109
assigned_split=heldout: 104
```

But M761 trained the residual head on all M755 positive rows. Therefore the
existing `assigned_split=heldout` field cannot be used as an unbiased holdout
for the residual head.

The next holdout must be fresh relative to M761. Acceptable options:

```text
1. source rows from M749/M752 that were not included in M755/M761, if enough
   clean positives can be reconstructed;

2. a new v4 reset-source sequence intervention wave with disjoint seeds or
   disjoint source proposals;

3. a source-balanced capped fresh replay if full fresh mining is too expensive.
```

## Failure Taxonomy Summary

Primary residual risk:

```text
scenario_sampling_failure
```

Reason:

```text
M764 is positive but still public-corpus evidence. The corpus is dominated by
zero_command_obs and long horizons, hard-negative availability remains
0.721352, and the existing heldout split is contaminated for the residual head.
```

Other risks:

```text
public_gate_overfit_risk:
  M761 trained on the same public source family evaluated by M764.

subgroup_concentration:
  alpha 1.0 intervention collisions concentrate in one seed/fault-family pair.
```

Not failures:

```text
not metadata_artifact
not reconstruction_blocked
not contract_violation
not proof_washout
not training_instability
not promotion_gate_failure
```

## Next Branch Decision

Decision:

```text
promote_to_v4_residual_source_holdout_replay_design
```

M766 should design a no-PPO source-holdout replay that:

```text
1. uses the frozen BC5660 actor plus M761 residual head;
2. prioritizes alpha 0.2, with alpha 0.5 and 1.0 diagnostic only;
3. uses source rows not used for M761 residual training;
4. preserves the same normal retention and intervention sensitivity metrics;
5. reports whether fresh source replay supports or weakens the coverage-mining
   hypothesis;
6. keeps PPO and checkpoint promotion blocked.
```

If a sufficiently fresh holdout cannot be built from existing artifacts, M766
should design a fresh v4 source-mining wave instead of forcing a contaminated
holdout.
