# M889 V4 Enriched Pair-Delta Replay Proof Gate Implementation

## Purpose

M889 executes the proof-gate stack designed in M888 for the M886
exact-admissible objective-only candidate.

Candidate:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
```

Baseline:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M889 does not run PPO and does not promote a checkpoint.

## Exact Recheck

Run:

```text
runs/m889_alpha_0_1_exact_recheck
```

Result:

```text
result_class: v4_enriched_pair_delta_objective_sanity_pass
expected_rows: 247
tensor_rows_reconstructed: 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
exact_losses_finite: true
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Compared with the M568/M883 base exact metrics:

```text
split                         delta
objective_train_public        -0.00012192464233318212
objective_eval_public         -0.00005724755200486875
source_holdout_public         -0.00011080083260894824
new_signature_holdout_public  -0.00004684925079345703
```

Note: this recheck reconstructs snapshots under the candidate checkpoint. The
fixed-tensor comparison remains the M886 interpolation artifact; this recheck is
an additional no-update consistency check.

## Replay Proof Gates

Run:

```text
runs/m889_m886_a010_replay_proof_gate
```

All six replay/proof surfaces passed:

```text
surface    rows  baseline_drops  candidate_drops  normal_margin_delta  margin_gap_delta  pass
M183/M168  16    0               0                +0.0000326381        +0.0000000096    true
M183/M170  17    0               0                +0.0000343508        +0.0000000100    true
M193/M189  14    0               0                +0.0000875210        -0.0000000223    true
M212/M204  17    0               0                +0.0000910832        -0.0000000234    true
M223/M219  17    0               0                +0.0000910843        -0.0000000214    true
M267/M264  17    0               0                +0.0000910580        -0.0000000278    true
```

Aggregate:

```text
replay_gate_count: 6
replay_gates_passed: 6
replay_gates_failed: 0
overall_pass: true
failure_types: none
actor_inputs_changed: false
```

## Behavior Retention

Runs:

```text
runs/m889_m886_a010_behavior_seed9505
runs/m889_m886_a010_behavior_seed9506
```

Per seed:

```text
seed  policy     success  termination  clearance_mean  return_mean
9505  m568_base  0.8125   0.1875       1.465080        69.604261
9505  m886_a010  0.8125   0.1875       1.465567        69.600278
9506  m568_base  0.8125   0.1875       1.479410        69.919597
9506  m886_a010  0.8125   0.1875       1.479901        69.915583
```

Aggregate candidate minus base:

```text
success_rate_delta: 0.0
termination_rate_delta: 0.0
min_clearance_margin_mean_delta: +0.0004892324201435372
return_mean_delta: -0.003998606511459002
```

Diagnostics:

```text
m886_a010_reset success_mean: 0.8125
m886_a010_zero_all success_mean: 0.7250
```

Behavior retention passes versus M568. The reset/zero-all rows are diagnostic
only, not promotion evidence.

## Interpretation

M889 is a clean proof-gate positive:

```text
M886 alpha_0_1 preserves M568-relative exact objective metrics, all six
closed-loop replay/proof surfaces, and behavior seeds 9505/9506.
```

This result still does not justify promotion:

- the candidate is rooted at the M568 diagnostic BC checkpoint, not the current
  public-gate driver base;
- the exact objective rows are public workflow artifacts;
- the behavior metrics are retention-level, not a meaningful driver-performance
  gain;
- no private/generalization holdout was used;
- no PPO continuation is admitted by this milestone.

## Decision

Decision:

```text
v4_enriched_pair_delta_replay_proof_gate_pass
```

Next:

```text
m890-v4-enriched-pair-delta-replay-proof-gate-audit
```

M890 should decide whether this branch should:

```text
continue with a repeat proof-gate seed/candidate,
route to source/generalization gate,
or stop because the movement is too small to matter.
```

It must not promote directly from M889.
