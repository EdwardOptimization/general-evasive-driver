# M1213 Paper-Route Corrected Profile Repeat Result Audit

## Summary

M1213 compares the two corrected public seed blocks:

```text
M1209: training_seed_base 110600, eval_seed_base 120600
M1212: training_seed_base 111600, eval_seed_base 121600
```

Decision:

```text
corrected_profile_repeat_audit_route_to_branch_synthesis
```

No training, PPO, candidate replay, promotion, private holdout, profile tuning,
or actor-input change occurs in M1213.

## Cross-Block Validity

Both runs are valid public diagnostics:

```text
M1209 completed_seed_runs: 24
M1212 completed_seed_runs: 24
M1209 all_eval_metrics_finite: true
M1212 all_eval_metrics_finite: true
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
```

The comparison is still public pilot evidence only. It cannot be promoted to
private generalization, paper-level ranking, recurrent-belief proof, or
self-identification proof.

## Aggregate Comparison

Success / collision / mean margin:

| Profile | M1209 | M1212 |
| --- | ---: | ---: |
| `L0_current_masked` | 0.1406 / 0.7135 / 0.2349 | 0.2240 / 0.6250 / 0.3540 |
| `L1_one_step` | 0.1406 / 0.7396 / 0.1747 | 0.3385 / 0.5156 / 0.4758 |
| `L2_window_13` | 0.1302 / 0.8073 / 0.0622 | 0.4062 / 0.4792 / 0.5237 |
| `L2_window_13_current_tiled` | 0.1094 / 0.8021 / 0.1041 | 0.4271 / 0.4427 / 0.6153 |
| `L2_window_25` | 0.1198 / 0.8177 / 0.0620 | 0.4115 / 0.4740 / 0.5240 |
| `L2_window_25_current_tiled` | 0.1146 / 0.7969 / 0.1050 | 0.4271 / 0.4427 / 0.6191 |
| `L3_online_gru` | 0.3594 / 0.5729 / 0.4966 | 0.1875 / 0.8073 / 0.1225 |
| `L3_reset_control_corrected` | 0.3594 / 0.5625 / 0.4562 | 0.1354 / 0.8646 / 0.0651 |

## Stable Findings

### L2 History Necessity

Classification:

```text
stable_negative_for_finite_window_history_necessity
```

Reason:

```text
M1209: normal L2 does not beat current-tiled controls on safety margins.
M1212: current-tiled controls beat normal L2 on success, collision, and mean margin.
```

This is the most stable finding from the corrected profile branch. The earlier
M1199 L2 trend should not be interpreted as finite-window history use.

### Current-Tiled Control Value

Classification:

```text
current_tiled_controls_are_required_for_future_profile_claims
```

Reason:

```text
Without current-tiled controls, the finite-window temporal-GRU capacity can be mistaken for history use.
```

## Unstable Findings

### L3 Architecture Family

Classification:

```text
unstable_L3_family_ranking
```

Reason:

```text
M1209: L3 family is strongest overall.
M1212: L2/current-tiled family is strongest overall and L3 family is weak.
```

The L3 family can train into a strong controller, but the profile-ranking claim
is not stable across the two public seed blocks.

### L3 Online vs Corrected Reset

Classification:

```text
weak_positive_for_online_vs_reset_in_M1212
inconclusive_across_blocks
not_self_identification_evidence
```

Reason:

```text
M1209: online and reset tie on success and termination.
M1212: online beats reset in aggregate success, collision, and mean margin.
Across blocks, the signal is not stable enough for recurrent-belief or self-ID claims.
```

The right next step is not another blind profile pilot. If the project wants to
test recurrent memory, it needs stronger causal history gates or tasks that make
online memory necessary.

## Decision

Do not promote a profile and do not run private holdout.

Do not run another immediate public repeat unless synthesis identifies a
specific unresolved question. The profile branch has already answered one
important question:

```text
L2 finite-window trend is not history-necessity evidence.
```

It has not answered:

```text
whether online recurrent hidden state is causally necessary;
whether a profile can support paper-level generalization;
whether this architecture should be the final driver.
```

## Next Milestone

```text
experiments/manifests/m1214-paper-route-corrected-profile-evidence-synthesis.json
```

M1214 should synthesize M1199-M1213 and choose the next branch. The likely
options are:

```text
1. stop repeated profile pilots and move to causal history gates;
2. repair the task/curriculum if memory is never needed;
3. design a smaller targeted online-vs-reset causal gate;
4. only repeat again if a specific uncertainty remains and the value is high.
```
