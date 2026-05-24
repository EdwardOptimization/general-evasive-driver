# M708 Cross-Fault Wrong-History Scenario Audit

## Purpose

M708 audits the M707 `cross_fault_reset_only` result before any source export,
actor update, PPO, or further scenario mining.

This milestone is process-only:

```text
no rerun
no source corpus export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M707 implementation was clean:

```text
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M707 generated:

```text
scenario_count:       9728
snapshot_count:      33026
matched_pair_count:   2048
unmatched_rows:        307
```

Outcome:

```text
accepted_rows:                         0
reset_only_rows:                      15
history_action_critical_rows:         15
wrong_history_action_critical_rows:    0
reset_history_action_critical_rows:   15
result_class: cross_fault_reset_only
```

The result is not source-positive:

```text
wrong_history_source_positive: false
```

## Action And Margin Diagnostics

Across all `2048` matched cross-fault pairs:

```text
wrong action L2 gap:
  mean: 0.0015866
  p90:  0.0031907
  p95:  0.0052390
  p99:  0.0092222
  max:  0.0132044

reset action L2 gap:
  mean: 0.0202284
  p90:  0.0233178
  p95:  0.0258423
  p99:  0.0297164
  max:  0.0330144

wrong margin gap:
  mean: -0.00000114
  p99:   0.00011459
  max:   0.00034936

reset margin gap:
  mean: 0.00017749
  p99:  0.01652604
  max:  0.03678615
```

Threshold counts:

```text
wrong action gap >= 0.015:        0
wrong margin gap >= 0.02:         0
wrong both thresholds:            0
reset action gap >= 0.015:     2014
reset margin gap >= 0.02:        11
reset both thresholds:           11
```

This is stronger than merely saying "no wrong-history row passed." The wrong
history branch does not even reach the action-divergence threshold, while
reset-hidden often changes the first action.

## Fault-Pair Concentration

Reset-only evidence concentrates around front lateral authority and steering or
combined faults:

```text
front_lateral_authority_drop -> steering_fault:
  rows: 194
  reset_only_rows: 11

front_lateral_authority_drop -> combined_fault:
  rows: 48
  reset_only_rows: 2

steering_fault -> front_lateral_authority_drop:
  rows: 203
  reset_only_rows: 1

combined_fault -> front_lateral_authority_drop:
  rows: 56
  reset_only_rows: 1
```

Wrong-history gap stays near zero even in these groups. That means the useful
signal is not "front versus steering wrong history produces the wrong maneuver";
the useful signal is currently narrower:

```text
resetting recurrent state can perturb action and sometimes margin under
front/steering extreme faults.
```

## Supported Claims

M708 supports:

```text
1. The current harness can generate broad current-model extreme fault data.

2. M704 and M707 both find recurrent-state dependence through reset-hidden
   interventions.

3. Front lateral authority and steering-fault contrasts are the most promising
   current-model region for further history analysis.

4. Current single-track fault proxies are useful diagnostics but not sufficient
   yet for wrong-history self-ID evidence.

5. True single-wheel/asymmetric failures remain future four-wheel or
   high-fidelity vehicle dynamics work.
```

## Falsified Claims

M708 falsifies:

```text
1. Nominal-vs-fault history pairing is the only reason wrong-history rows were
   absent in M704.

2. Simple cross-fault pairing over current-model extreme faults is sufficient
   to produce wrong-history-critical rows.

3. Larger current-model extreme scenario coverage alone is enough to validate
   closed-loop self-identification.

4. Reset-hidden degradation is equivalent to wrong-history capability-belief
   evidence.
```

M708 does not falsify:

```text
the overall ideal driver hypothesis
```

because the actor was not trained with a cross-fault self-ID objective and the
current model still lacks asymmetric wheel-level failures.

## Failure Taxonomy Summary

Primary:

```text
metric_artifact
```

Reason:

```text
Reset-only rows are real recurrent-state evidence, but treating them as
wrong-history self-ID rows would overclaim the metric.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
Cross-fault scenario coverage increased substantially, but the generated wrong
histories still do not create action or outcome divergence.
```

Not classified as:

```text
training_instability:
  no training occurred

contract_violation:
  actor observations were unchanged

proof_washout:
  actor parameters were unchanged
```

## Public Gate Overfit Risk

The active overfit risk is now:

```text
reset-hidden overclaiming
```

A policy can be reset-sensitive because the hidden state is part of recurrent
state continuity, without encoding a useful fault-specific belief. Therefore
the next gate should not optimize for more reset-only rows. It should localize
why wrong histories are action-indistinguishable:

```text
raw hidden state gap
next hidden state gap
fusion feature gap
policy action gap
closed-loop margin gap
```

## Next Branch Decision

Synthesis decision:

```text
continue
```

Continue branch:

```text
extreme_hidden_condition_scenario_generation
```

Next evidence axis:

```text
G_history_incompatibility_localization:
determine whether M707 wrong histories are already similar in raw recurrent
state, whether their signal is washed out at fusion/action, or whether current
visible state dominates the policy.
```

Next blocker:

```text
m709-cross-fault-hidden-action-gap-audit-design
```

M709 should design a no-training audit that reruns or extends the M707
cross-fault pairing export to capture hidden/action separability:

```text
normal hidden vs wrong hidden raw L2
normal next-hidden vs wrong next-hidden L2
fused policy feature L2
first action L2
short closed-loop margin gap
front/steering reset-only rows as focused sentinels
```

Source export, actor update, PPO, and promotion remain blocked.
