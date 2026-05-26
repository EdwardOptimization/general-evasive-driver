# M993 V4 Public Base Capability-Step Sequence Intervention Design

## Purpose

M993 designs the next no-training probe after M992 showed that M991 is
`cross_fault_reset_only`.

The key diagnosis from M992:

```text
wrong-history hidden swaps are usually too compatible:
  wrong action_l2 p50: 0.0
  wrong margin gap mean: 0.000006

reset-hidden is a large intervention:
  reset action_l2 p50: 0.811984
  reset margin gap mean: 0.030334
```

So the next step should not be more single hidden-state swaps or PPO. It should
test stronger sequence-level command-response interventions while preserving
the P0 actor contract.

M993 is design-only:

```text
no code change
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Design Goal

Convert broad reset-only evidence into a cleaner causal test:

```text
If the recurrent state encodes a belief over current vehicle capability, then a
short incompatible command-response history should change the action sequence
and reduce terminal margin or success when injected into a matched current
state.
```

This is stricter than reset-hidden:

```text
reset-hidden:
  tests whether recurrence matters at all

sequence-level mismatch:
  tests whether a plausible but wrong recent command-response history changes
  the policy's capability belief in a behaviorally meaningful way
```

## Why Existing Artifacts Are Not Enough

M991 writes matched-pair CSVs and rollout summaries, but it does not store full
pre-snapshot observation/hidden windows. A sequence-level intervention needs
the preceding window:

```text
o_{t-K:t}
h_{t-K:t}
actions_{t-K:t-1}
actuator states_{t-K:t}
fault metadata for reconstruction/logging only
```

Therefore M994 should implement a small trace-window probe rather than trying
to reinterpret the existing CSVs as full sequence data.

## M994 Implementation Shape

Add a no-training runner:

```text
src/autodrift/capability_step_sequence_intervention_probe.py
```

Inputs:

```text
checkpoint:
  runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt

scenario config:
  configs/m991_capability_step_fault_source_wave.json

source rows:
  runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv

mode:
  cross_fault sequence intervention
```

The runner should reconstruct selected seed/fault scenarios, record trace
windows around reset-only rows, and replay no-training interventions.

Suggested command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv \
  --max-source-rows 384 \
  --per-fault-pair-cap 48 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m994_v4_public_base_capability_step_sequence_intervention_probe
```

## Candidate Interventions

### 1. Delayed Capability History

Use the same scenario's hidden/observation window from before the capability
step or before enough response evidence has accumulated.

Purpose:

```text
Tests whether the policy needs recent post-fault response evidence rather than
just the current visible state.
```

Expected result:

```text
delayed history should be worse than normal only when post-fault response
evidence is behaviorally relevant.
```

### 2. Cross-Fault Response Window

Use a short hidden-state warmup built from the wrong fault's recent
command-response observation window, then execute on the preferred current env.

Purpose:

```text
Creates a plausible wrong capability belief rather than a single hidden-vector
swap.
```

This is the main M994 intervention.

### 3. Action-Response Mismatch Window

Build a synthetic history window by combining:

```text
commands/action-history channels from one fault family
ego response/actuator channels from another fault family
```

Purpose:

```text
Tests whether the response encoder is sensitive to command-response consistency,
not just hidden-state identity.
```

Use only deployable observation channels. Hidden fault labels are metadata, not
actor inputs.

### 4. Zero Command History Window

Zero recent previous-command channels while keeping ego response and scene
context.

Purpose:

```text
Tests whether command-response attribution, not response alone, drives the
reset-only sensitivity.
```

### 5. Reset Then Warm History

Reset hidden at `t-K`, then feed the actual preferred observation window for
`K` steps before the decision.

Purpose:

```text
Separates generic reset disruption from missing recent command-response
evidence.
```

If `reset_then_warm_history` recovers normal behavior quickly, the recurrent
state only needs a short evidence window. If it remains bad, longer memory or
hidden continuity is important.

## Implementation Constraints

The probe must:

```text
not train;
not call optimizer.step;
not run PPO;
not promote;
not change actor inputs;
not put fault family/severity/activation step into policy observations;
not count reset-only rows as accepted wrong-history rows;
not claim true per-wheel/asymmetric faults.
```

Use fault labels only for:

```text
row selection
source balancing
CSV metadata
diagnostic grouping
```

## Acceptance Metrics

For each source row and intervention:

```text
normal_success
intervention_success
success_drop
normal_margin
intervention_margin
margin_gap = normal_margin - intervention_margin
first_action_l2
sequence_action_l2_mean
sequence_action_l2_max
terminal_reason
fault_pair
seed
history_length
intervention_type
```

Primary acceptance:

```text
normal_success == true
normal_margin >= 0
and (
  success_drop == true
  or margin_gap >= 0.012
)
and sequence_action_l2_mean >= 0.025
```

Separate result classes:

```text
sequence_wrong_positive:
  source-diverse accepted sequence rows exist

sequence_action_only:
  sequence actions differ but terminal margins do not

sequence_reset_only:
  reset variants remain dominant and cross-fault sequence variants fail

sequence_no_signal:
  neither action nor outcome changes meaningfully

sequence_artifact:
  normal rows fail, actor checksum changes, or input contract is violated
```

## Source Diversity Gates

M994 is a probe, not a promotion gate. Still report:

```text
accepted_sequence_rows
accepted_sequence_fault_pairs
accepted_sequence_seeds
max_accepted_seed_fraction
max_accepted_fault_pair_fraction
reset_then_warm_recovery_rate
```

Suggested source-positive thresholds for later larger wave:

```text
accepted_sequence_rows >= 40
accepted_sequence_fault_pairs >= 6
accepted_sequence_seeds >= 12
max_accepted_seed_fraction <= 0.30
max_accepted_fault_pair_fraction <= 0.45
```

M994 smoke may report these without requiring them.

## Route After M994

If sequence interventions produce source-diverse accepted rows:

```text
route to sequence corpus export and exact objective sanity
```

If sequence interventions are action-only:

```text
route to terminal-margin-grounded sequence target redesign
```

If sequence interventions remain reset-only:

```text
synthesize the capability-step branch and consider simulator/dynamics
extensions, especially asymmetric/four-wheel faults
```

If trace reconstruction is the blocker:

```text
implement a minimal trace-window exporter first
```

## Decision

Admit:

```text
m994-v4-public-base-capability-step-sequence-intervention-probe
```

M994 should be no-training and should not promote. Its purpose is to determine
whether sequence-level intervention can convert reset-only evidence into clean
wrong-history/action-response self-identification evidence.
