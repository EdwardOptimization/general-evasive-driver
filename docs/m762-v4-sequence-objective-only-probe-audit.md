# M762 V4 Sequence Objective-Only Probe Audit

## Purpose

M762 audits the M761 residual objective-only probe before any closed-loop
residual replay, PPO, checkpoint promotion, or simulator-fidelity claim.

The question is:

```text
Is M761 a clean enough objective-only positive to justify designing a no-PPO
closed-loop residual replay evaluator?
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

M761 result:

```text
result_class: v4_sequence_objective_probe_candidate

positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0

residual_parameter_count: 4355
candidate_alpha_count: 3
candidate_alphas:
  0.2
  0.5
  1.0

actor_backbone_changed: false
residual_only_training: true
ppo_used: false
promoted: false
```

Candidate alpha metrics:

```text
alpha 0.2:
  normal drift mean/p95: 0.000480 / 0.000939
  gap mean/p10: 0.029079 / 0.023874
  gap deficit mean/p95: 0.012637 / 0.016976

alpha 0.5:
  normal drift mean/p95: 0.001200 / 0.002348
  gap mean/p10: 0.035731 / 0.025665
  gap deficit mean/p95: 0.006068 / 0.009633

alpha 1.0:
  normal drift mean/p95: 0.002401 / 0.004697
  gap mean/p10: 0.047347 / 0.028827
  gap deficit mean/p95: 0.000000337 / 0.0
```

All three candidate alphas pass the registered normal-retention and gap-lift
gates. Alpha `0.2` is the most conservative first passing candidate. Alpha
`1.0` almost eliminates the exact first-action gap deficit while still passing
normal-retention gates.

## Stratification Notes

The M761 positive rows are not uniformly distributed:

```text
variant:
  zero_command_obs: 1044
  reset_hidden_each_step: 169

horizon:
  H=8: 565
  H=6: 455
  H=4: 168
  H=2: 25

claim_boundary_level:
  current_model_or_proxy: 1213

hard_negative_available_fraction:
  0.721352
```

Gap by variant:

```text
alpha 0.2:
  reset_hidden_each_step: 0.023100
  zero_command_obs: 0.030047

alpha 0.5:
  reset_hidden_each_step: 0.024952
  zero_command_obs: 0.037476

alpha 1.0:
  reset_hidden_each_step: 0.028058
  zero_command_obs: 0.050470
```

The residual signal is strongest on `zero_command_obs`, which dominates the
corpus. `reset_hidden_each_step` still improves but more weakly. This matters
for the next replay design: it should not only report aggregate success. It
must stratify by intervention variant, horizon, fault family, and source rows.

## Supported Claims

M762 supports:

```text
1. M761 is a clean objective-only positive: reconstruction is complete,
   metadata is present, actor checksum is unchanged, and no PPO/promotion
   occurred.

2. The M755/M758 v4 sequence corpus contains enough signal for a small
   residual head to increase the registered exact intervention gap.

3. The user's coverage-mining hypothesis remains plausible: broader v4
   extreme/proxy coverage produced many sequence outcome rows and then a
   usable actor-coupling signal.

4. A no-PPO closed-loop residual replay design is now admissible.
```

## Falsified Claims

M762 falsifies:

```text
1. The v4 sequence objective has no trainable residual signal.

2. The only way to improve the exact gap is to move normal-history actions
   outside the registered first-action drift gates.

3. M761 was a metadata, reconstruction, or actor-mutation artifact.
```

M762 does not prove:

```text
1. The residual head improves closed-loop success or margin.

2. The residual head preserves old proof surfaces under rollout.

3. PPO is safe.

4. The residual head should become a promoted driver component.

5. Current proxy faults are sufficient for true tire blowout, wheel lock, axle
   break, or four-wheel vehicle-fidelity claims.
```

## Failure Taxonomy Summary

Primary residual risk:

```text
scenario_sampling_failure
```

Reason:

```text
M761 is positive, but hard-negative availability is still only 0.721352 and the
positive rows are dominated by zero_command_obs and long horizons. This does
not invalidate the result; it constrains the next replay design.
```

Other risks:

```text
public_gate_overfit_risk:
  M761 trains and evaluates on the public M755/M758 objective corpus.

closed_loop_unknown:
  exact first-action metrics improved, but no closed-loop replay has evaluated
  residual behavior yet.
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

## Public Gate Overfit Risk

M761 should not be interpreted as a driver result. It is an exact objective
probe on a public corpus. The next design must therefore separate:

```text
objective improvement:
  exact first-action normal-vs-intervention gap improved in M761

closed-loop behavior:
  still untested

promotion:
  blocked
```

The closed-loop replay should compare base and residual alphas without
additional fitting, and it should report failures instead of tuning from the
same replay rows.

## Next Branch Decision

Decision:

```text
promote_to_v4_residual_closed_loop_replay_design
```

M763 should design a no-PPO closed-loop residual replay evaluator that:

```text
1. loads the frozen BC5660 actor plus M761 residual head;
2. evaluates alpha 0.2, 0.5, and 1.0 against base alpha 0.0;
3. replays normal and intervention branches from M755/M761 source metadata;
4. reports success, collision, road departure, spin, margin, terminal reason,
   first-action drift, and sequence-action drift;
5. stratifies by variant, horizon, fault family, source seed, and claim
   boundary;
6. includes sentinel / hard-negative diagnostics where available;
7. blocks PPO and checkpoint promotion.
```

The conservative alpha for first closed-loop evaluation should be `0.2`, but
M763 should also compare `0.5` and `1.0` because they pass exact first-action
gates and may reveal the closed-loop safety/performance tradeoff.
