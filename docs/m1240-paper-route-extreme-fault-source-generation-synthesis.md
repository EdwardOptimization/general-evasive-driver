# M1240 Paper-Route Extreme Fault Source-Generation Synthesis

## Summary

M1240 synthesizes the `paper_route_extreme_fault_source_generation` branch from
M1232 through M1239.

Decision:

```text
extreme_fault_source_generation_synthesis_promote_to_capability_separable_source_construction
```

The current source path should stop. It produced useful infrastructure and
negative evidence, but it did not expose history-necessity signal. The next
branch should construct or mine capability-separable sources where hidden
dynamics demonstrably require different actions under matched current
observations.

No new experiment, training, PPO, checkpoint repair, promotion, private holdout,
profile tuning, actor-input expansion, or self-identification claim occurs in
M1240.

## Evidence Summary

M1232 designed the branch:

```text
current-model/proxy fault families specified
future high-fidelity-only fault claims separated
actor-input guardrails specified
source-diversity gates specified
```

M1233 ran the first smoke:

```text
result_class: cross_fault_reset_only
scenario_count: 832
snapshot_count: 3211
matched_pair_count: 768
accepted_rows: 0
reset_only_rows: 58
normal_failed_rejected: 636
```

M1234 audited that smoke:

```text
classification: normal_failure_dominated_reset_only_source_shape
decision: repair timing/horizon before scaling
```

M1235 designed timing repair:

```text
target normal_surviving_fraction: 0.35
max_continuation_steps: 36 -> 18
source window adjusted
fault families unchanged
```

M1236 ran the repaired smoke:

```text
result_class: history_insensitive_too_mild
normal_surviving_fraction: 0.7213541667
matched_pair_count: 768
accepted_rows: 0
reset_only_rows: 0
history_insensitive_rejected: 554
```

M1237 designed sequence interventions:

```text
source: M1236 history-insensitive normal-surviving rows
variants: delayed history, reset-warm, zero-command, cross-fault response,
          wrong commands, wrong response
```

M1238 ran the sequence probe:

```text
result_class: sequence_no_signal
selected_source_rows: 384
intervention_rows: 6912
variant_count: 6
accepted_sequence_rows: 0
sequence_action_critical_rows: 0
```

M1239 audited the negative:

```text
classification: same_source_sequence_no_signal
decision: synthesize before continuing
```

## Supported Claims

Supported engineering claims:

```text
The current paper-route L3 checkpoint is compatible with the hidden
capability-step/fault source harness.

The branch preserves the P0 human-view/no-oracle actor contract.

The current single-track model can express useful current-model/proxy hidden
capability changes, while true per-wheel/asymmetric fault claims remain blocked.

Normal-history survivability can be repaired by shorter continuation and safer
source windows.

The sequence intervention probe runs successfully on repaired sources without
trace reconstruction failures.
```

Supported negative scientific claim:

```text
For this current-model/proxy fault source path and current checkpoint, neither
single cross-fault hidden-state swaps nor the tested command-response sequence
interventions expose action- or outcome-critical history dependence.
```

## Falsified Or Blocked Claims

Falsified for this branch:

```text
The M1236 repaired extreme/fault source distribution is sufficient to expose
history dependence with the existing sequence intervention probe.
```

Blocked:

```text
source-diverse cross-fault wrong-history proof
temporal-history sequence proof
history necessity
recurrent belief
online self-identification
training readiness
PPO readiness
promotion
paper-level result
true per-wheel/asymmetric fault physics in the current model
```

## Failure Taxonomy Summary

Observed failure modes:

```text
scenario_sampling_failure:
  M1233 had many normal-failed rows.
  M1236 repaired normal survival but left only history-insensitive rows.
  M1238 sequence interventions produced no action-critical or outcome-critical
  rows.

none:
  M1232, M1235, and M1237 were design/process milestones.
  M1236 passed the normal-survival repair gate.
```

Not observed:

```text
contract_violation
training_instability
proof_washout
promotion_gate_failure
private_holdout_contamination
```

## Public Gate Overfit Risk

Risk level:

```text
high if the branch continues with more same-source variants
```

Reasons:

```text
The M1236 source distribution has already been used for hidden-swap and sequence
intervention tests.

M1238 tried six variants and three history lengths with zero action-critical
rows.

Lowering thresholds or adding nearby variants would likely optimize the harness
instead of revealing a real mechanism.
```

Mitigation:

```text
Close this source path and pivot to a source-construction branch that first
proves hidden dynamics require different actions before testing the RL actor.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
paper_route_extreme_fault_source_generation
```

Open:

```text
paper_route_capability_separable_source_construction
```

The next branch should answer a more primitive question:

```text
Does the simulator contain matched-current hidden-dynamics cases where the
right action or short action sequence is genuinely different?
```

The proposed M1241 design should use offline/privileged source construction,
not actor inputs:

```text
1. sample matched-current scene/ego states under different hidden dynamics;
2. search a small action or action-sequence lattice for terminal margin;
3. accept pairs only if the best action for hidden condition A is bad for B, or
   vice versa;
4. record oracle/source labels as metadata only;
5. then test whether the human-view recurrent actor has or lacks the needed
   history signal.
```

This is not a rule controller and not a deployable actor input. It is a source
validity test: before asking whether RL self-identifies, prove that the source
actually requires self-identification.

## Decision

```text
extreme_fault_source_generation_synthesis_promote_to_capability_separable_source_construction
```

M1241 should design the capability-separable source-construction branch before
any new source mining, objective, PPO, or training.
