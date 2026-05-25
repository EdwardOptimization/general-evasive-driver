# M771 V4 Limited Residual Holdout Replay Audit

## Purpose

M771 audits the M770 limited fresh-holdout residual replay result before any
broader source wave, residual objective change, PPO, or checkpoint promotion.

The question is:

```text
Does M770 provide real limited holdout support for the coverage-mining
hypothesis, and what remains before stronger generalization claims?
```

This audit is process-only:

```text
no replay run
no actor training
no residual retraining
no PPO
no checkpoint promotion
```

## Evidence Summary

M770 result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 995
reconstructed_rows: 995
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0

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

Primary alpha `0.2`:

```text
normal_success_rate: 1.0
normal_collision_rate: 0.0
normal_first_action_drift_mean/p95: 0.000553 / 0.001208

intervention_action_gap_mean/p10:
  base: 0.043862 / 0.039491
  alpha 0.2: 0.050473 / 0.045717

margin_gap_mean:
  base: 0.026641
  alpha 0.2: 0.030329

outcome_sensitivity_retention_rate: 1.0
closed_loop_replay_candidate: true
```

This is a real limited holdout positive: the pre-registered primary alpha
transfers to disjoint-seed source rows.

## Collision / Concentration Audit

Normal branch:

```text
normal collisions: 0 / 995 for every alpha
normal success: 995 / 995 for every alpha
```

Intervention branch:

```text
alpha 0.0 collisions: 20 / 995
alpha 0.2 collisions: 23 / 995
alpha 0.5 collisions: 28 / 995
alpha 1.0 collisions: 31 / 995
```

Collision rows are concentrated:

```text
base alpha 0.0:
  dominant seed: 76519
  preferred_fault_family: combined_fault
  wrong_fault_family: global_mu_drop / brake_authority_drop

alpha 0.2 added collision concentration:
  seeds: 76521, 76573
  preferred_fault_family: front_lateral_authority_drop
  wrong_fault_family: combined_fault
```

Interpretation:

```text
The residual increases wrong/ablated-history sensitivity on holdout, while
normal behavior remains safe. However, because both source rows and collision
rows are concentrated, this is still limited mechanism evidence, not broad
generalization evidence.
```

## Supported Claims

M771 supports:

```text
1. The user's coverage hypothesis is materially supported: after broad v4
   source mining, the residual self-ID mechanism appears on public rows and on
   a fresh disjoint-seed holdout.

2. Alpha 0.2 is a genuine conservative limited-holdout candidate, not merely a
   public-corpus artifact.

3. The project now has a stronger evidence chain:
   v4 coverage -> sequence outcome rows -> objective residual signal ->
   public closed-loop replay -> limited fresh holdout replay.
```

## Falsified Claims

M771 falsifies:

```text
1. The M761/M764 residual mechanism was only public-corpus overfit.

2. Fresh source rows produce no residual closed-loop mechanism signal.

3. Alpha 0.2 immediately fails on holdout.
```

M771 does not prove:

```text
1. Broad distributional generalization.

2. Driver promotion readiness.

3. PPO safety.

4. True tire blowout / axle break / single-wheel fault physics.
```

## Failure Taxonomy Summary

Primary residual risk:

```text
scenario_sampling_failure
```

Reason:

```text
The holdout result is positive but the source corpus is sparse and concentrated.
This limits claim scope and motivates a broader source-holdout wave before
stronger claims.
```

Not failures:

```text
not metadata_artifact
not reconstruction_blocked
not private_holdout_contamination
not contract_violation
not proof_washout
not training_instability
not promotion_gate_failure
```

## Next Branch Decision

Decision:

```text
promote_to_broader_source_holdout_wave_design
```

M772 should design a broader fresh source-holdout wave, not PPO. The goal is to
reduce source concentration and raise fault-family-pair diversity before making
stronger generalization claims.

Recommended direction:

```text
1. use a larger or multi-block fresh seed range;
2. keep source selection disjoint from M761/M767;
3. preserve no-training / no-PPO / no-promotion scope;
4. target at least:
   positive_rows >= 1500
   unique_positive_seeds >= 40
   unique_positive_fault_family_pairs >= 18
   max_positive_seed_dominance <= 0.15
5. only after audit, run residual replay again with alpha 0.2 primary.
```

PPO and checkpoint promotion remain blocked.
