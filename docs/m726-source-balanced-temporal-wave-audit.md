# M726 Source-Balanced Temporal Wave Audit

## Purpose

M726 audits the M725 source-balanced temporal wave before another run.

The question is:

```text
Was M725 source_balance_blocked because the scenario proposal space is still
too weak, or because the registered selection quotas over-constrained a broad
proposal table?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M725 generated a broad proposal table:

```text
proposal_count: 69591
proposal preferred families: 9
proposal fault-family pairs: 40
```

Top proposal preferred families:

```text
combined_fault:                17465
global_mu_drop:                 8721
mass_cg_shift:                  6580
drive_authority_drop:           6567
brake_authority_drop:           6526
front_lateral_authority_drop:   6446
steering_fault:                 6440
rear_lateral_authority_drop:    6430
delay_noise_fault:              4416
```

The selected table improved seed diversity but did not satisfy the registered
source-balance gate:

```text
selected_pair_count:             2048
selected_pair_target:            4096
unique_selected_seeds:            256
unique_preferred_fault_families:    7
unique_fault_family_pairs:         24
max_seed_dominance:           0.00390625
max_preferred_family_dominance: 0.3125
```

Selected preferred families:

```text
brake_authority_drop:          640
combined_fault:                640
drive_authority_drop:          352
delay_noise_fault:             256
front_lateral_authority_drop:  128
global_mu_drop:                 31
mass_cg_shift:                   1
```

The immediate selection blocker is explicit:

```text
step_bucket 1: 1024
step_bucket 2: 1024
```

The registered `per_step_bucket_cap=1024` plus two populated step buckets
creates a hard `2048` selected-pair ceiling, independent of the much larger
proposal table.

## Temporal Evidence

M725 preserves the temporal action signal:

```text
temporal_action_critical_rows: 1392
unique_temporal_action_seeds:  186
```

The dominant variant remains `mismatch_zero_command_history`:

```text
rows:                         2048
temporal action-critical:     1390
temporal outcome-critical:       0
first action distance mean: 0.021091
first action distance max:  0.033441
margin gap max:            0.005286
```

Reset hidden is similar at the action level:

```text
rows:                     2048
action-critical rows:     1394
first action distance mean: 0.020014
margin gap max:            0.004695
```

Cross-fault wrong hidden remains action-washed-out:

```text
rows:                    2048
action-critical rows:       0
first action distance max: 0.012911
margin gap max:           0.000271
```

Outcome evidence is still absent:

```text
temporal_outcome_critical_rows: 0
unique_temporal_outcome_seeds:  0
sentinel_false_positive_rate:   0.0
```

## Supported Claims

M726 supports:

```text
1. The earlier M719/M722 source concentration concern was real.

2. M725 substantially reduces seed concentration:
   M722 source seeds: 4
   M725 selected seeds: 256

3. M725 did not fail because no broad proposal table exists.
   It generated 69591 proposals across 9 preferred families and 40 family
   pairs.

4. The registered quota design is over-constrained:
   the per-step-bucket cap limits selection to 2048 rows.

5. The command-history action signal survives source balancing.

6. Sentinel false positives remain clean.
```

## Falsified Claims

M726 falsifies:

```text
1. M725 is a successful source-balanced full wave.
   It missed the selected-pair target and family dominance gate.

2. M725 provides closed-loop self-ID outcome proof.
   It has 1392 temporal action-critical rows but 0 outcome-critical rows.

3. M725 justifies source export, actor update, PPO, or promotion.
```

M726 does not falsify:

```text
1. A quota-calibrated full wave may pass the source-balance gate.

2. Boundary mining may still convert source-balanced action rows into
   outcome-critical rows.

3. Sequence-level interventions may still be required after quota calibration.

4. More physical asymmetric faults may still require dynamics-fidelity work.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The run failed the registered source-balance gate, but the immediate cause is
quota overconstraint rather than proposal absence.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
Action-critical temporal rows are not closed-loop outcome proof.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor inputs were unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate.

M725 uses fixed public thresholds and the same v2 extreme-fault configuration.
However, the current result is not a promoted checkpoint and not a policy
claim. It is a data-generation audit. The main risk is repeatedly retuning
source quotas until a preferred family distribution passes while the
closed-loop outcome signal remains zero.

The guardrail for M727 is:

```text
source-balance pass is necessary but not sufficient;
action rows must remain separate from outcome rows;
PPO and source export remain blocked unless a later audited corpus has
outcome-positive rows or a pre-registered lower-level objective claim.
```

## Next Branch Decision

Decision:

```text
continue fresh_source_balanced_temporal_wave with quota calibration
```

Rationale:

```text
The proposal table is broad enough to justify one calibrated rerun.
The selected-pair failure is directly explained by per-step-bucket quota caps.
The action signal survives and is more source-diverse than M722.
```

Do not proceed directly to boundary mining from M725 because the registered
source-balance gate did not pass.

Do not proceed to sequence-level intervention yet because the current blocker
is quota calibration, not a proven exhaustion of source-balanced single-step
temporal action evidence.

Do not proceed to dynamics fidelity yet because the current model still has an
unresolved quota-calibration artifact.

## M727 Requirements

M727 should design a quota-calibrated source-balanced rerun with:

```text
1. `selected_pair_count` target either preserved at 4096 with caps that allow
   it, or explicitly rescaled to a smaller registered target.

2. `per_step_bucket_cap` large enough for the target, or converted to a
   fractional dominance gate instead of a hard ceiling.

3. preferred-family balancing that does not cap the sparse useful families out
   of the selected table.

4. retained per-seed cap and sentinel false-positive checks.

5. separate action and outcome gates.

6. no actor training, no PPO, and no promotion.
```

Recommended M727 target:

```text
selected_pair_count: 4096
per_seed_pair_cap: 8
per_step_bucket_cap: 4096
per_preferred_family_cap: 640
per_fault_family_pair_cap: 256
min_unique_selected_seeds: 256
min_unique_preferred_fault_families: 8
max_preferred_family_dominance: 0.25
```

If the calibrated rerun still finds `0` outcome-critical rows, the next audit
should choose between:

```text
1. source-balanced boundary mining;
2. sequence-level command-response interventions;
3. explicit asymmetric/yaw-disturbance or four-wheel dynamics fidelity.
```
