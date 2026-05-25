# M778 V4 Limited Broader Residual Replay Audit

## Purpose

M778 audits the M777 broader residual replay result before any repair, alpha
retuning, residual retraining, PPO, or checkpoint promotion.

The question is:

```text
Is M777 a mechanism-positive result with one near-boundary normal-retention
failure, or does it show broader normal-branch degradation?
```

This milestone is audit-only:

```text
no replay run
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
no retroactive alpha selection
```

## Evidence Summary

M777 result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 2652
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

replay_rows: 21120
objective_rows: 10560
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

Alpha `0.2` improves the intended intervention-separation metrics:

```text
base intervention_action_gap_mean/p10:
  0.040348 / 0.025782

alpha 0.2 intervention_action_gap_mean/p10:
  0.046317 / 0.027627

base margin_gap_mean:
  0.029796

alpha 0.2 margin_gap_mean:
  0.033918

outcome_sensitivity_retention_rate:
  1.000000
```

The script-level candidate gate marks alpha `0.2`, `0.5`, and `1.0` as
closed-loop replay candidates. M778 does not use that script-level candidate
status as a strict pass because M775 pre-registered a stronger normal-retention
standard.

## Strict Gate Result

M775 strict alpha `0.2` gate:

```text
sample_reconstruction_success_rate >= 0.98:
  0.995475 -> pass

metadata_missing_rows == 0:
  0 -> pass

normal_success_rate == 1.0:
  0.995455 -> fail

normal_collision_rate == 0.0:
  0.004545 -> fail

intervention_action_gap_mean > base:
  0.046317 > 0.040348 -> pass

margin_gap_mean > base:
  0.033918 > 0.029796 -> pass

outcome_sensitivity_retention_rate == 1.0:
  1.0 -> pass

actor/training/PPO/promotion flags false:
  pass
```

Interpretation:

```text
M777 is mechanism-positive but strict-normal-retention-failed.
```

The residual signal transfers to the broader M773 corpus in intervention action
gap and margin gap metrics. The same alpha does not satisfy the stricter
normal-branch safety requirement.

## Normal Collision Audit

Normal-branch collisions by alpha:

```text
alpha 0.0:
  normal collisions: 0 / 2640

alpha 0.2:
  normal collisions: 12 / 2640
  unique normal collision sources: 1

alpha 0.5:
  normal collisions: 12 / 2640
  unique normal collision sources: 1

alpha 1.0:
  normal collisions: 12 / 2640
  unique normal collision sources: 1
```

All normal collisions share one source:

```text
seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
claim_boundary_level: current_model_or_proxy
```

The 12 rows are not 12 independent sources. They are the same normal rollout
repeated across the three intervention variants and four horizons:

```text
variants:
  zero_command_obs
  reset_hidden_then_normal
  reset_hidden_each_step

horizons:
  2
  4
  6
  8
```

Normal margins for the failed source:

```text
alpha 0.0:
  min_clearance_margin: +0.000124
  collision: false

alpha 0.2:
  min_clearance_margin: -0.000062
  collision: true

alpha 0.5:
  min_clearance_margin: -0.000370
  collision: true

alpha 1.0:
  min_clearance_margin: -0.000972
  collision: true
```

Alpha `0.2` only changes the first action by a very small amount on this
source:

```text
first_action_drift_vs_base_normal: 0.000380
first residual:
  steer: +0.001266
  throttle: -0.000992
  brake: +0.001012
```

This is a near-boundary terminal-margin cliff: the base normal branch has only
`0.000124` margin, so a small residual can flip it into collision.

## Intervention Collision Audit

Intervention-branch collisions are not newly introduced by alpha `0.2`:

```text
alpha 0.0:
  intervention collisions: 36 / 2640
  unique intervention collision sources: 3

alpha 0.2:
  intervention collisions: 36 / 2640
  unique intervention collision sources: 3

alpha 0.5:
  intervention collisions: 36 / 2640
  unique intervention collision sources: 3

alpha 1.0:
  intervention collisions: 36 / 2640
  unique intervention collision sources: 3
```

