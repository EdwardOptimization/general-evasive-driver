# M893 V4 Enriched Pair-Delta Fresh-Seed Replay Proof Gate

## Purpose

M893 executes the proof-gate stack for the M891 fresh-seed exact-admissible
objective-only candidate.

Candidate:

```text
runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt
```

Baseline:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

M893 does not run PPO and does not promote a checkpoint.

## Exact Recheck

Run:

```text
runs/m893_alpha_0_1_exact_recheck
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
actor_parameters_changed: false
```

Compared with the M568/M883 base exact metrics:

```text
split                         delta
objective_train_public        -0.0001221872167519367
objective_eval_public         -0.000057274645025334496
source_holdout_public         -0.00011099995374568864
new_signature_holdout_public  -0.00004692872365309998
```

Note: this recheck reconstructs snapshots under the candidate checkpoint. The
fixed-tensor comparison remains the M891 interpolation artifact; this recheck is
an additional no-update consistency check.

## Replay Proof Gates

Run:

```text
runs/m893_m891_a010_replay_proof_gate
```

All six replay/proof surfaces passed:

```text
surface    rows  baseline_drops  candidate_drops  normal_margin_delta  margin_gap_delta  pass
M183/M168  16    0               0                +0.0000327358        +0.0000000131    true
M183/M170  17    0               0                +0.0000344530        +0.0000000083    true
M193/M189  14    0               0                +0.0000877746        -0.0000000184    true
M212/M204  17    0               0                +0.0000913554        -0.0000000222    true
M223/M219  17    0               0                +0.0000913551        -0.0000000205    true
M267/M264  17    0               0                +0.0000913302        -0.0000000275    true
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
runs/m893_m891_a010_behavior_seed9505
runs/m893_m891_a010_behavior_seed9506
```

Per seed:

```text
seed  policy     success  termination  clearance_mean  return_mean
9505  m568_base  0.8125   0.1875       1.465080        69.604261
9505  m891_a010  0.8125   0.1875       1.465568        69.600267
9506  m568_base  0.8125   0.1875       1.479410        69.919597
9506  m891_a010  0.8125   0.1875       1.479903        69.915572
```

Aggregate candidate minus base:

```text
success_rate_delta: 0.0
termination_rate_delta: 0.0
min_clearance_margin_mean_delta: +0.0004909103515290392
return_mean_delta: -0.004009246678577938
```

Diagnostics:

```text
m891_a010_reset success_mean: 0.8125
m891_a010_zero_all success_mean: 0.7250
```

Behavior retention passes versus M568. The reset/zero-all rows remain diagnostic
only, not promotion evidence.

## Interpretation

M893 is a fresh-seed repeat proof-gate positive:

```text
M891 alpha_0_1 preserves M568-relative exact objective metrics, all six
closed-loop replay/proof surfaces, and behavior seeds 9505/9506.
```

Together with M889, this supports a narrow claim:

```text
The no-PPO enriched pair-delta objective-only recipe has repeated exact and
replay/proof retention across two optimizer/minibatch seeds.
```

Unsupported claims:

- public-gate driver promotion;
- meaningful driver-performance improvement;
- source/generalization robustness beyond the public replay and behavior rows;
- PPO continuation safety;
- evidence that the current update size is large enough to materially change
  broad closed-loop behavior.

## Decision

Decision:

```text
v4_enriched_pair_delta_fresh_seed_replay_proof_gate_pass
```

Next:

```text
m894-v4-pair-delta-objective-probe-branch-synthesis
```

M894 should synthesize M885-M893 before any further narrow repeat,
generalization gate, PPO, or promotion work.
