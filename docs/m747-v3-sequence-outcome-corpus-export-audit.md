# M747 V3 Sequence-Outcome Corpus Export Audit

## Purpose

M747 audits the M746 v3 corpus export before any objective design, actor update,
PPO, checkpoint promotion, or simulator-fidelity claim.

The question is:

```text
Is M746's v3 sequence-outcome corpus clean enough to preserve, and should the
next branch train from it or first broaden extreme-fault coverage?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint loading
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M746 exported a clean positive corpus:

```text
result_class: v3_sequence_outcome_corpus_hard_negative_sparse

positive_rows: 995
positive_sentinel_rows: 0
positive_source_role_sentinel_rows: 0
sentinel_false_positive_rows_exported_as_positive: 0
duplicate_positive_keys: 0
missing_normal_matches: 0
positive_rows_missing_v3_metadata: 0
positive_rows_missing_fidelity_metadata: 0

unique_positive_seeds: 20
unique_positive_fault_family_pairs: 26
max_positive_seed_dominance: 0.169849
max_positive_fault_family_pair_dominance: 0.100503

contrast_groups: 995
normal_rows: 995
positive_intervention_rows: 995
hard_negative_rows: 992
positives_without_hard_negative: 90

positive_corpus_gate_pass: true
v3_metadata_gate_pass: true

training_started: false
optimizer_started: false
checkpoint_loaded: false
ppo_used: false
promoted: false
```

Coverage by variant and horizon:

```text
variant:
  zero_command_obs: 950
  reset_hidden_each_step: 45

horizon:
  H=2: 3
  H=4: 145
  H=6: 370
  H=8: 477
```

Coverage by fault family:

```text
preferred families:
  front_lateral_authority_drop: 135
  combined_fault: 130
  mass_cg_shift: 126
  steering_fault: 120
  brake_authority_drop: 119
  global_mu_drop: 110
  delay_noise_fault: 102
  drive_authority_drop: 102
  rear_lateral_authority_drop: 51

top fault-family pairs:
  delay_noise_fault->brake_authority_drop: 100
  drive_authority_drop->rear_lateral_authority_drop: 95
  steering_fault->front_lateral_authority_drop: 91
  global_mu_drop->front_lateral_authority_drop: 90
  brake_authority_drop->global_mu_drop: 89
```

V3 fidelity boundary:

```text
future_only_fault_count: 12
current_model_fault_count: 12
current_model_proxy_fault_count: 20
preferred_fidelity_classes:
  current_model_proxy: 554
  current_model_fault: 441
wrong_fidelity_classes:
  current_model_proxy: 512
  current_model_fault: 483
```

## Supported Claims

M747 supports:

```text
1. M746 is a valid, auditable, v3-aware positive corpus export.

2. M743's sequence-intervention evidence was not lost: the corpus preserves
   `995` non-sentinel outcome-sensitive rows with matched normal rows.

3. The earlier "maybe we did not mine enough" hypothesis is supported by the
   M740 -> M743 -> M746 chain:
     M740: 744 reset-only rows, 0 wrong-history action rows
     M743: 995 sequence outcome rows
     M746: 995 clean exported positives

4. The current corpus is suitable for later objective-sanity design or repeat
   validation.

5. The corpus should not be treated as a full hard-negative contrast corpus
   because the same-source/same-horizon hard-negative side is sparse.
```

## Falsified Claims

M747 falsifies:

```text
1. The v3 reset-only branch was a dead end.

2. A direct M737-style export is sufficient for v3 evidence; M746 shows that
   v3 source and fidelity metadata must be preserved explicitly.

3. The M746 hard-negative sparsity invalidates the positive corpus.
```

M747 does not prove:

```text
1. A trained driver improves after learning from the M746 corpus.

2. PPO can retain these rows without proof washout.

3. The current single-track proxy faults are true single-wheel blowout,
   split-mu, stuck-caliper, or halfshaft-break physics.

4. The current public corpus is enough for paper-level generalization evidence.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
M746's positive corpus is clean, but the hard-negative contrast set remains
slightly sparse (`992 < 995`) and `90` positives lack a same-source/same-horizon
action-only hard-negative candidate.
```

Residual risks:

```text
public_gate_overfit:
  M746 positives are public diagnostics derived from the same M743 wave.

claim_boundary:
  V3 contains current-model and proxy capability faults, but not true four-wheel
  asymmetric failures.

hard_negative_sparsity:
  Positive-vs-normal objective design remains admissible later, but complete
  positive-vs-action-only contrast design needs repair or a different loss.
```

Not failures:

```text
not contract_violation
not proof_washout
not promotion_gate_failure
not metric_artifact
not training_instability
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate to high if objective work starts
immediately.

Reasons:

```text
1. The `995` positives are all from one public M743 run family.
2. The strongest mechanism is dominated by `zero_command_obs` at long horizons.
3. The corpus is now large enough to overfit if it becomes the next loss target.
4. The user's latest hypothesis explicitly points to insufficient extreme
   scenario coverage.
```

Mitigation:

```text
Preserve M746 as a positive corpus, but do not train from it yet.
First design a v4 extreme-fault coverage branch that separates current-model
faults, current-model proxies, and future four-wheel/high-fidelity faults.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v4_extreme_fault_coverage_design
```

Rationale:

```text
M746 is clean enough to preserve, but the project should not immediately turn
the public v3 corpus into a training objective. The user's concern is now the
coverage axis: wheel blowout, sudden grip loss, split-mu, stuck caliper,
halfshaft/driveline failures, and other asymmetric events.
```

The next branch should design a v4 coverage taxonomy with three claim levels:

```text
current_model_fault:
  directly represented by the existing single-track VehicleParams dynamics.

current_model_proxy:
  useful capability-loss or disturbance proxy for self-ID mining, but not a
  physical single-wheel claim.

future_four_wheel_or_high_fidelity:
  requires four-wheel/contact-patch dynamics, Chrono/BeamNG-like validation, or
  a new dynamics engine before physical claims are allowed.
```

M748 should design the v4 scenario taxonomy and data-wave plan before another
training/objective milestone. It should keep actor training, PPO, and promotion
blocked.

## Allowed Next Steps

Allowed:

```text
1. design v4 extreme-fault coverage taxonomy;
2. design a v4 current-model/proxy data wave;
3. identify which desired faults require four-wheel or high-fidelity dynamics;
4. keep M746 corpus as a preserved public positive corpus for later objective
   sanity or repeat validation.
```

Blocked:

```text
1. PPO from M746;
2. actor update from M746;
3. checkpoint promotion;
4. true per-wheel physics claims from current v3 proxy data;
5. paper-level generalization claims from the public M746 corpus alone.
```
