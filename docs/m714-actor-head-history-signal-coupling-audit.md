# M714 Actor-Head History-Signal Coupling Audit

## Purpose

M714 audits the M713 `actor_head_coupling_positive` diagnostic before any
objective design, actor update, PPO, or promotion.

This milestone is process-only:

```text
no rerun
no source export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M713 implementation was clean:

```text
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

M713 generated:

```text
scenario_count:       9728
snapshot_count:      33026
matched_pair_count:   2048
row_count:            4096
wrong_rows:           2048
reset_rows:           2048
```

Main result:

```text
result_class: actor_head_coupling_positive
actor_head_coupling_positive: true
```

Positive criteria:

```text
wrong_low_alpha_rows:           164
required low-alpha rows:         30
unique_low_alpha_fault_pairs:    20
required unique fault pairs:      4
```

Alpha line-search:

```text
wrong rows crossing by alpha <= 2:    67
wrong rows crossing by alpha <= 4:   164
wrong rows crossing by alpha <= 8:   504
wrong rows crossing by alpha <= 16: 1079
```

## What The Positive Result Means

M713 shows that the M710 fused wrong-history feature directions are not
intrinsically useless:

```text
f_alpha = f_normal + alpha * (f_wrong - f_normal)
```

For a source-diverse subset, moderate feature-delta amplification crosses the
action threshold:

```text
||tanh(actor_mean(f_alpha)) - tanh(actor_mean(f_normal))|| >= 0.015
```

This supports a new objective-design path:

```text
make the policy or an auxiliary residual head use existing history-sensitive
feature directions more strongly while preserving normal-history behavior.
```

It also means the previous `action_washout` diagnosis should not be treated as
an architectural impossibility. The actor head can respond to the feature
directions; the remaining question is whether the project has enough
closed-loop scenarios where those directions must matter without artificial
amplification.

## What It Does Not Mean

M713 does not prove:

```text
the deployed actor already uses wrong-history belief
closed-loop margin improves
the alpha-amplified counterfactual action is safe
PPO is admissible
a checkpoint should be promoted
current extreme-fault coverage is complete
```

The positive rows are feature-counterfactual diagnostics. They are not deployed
policy rollouts.

M713 also does not rule out the coverage hypothesis:

```text
the current M704/M707 extreme-fault corpora may still be too narrow or too
single-track-proxy-limited to expose the hardest self-identification cases.
```

## Supported Claims

M714 supports:

```text
1. M710 action washout is not a hard actor-head null-space result.

2. Wrong-history fused directions can affect the actor head under moderate
   amplification in a source-diverse subset.

3. Tanh saturation is not the primary blocker:
   wrong tanh attenuation mean is 0.955513, reset is 0.936245.

4. The current blocker is before or at feature-to-action coupling strength:
   wrong feature deltas are smaller and less projected than reset.

5. A conservative exact objective or frozen residual-head design is now a
   reasonable next diagnostic.
```

## Falsified Claims

M714 falsifies:

```text
1. Current cross-fault wrong-history feature directions can never influence
   action.

2. Tanh saturation explains M710 action washout.

3. M713 justifies direct PPO or promotion.
```

M714 does not falsify:

```text
1. The project may need broader extreme-fault coverage before turning the
   diagnostic into an objective.

2. Single-wheel/asymmetric failures may require a four-wheel model or an
   explicit current-model proxy boundary before they can be used as evidence.
```

## Failure Taxonomy Summary

Primary:

```text
none
```

Reason:

```text
M713 is a positive diagnostic and implementation-clean.
```

Residual caution:

```text
metric_artifact risk remains if feature-line-search positives are treated as
deployed behavior.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observations were unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Public Gate Overfit Risk

The active risk is:

```text
counterfactual-amplification overclaiming
```

An amplified feature-direction action can cross a threshold without being safe
or useful in closed-loop replay. Future gates must require:

```text
normal-history retention
wrong-history action separation
closed-loop replay admission
behavior-sentinel non-regression
```

before any actor update, PPO, or promotion.

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Close immediate actor-head localization branch:

```text
actor_head_history_signal_coupling
```

The actor-head result is positive enough to stop localizing the action-washout
mechanism for now, but not strong enough to mutate the actor. The next highest
leverage step is to register a broader extreme-fault coverage refresh before
choosing between objective design and more data mining.

Next branch:

```text
extreme_fault_coverage_refresh
```

Next evidence axis:

```text
G_scenario_coverage:
test whether missing extreme fault families, severities, activation timings,
and current-model proxy boundaries explain why wrong-history interventions have
not yet produced strong closed-loop outcome gaps.
```

Next blocker:

```text
m715-extreme-fault-coverage-refresh-design
```

M715 should design a no-training coverage refresh:

```text
current-model fault taxonomy
current-model proxy taxonomy
future four-wheel-only fault boundary
full data wave config and M716 run plan
normal/reset/wrong/delayed-history evaluation rules
no checkpoint promotion
```

Direct PPO and base actor mutation remain blocked.

The deferred actor-head objective path remains admissible after the coverage
refresh:

```text
base actor frozen
normal-history target: zero residual / no action drift
wrong-history target: alpha-derived action residual for low-alpha rows
exact gates before any closed-loop replay
no checkpoint promotion
```
