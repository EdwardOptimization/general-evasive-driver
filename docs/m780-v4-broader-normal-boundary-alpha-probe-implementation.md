# M780 V4 Broader Normal-Boundary Alpha Probe Implementation

## Purpose

M780 runs the no-training lower-alpha probe designed by M779 after M777 failed
strict normal retention at alpha `0.2`.

The question is:

```text
Is there a residual alpha below 0.2 that preserves strict normal retention on
the broader M773 corpus while still improving intervention sensitivity?
```

This run is replay-only:

```text
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m780_v4_broader_normal_boundary_alpha_probe \
  --device cpu \
  --alphas 0.0,0.05,0.1,0.125,0.15,0.175,0.2
```

## Evidence Summary

Registered result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 2652
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

replay_rows: 36960
objective_rows: 18480

candidate_alpha_count: 4
candidate_alphas:
  0.125
  0.15
  0.175
  0.2

actor_backbone_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

The script-level best candidate is:

```text
alpha: 0.125
```

## Alpha Metrics

Base:

```text
alpha 0.0:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.040348 / 0.025782
  margin_gap_mean: 0.029796
  intervention_collision_rate: 0.013636
```

Lower alphas:

```text
alpha 0.05:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.041814 / 0.026207
  margin_gap_mean: 0.030811
  script_closed_loop_replay_candidate: false

alpha 0.10:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.043298 / 0.026634
  margin_gap_mean: 0.031837
  script_closed_loop_replay_candidate: false

alpha 0.125:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  normal_first_action_drift_mean/p95_vs_base: 0.000244 / 0.000586
  intervention_action_gap_mean/p10: 0.044047 / 0.026886
  margin_gap_mean: 0.032352
  outcome_sensitivity_retention_rate: 1.000000
  script_closed_loop_replay_candidate: true
```

Known failing region:

```text
alpha 0.15:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  intervention_action_gap_mean/p10: 0.044799 / 0.027112
  margin_gap_mean: 0.032871

alpha 0.175:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  intervention_action_gap_mean/p10: 0.045556 / 0.027369
  margin_gap_mean: 0.033393

alpha 0.20:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  intervention_action_gap_mean/p10: 0.046317 / 0.027627
  margin_gap_mean: 0.033918
```

Interpretation:

```text
Alpha 0.125 is the only tested alpha that both satisfies strict normal
retention and passes the script-level closed-loop replay candidate gate.
```

Alphas `0.05` and `0.10` retain normal behavior and improve the raw gap/margin
metrics over base, but the script-level closed-loop candidate threshold does
not accept them. Alphas `0.15`, `0.175`, and `0.20` improve the gap metrics
more but fail strict normal retention on the same near-boundary source.

## Boundary Source Stratification

The M777 failing source behaves as a clean alpha boundary:

```text
seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

Normal margin by alpha:

```text
alpha 0.0:
  margin: +0.000124
  collisions: 0 / 12

alpha 0.05:
  margin: +0.000079
  collisions: 0 / 12

alpha 0.10:
  margin: +0.000033
  collisions: 0 / 12

alpha 0.125:
  margin: +0.000009
  collisions: 0 / 12

alpha 0.15:
  margin: -0.000014
  collisions: 12 / 12

alpha 0.175:
  margin: -0.000038
  collisions: 12 / 12

alpha 0.20:
  margin: -0.000062
  collisions: 12 / 12
```

First-action drift for that source:

```text
alpha 0.05:  0.000095
alpha 0.10:  0.000190
alpha 0.125: 0.000238
alpha 0.15:  0.000285
alpha 0.175: 0.000333
alpha 0.20:  0.000380
```

This supports the M778 interpretation: M777 did not reveal broad normal branch
collapse. It revealed a very tight terminal-margin boundary. Alpha `0.125`
threads the boundary, but with only about `9e-6` margin on the source.

## Intervention Collision Audit

Intervention collisions are unchanged across the alpha ladder:

```text
alpha 0.0:   36 collisions, 3 unique sources
alpha 0.05:  36 collisions, 3 unique sources
alpha 0.10:  36 collisions, 3 unique sources
alpha 0.125: 36 collisions, 3 unique sources
alpha 0.15:  36 collisions, 3 unique sources
alpha 0.175: 36 collisions, 3 unique sources
alpha 0.20:  36 collisions, 3 unique sources
```

Thus M780's lower-alpha result is not hiding a new intervention-branch failure
mode. The intervention branch was already collision-sensitive at base alpha.

## Rejected Rows

Rejected rows remain the same as M777:

```text
rejected_rows: 12
reason: unsupported_variant:command_shift_obs
metadata_missing_rows: 0
```

The rejected rows do not explain alpha feasibility or the normal boundary.

## Supported Claims

M780 supports:

```text
1. M777's alpha 0.2 failure was a narrow residual-scale boundary, not broad
   normal branch collapse.

2. A lower alpha can preserve strict normal retention and retain measurable
   intervention action-gap and margin-gap improvement on the broader M773
   corpus.

3. Alpha 0.125 is the strongest tested alpha that both passes strict normal
   retention and satisfies the script-level replay candidate gate.

4. The broader data wave was valuable: it exposed the tight normal-margin
   boundary that smaller M770 did not show.
```

## Falsified Claims

M780 falsifies:

```text
1. No alpha below 0.2 can preserve strict normal retention while improving
   intervention sensitivity.

2. The normal-retention failure is spread across many broader-corpus sources.

3. Alpha 0.2 can be accepted under the strict M775/M779 normal-retention
   standard.
```

M780 does not prove:

```text
1. Driver promotion readiness.

2. PPO safety.

3. Robust margin around alpha 0.125.

4. Broad generalization beyond this current-model/proxy corpus.

5. True four-wheel or single-wheel fault fidelity.
```

## Failure Taxonomy

Primary residual risk:

```text
behavior_regression
```

Reason:

```text
The alpha ladder identifies the collision boundary, but alphas at or above
0.15 still regress normal branch behavior on source 77025/source_index 12.
```

Secondary risk:

```text
scenario_sampling_failure
```

Reason:

```text
The result remains tied to M773's current-model/proxy broader corpus with hard
negative sparsity and source concentration caveats.
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

M780 admits audit only:

```text
m781-v4-broader-normal-boundary-alpha-probe-audit
```

M781 should decide whether alpha `0.125` is enough as a limited
alpha-feasibility diagnostic or whether the next branch should redesign the
residual objective with explicit normal-margin retention around near-boundary
sources.

PPO, checkpoint promotion, residual retraining, and broad generalization claims
remain blocked.