The three intervention collision sources are:

```text
seed 77025 source_index 3:
  halfshaft_torque_loss_proxy
  drive_authority_drop->combined_fault

seed 77025 source_index 12:
  halfshaft_torque_loss_proxy
  drive_authority_drop->rear_lateral_authority_drop

seed 77025 source_index 93:
  halfshaft_torque_loss_proxy
  drive_authority_drop->combined_fault
```

The failed normal source is also one of the already intervention-colliding
sources. That means the source is genuinely boundary-sensitive, but M777 does
not preserve the required distinction:

```text
base normal succeeds narrowly;
wrong/ablated history fails;
alpha 0.2 residual makes normal fail too.
```

## Rejected Rows

Rejected rows:

```text
rejected_rows: 12
reason: unsupported_variant:command_shift_obs
metadata_missing_rows: 0
affected seed: 77025
affected source_index values:
  3
  12
  93
```

These rejected rows do not explain the strict normal-retention failure. The
normal collision rows are reconstructed and evaluated.

## Supported Claims

M778 supports:

```text
1. M777 is not a routing or metric artifact. Reconstruction is high,
   metadata is present, and actor/training/PPO/promotion flags remain clean.

2. The residual mechanism transfers to the broader M773 corpus in the intended
   intervention action-gap and margin-gap metrics.

3. Broader source mining was valuable: M773 exposed a near-boundary normal
   collision source that M770's smaller holdout did not reveal.

4. The normal-retention failure is concentrated in one unique source, not a
   broad normal-branch collapse across the corpus.
```

## Falsified Claims

M778 falsifies:

```text
1. Alpha 0.2 cleanly passes the stricter M775 normal-retention gate on the
   broader M773 corpus.

2. The script-level closed-loop candidate flag is sufficient for accepting
   the result as strict-retention-safe.

3. The M777 failure can be ignored as duplicate rows only. The duplicates
   refer to one source, but that source is a real normal collision at alpha
   0.2.
```

M778 does not prove:

```text
1. Broad distributional generalization.

2. Driver promotion readiness.

3. PPO safety.

4. A safe alpha below 0.2.

5. True four-wheel, single-wheel, halfshaft, or tire-blowout physical fidelity.
```

## Failure Taxonomy

Primary failure:

```text
behavior_regression
```

Reason:

```text
The strict normal branch regresses from 2640/2640 success at alpha 0.0 to
2628/2640 success at alpha 0.2, with 12 normal collision rows from one source.
```

Secondary risk:

```text
scenario_sampling_failure
```

Reason:

```text
The failing source is concentrated in seed 77025 and a current-model/proxy
halfshaft fault family. The next step must determine whether this is a
repairable near-boundary source, an alpha threshold issue, or evidence that the
residual objective needs explicit normal-margin retention.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not training_instability
not promotion_gate_failure
not proof_washout
```

## Decision

Decision:

```text
admit_broader_normal_boundary_alpha_probe_design
```

M778 does not admit PPO, promotion, or residual retraining. It also does not
retroactively retune alpha. The next milestone should design a pre-registered
normal-boundary alpha probe that asks:

```text
1. Is there an alpha below 0.2 that keeps strict normal retention on M773?
2. Does that lower alpha still improve intervention action-gap and margin-gap?
3. Is seed 77025 / source_index 12 the only near-boundary normal source under
   a lower-alpha ladder?
4. If no lower alpha preserves both normal retention and intervention signal,
   should the branch pivot to explicit normal-margin retention or targeted
   boundary-source repair?
```

Next blocker:

```text
m779-v4-broader-normal-boundary-alpha-probe-design
```

PPO, checkpoint promotion, residual retraining, and broad generalization claims
remain blocked.
