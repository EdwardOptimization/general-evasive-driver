# M1201 Paper-Route Profile Separability Audit

## Summary

M1201 audits whether the M1199 L0/L1/L2/L3 profile families are meaningfully
separated before running a longer comparison.

Decision:

```text
profile_separability_audit_route_to_profile_control_repair_design
```

The profile configs and L2 observation stacks are not broken, but M1199 still
has two important interpretation problems:

```text
1. L2 finite-window policies are almost insensitive to replacing older frames with the current frame.
2. M1199 did not enforce the L3_reset_control every-step hidden reset during external public eval.
```

So the next step should repair the diagnostic controls before more training.

## Artifacts

```text
runs/m1201_profile_separability_audit/summary.json
runs/m1201_profile_separability_audit/config_summary.csv
runs/m1201_profile_separability_audit/observation_stack_diversity.csv
runs/m1201_profile_separability_audit/l2_older_history_action_sensitivity.csv
runs/m1201_profile_separability_audit/l3_hidden_action_sensitivity.csv
```

Run-level guardrails:

```text
training_started: false
ppo_started: false
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_specific_tuning: false
paper_level_claimed: false
self_identification_claimed: false
```

## Config Separability

The generated configs differ as intended:

| Profile | Encoder | History | Observation Dim | Recurrent Sequence Training | Reset Policy |
| --- | --- | ---: | ---: | --- | --- |
| `L0_current_masked` | `mlp` | 1 | 72 | false | `not_applicable` |
| `L1_one_step` | `mlp` | 1 | 72 | false | `not_applicable` |
| `L2_window_13` | `temporal_gru` | 13 | 936 | false | `per_decision_window` |
| `L2_window_25` | `temporal_gru` | 25 | 1800 | false | `per_decision_window` |
| `L2_window_50` | `temporal_gru` | 50 | 3600 | false | `per_decision_window` |
| `L2_window_100` | `temporal_gru` | 100 | 7200 | false | `per_decision_window` |
| `L3_online_gru` | `human_view_online_gru` | 1 | 72 | true | `episode_persistent` |
| `L3_reset_control` | `human_view_online_gru` | 1 | 72 | false | `every_step_control` |

This rules out a simple config-generation collapse.

## L2 Observation Stack Audit

Under a deterministic excitation rollout, L2 history stacks contain distinct
older frames:

| Profile | History | Current-Oldest L2 | Adjacent L2 Mean | Nonidentical |
| --- | ---: | ---: | ---: | --- |
| `L2_window_13` | 13 | 1.1029 | 0.1017 | true |
| `L2_window_25` | 25 | 2.0866 | 0.0996 | true |
| `L2_window_50` | 50 | 1.9977 | 0.0783 | true |
| `L2_window_100` | 100 | 2.0825 | 0.0569 | true |

This rules out the environment returning identical history frames after
rollout.

## L2 Older-History Action Sensitivity

For trained M1199 L2 checkpoints, actions were compared against two
older-history ablations on public states:

```text
older_tiled: replace frames 1..N with the current frame
older_zeroed: replace frames 1..N with zeros
```

Overall action L2 differences:

```text
older_tiled_action_l2_mean_overall: 0.001374
older_zeroed_action_l2_mean_overall: 0.060810
```

Interpretation:

```text
The L2 policies react to impossible zeroed histories, but they barely change when older frames are replaced by plausible current-frame copies.
```

Classification:

```text
current_frame_substitution_risk_high
```

Therefore M1199 does not prove that finite-window history itself caused the L2
advantage. The advantage may come from temporal-GRU encoder capacity or another
architecture effect rather than older command-response history.

## L3 Hidden-State Audit

Action-level normal-vs-reset-hidden differences are nonzero but modest:

```text
L3_online_gru normal_vs_reset_action_l2_mean: 0.044612
L3_reset_control normal_vs_reset_action_l2_mean: 0.041186
```

This says L3 hidden state can influence actions. It does not say hidden state
improved M1199 behavior.

More importantly, M1199's external evaluation did not enforce the
`L3_reset_control` config's `every_step_control` reset policy. The evaluator
carried hidden state for all online recurrent actor checkpoints.

Classification:

```text
metric_artifact_for_l3_reset_control_diagnostic
```

This does not invalidate the seven main-profile M1199 runs, but it invalidates
the literal reset-control parity interpretation. The reset diagnostic must be
rerun with evaluation semantics that honor the profile reset policy.

## Route Decision

Do not run a longer M1199-style comparison yet.

Next route:

```text
m1202-paper-route-profile-control-repair-design
```

M1202 should design two repairs:

```text
1. evaluator/runtime support for reset_hidden_policy during public eval;
2. a capacity-matched current-tiled L2 control, so L2 history can be separated from temporal-GRU encoder capacity.
```

Only after those controls exist should the project repeat the public profile
comparison or increase training budget.

## Unsupported Claims

M1201 does not support:

```text
L2 promotion
paper-level architecture ranking
finite-window history necessity
GRU recurrent-belief advantage
self-identification
private-holdout generalization
real-vehicle transfer
```

## Next Milestone

```text
experiments/manifests/m1202-paper-route-profile-control-repair-design.json
```
