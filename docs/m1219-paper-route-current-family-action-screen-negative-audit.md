# M1219 Paper-Route Current-Family Action-Screen Negative Audit

## Summary

M1219 audits the M1218 negative wrong/delayed history action screen and selects
the next route.

Decision:

```text
negative_action_screen_admit_hidden_action_sensitivity_probe
```

No evaluation rollout, outcome intervention, training, PPO, checkpoint repair,
promotion, private holdout, profile tuning, or actor-input change occurs in
M1219.

## Evidence Reviewed

M1218 screened the M1217 current-family matched-current surface:

```text
input matched pairs:        762
intervention rows:         3810
variant summary rows:        45
```

Aggregate action distances:

| Variant | Mean | P90 | Max | Above Threshold |
| --- | ---: | ---: | ---: | ---: |
| wrong_matched_history | `0.001075` | `0.001946` | `0.002415` | `0` |
| delayed_history | `0.000154` | `0.000160` | `0.015598` | `0` |
| reset_hidden | `0.041795` | `0.076904` | `0.080238` | `629` |
| zero_action_history | `0.013854` | `0.015445` | `0.015767` | `0` |
| zero_current_response | `0.017431` | `0.019126` | `0.021021` | `20` |

No wrong/delayed checkpoint-target group passed:

```text
mean action distance >= 0.01
above-threshold count >= 16
```

## Diagnosis

M1218 creates a specific split:

```text
reset-hidden sensitivity: strong
matched wrong/delayed hidden-history sensitivity: absent
```

This means the recurrent hidden path can influence action, but the current
natural hidden histories chosen by M1217 are action-equivalent for the actor.
Resetting hidden to the initial state is a blunt intervention; it should not be
interpreted as self-identification evidence.

The most likely explanations are:

```text
1. real rollout hidden states are close or action-equivalent even when future
   response targets differ;
2. the actor head uses hidden as a generic offset/calibration but not as a
   history-specific capability belief;
3. M1217 pairs are future-response ambiguous but not action-critical;
4. the current corrected-profile PPO budget trained a mostly reactive policy;
5. wrong-history intervention is too weak or too same-family to expose a
   causal effect.
```

## Rejected Next Step

Do not run `persistent_wrong_history_intervention_gate` now.

Reason:

```text
M1218 was explicitly an admission screen for outcome rollout, and the required
wrong/delayed action signal failed.
```

Running outcome rollout anyway would turn the harness into a search over
post-hoc explanations rather than a pre-registered evidence chain.

## Selected Next Route

The next route should be a hidden-action sensitivity probe, using the existing
tool:

```text
autodrift.bc_hidden_action_sensitivity_probe
```

Despite the module name, the tool is compatible with online-GRU checkpoints and
matched-current pairs. It adds the variants needed to distinguish hidden-path
insensitivity from weak real-history interventions:

```text
reset_hidden
delayed_history
wrong_matched_history
shuffled_history
scaled_hidden_0_5
scaled_hidden_1_5
scaled_hidden_2_0
random_hidden_fit
random_hidden_unit
zero_current_response
zero_action_history
```

M1220 should answer:

```text
Does the current-family actor react to hidden perturbations at all?
If yes, is the response limited to reset/random/scaled off-manifold hidden
states while real wrong/delayed histories stay action-equivalent?
```

Interpretation:

| M1220 Pattern | Meaning | Next Route |
| --- | --- | --- |
| random/scaled and reset strong, wrong/delayed weak | real histories are action-equivalent; mine action-critical pairs or train contrastive hidden use |
| all hidden variants weak | actor head effectively ignores hidden path; objective or architecture repair |
| wrong/delayed become strong under expanded variants | reconsider outcome gate with selected rows |
| zero controls dominate all hidden variants | current-frame/previous-command policy; no self-ID claim |

## Decision

```text
negative_action_screen_admit_hidden_action_sensitivity_probe
```

Next blocker:

```text
m1220-paper-route-current-family-hidden-action-sensitivity-probe
```
