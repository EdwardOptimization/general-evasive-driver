# M1492 Paper-Route Self-ID Go/No-Go Matrix Design

## Summary

M1492 designs the next paper-route controller-family matrix after M1491 applied
the source-diverse pressure hard stop.

Decision:

```text
self_id_go_no_go_matrix_design_admit_profile_config_refresh
```

This milestone does not train, run PPO, run replay, promote a checkpoint, use
private holdout, export a corpus, or change actor inputs.

## Why The Route Changes

M1491 found that M1490 is replay-positive, but not source-diverse:

```text
actual_replay_rows: 204
actual replay diversity: 5 seeds / 6 capability pairs / 6 reveal buckets
history_positive_rows: 7
history-positive diversity: 1 seed / 1 capability pair / 1 reveal bucket
control_positive_rows: 12
control-positive diversity: 1 seed / 1 capability pair
```

This triggers the M1488 hard stop. The project should not keep retargeting the
same source-diverse pressure branch as if another public replay loop will turn
the local source family into paper-grade self-ID evidence.

The next question is broader and falsifiable:

```text
Does recurrent hidden state add source-diverse, outcome-relevant value beyond
current response and finite-window feedback under fair budgets?
```

## Existing Evidence To Preserve

The matrix starts from existing evidence, not from a blank slate.

M1388/M1389 fixed-budget profile pilot:

```text
L2_window_13 success / collision / margin:              0.56771 / 0.43229 / 0.71303
L2_window_13_current_tiled:                             0.56250 / 0.43750 / 0.70532
L2_window_25:                                           0.55729 / 0.44271 / 0.70168
L2_window_25_current_tiled:                             0.56250 / 0.43750 / 0.70587
L3_online_gru:                                          0.44271 / 0.54688 / 0.49734
L3_reset_control_corrected:                             0.46354 / 0.52604 / 0.51299
```

M1389 classification:

```text
finite_window_history_necessity: not_supported
online_gru_hidden_advantage: not_supported
current_frame_substitution_risk: high
```

M1390-M1398 causal-history branch:

```text
matched-current and warmup-latched source generation works;
reset and zero-current controls expose broad sensitivity;
wrong/delayed warmup-history outcome positives remain zero or source-narrow;
source-diverse level3 self-ID remains unsupported.
```

M1491:

```text
calibrated neighbor replay is live, but positives remain source-singleton and
same-family controls are live.
```

Therefore M1492 treats self-ID as still plausible but unproven, and designs a
matrix that can return a positive, negative, or conditional verdict.

## Controller Families

All controllers must keep the same deployable actuator-level output:

```text
[steer, throttle, brake]
```

All controllers must obey the P0 human-view/no-wheel/no-oracle actor input
contract. Hidden capability labels may be used by samplers, miners, teachers,
and diagnostics only; they must not enter actor input.

### C0: L0 Current

```text
profile: L0_current_masked
input: current 72-dim P0 frame with previous-command fields 9, 10, 11 masked
purpose: lower anchor for current scene/ego-response-only behavior
```

### C1: L1 One-Step

```text
profile: L1_one_step
input: current 72-dim P0 frame, including actuator state and previous commands
purpose: one-step closed-loop feedback baseline
```

### C2: L2 Finite-Window

```text
profiles:
  L2_window_13   approximately 0.26s
  L2_window_25   approximately 0.50s
  L2_window_50   approximately 1.00s
  L2_window_100  approximately 2.00s

input: explicit P0 command-response window
encoder: temporal_gru with finite observation stack
purpose: test whether explicit finite history helps without online recurrent hidden state
```

### C2c: L2 Current-Tiled Capacity Controls

```text
profiles:
  L2_window_13_current_tiled
  L2_window_25_current_tiled
  L2_window_50_current_tiled
  L2_window_100_current_tiled

input: same observation dimension and encoder as matched L2 window, but older
frames are replaced with the current frame
purpose: separate history value from parameter count, unroll length, and current-frame substitution
```

The current code has corrected current-tiled configs for 13 and 25. M1493 must
extend the corrected config generator to include 50 and 100 before a paper-grade
matrix run.

### C3: L3 Online GRU

```text
profile: L3_online_gru
input: current 72-dim P0 frame
memory: episode-persistent online GRU hidden state
purpose: main recurrent belief candidate
```

### C3c: L3 Reset / Truncated Controls

```text
profiles:
  L3_reset_control_corrected
  L3_truncated_0p25s_control
  L3_truncated_0p50s_control

purpose: separate useful recurrent history from architecture or hidden-size effects
```

The corrected every-step reset profile exists. Truncated controls may be added
later only if the reset comparison is inconclusive and the implementation keeps
the same actor input contract.

## Fixed-Budget Matrix Stages

### Stage A: Config And Runtime Readiness

Next milestone:

```text
m1493-paper-route-go-no-go-profile-config-refresh-implementation
```

M1493 should implement or refresh full go/no-go profile configs without
training:

```text
L0_current_masked
L1_one_step
L2_window_13 / 25 / 50 / 100
L2_window_13 / 25 / 50 / 100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Pass requirements:

```text
all configs instantiate;
all forbidden-input flags remain false;
current-tiled controls preserve matched observation dimensions;
L3 reset-control runtime policy is every-step reset;
no training, PPO, promotion, private holdout, replay, or corpus export.
```

### Stage B: One-Seed Plumbing Smoke

Run only after Stage A passes.

Purpose:

```text
confirm all profiles can train/evaluate under the same budget and seed policy
without finite-metric or runtime failures.
```

Interpretation:

```text
plumbing only;
no architecture ranking;
no self-ID claim.
```

### Stage C: Three-Seed Public Matrix

Run only after the one-seed smoke is audited.

Required policy:

```text
same training steps;
same optimizer;
same rollout/env count;
same public eval seeds;
same device class unless pre-registered;
no profile-specific tuning.
```

The public matrix may report trends, but cannot promote a checkpoint or claim
private generalization.

### Stage D: Decisive Task Matrix

Run only after the standard public matrix is complete and audited.

Task families:

```text
T1 reactive emergency avoidance
T2 delayed actuator/response feedback
T3 diagnostic warmup followed by obstacle reveal
T4 same-current, same-recent-window, different-older-history
T5 terminal-boundary near-constraint avoidance
```

T4 and T5 are the decisive self-ID tasks. T1/T2/T3 are important engineering
coverage, but cannot by themselves prove level3 self-ID.

## Metrics

Every matrix run must report:

```text
success_rate
collision_rate
road_departure_rate
spin_or_unstable_rate
clearance_margin_mean
clearance_margin_p10
clearance_margin_min
return_mean
steps_mean
control_smoothness
parameter_count
runtime_seconds
inference_latency_proxy
termination_reason_histogram
```

History-specific metrics:

```text
L2 normal minus L2 current-tiled:
  success_delta
  collision_delta
  mean_margin_delta
  p10_margin_delta

L3 online minus L3 reset/truncated:
  success_delta
  collision_delta
  mean_margin_delta
  p10_margin_delta

Intervention gaps:
  wrong_history_margin_gap
  delayed_history_margin_gap
  reset_hidden_margin_gap
  zero_current_response_margin_gap
  zero_action_history_margin_gap
  first_action_l2
  sequence_action_l2
```

## Verdict Rules

Use the weakest supported verdict.

### Self-ID Positive

Allowed only if all are true:

```text
1. L3 online beats L3 reset/truncated by >= 0.02 success or >= 0.05 p10 margin
   on source-diverse decisive tasks.
2. L3 online is competitive with or better than best L0/L1/L2 controller under
   the same budget on safety metrics.
3. wrong/delayed/removed history produces source-diverse terminal-margin
   degradation, not only action distance.
4. positives are not source-singleton and are not explained by zero-current or
   reset controls alone.
```

### Self-ID Negative

Return a negative verdict if at least two hold:

```text
1. L2 finite-window or L1 one-step matches or beats L3 online on decisive tasks.
2. L2 current-tiled matches L2 finite-window, indicating older frames are not
   carrying useful information.
3. L3 reset/truncated matches L3 online, indicating recurrent hidden state is
   not needed.
4. wrong/delayed history changes action but not terminal margin.
5. outcome-positive rows remain source-singleton or control-sensitive after
   calibrated task attempts.
```

### Self-ID Conditional

Use a conditional verdict if:

```text
L3 history helps only in delayed, ambiguous, or terminal-boundary task families,
while L0/L1/L2 remains sufficient for ordinary reactive avoidance.
```

Conditional is a valid paper outcome. The project can still be a strong
actuator-level RL active-safety paper even if recurrent self-ID is not the main
claim.

## M1362 Anchor Policy

M1362 remains the current public-gate diagnostic anchor:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

It should not be compared as a fixed-budget architecture-ranking participant
against freshly trained L0/L1/L2 profiles because lineage and objectives differ.
It may be reported as:

```text
current public-base L3 diagnostic anchor
```

Checkpoint mutation to add metadata remains forbidden.

## Next Route

Admit:

```text
m1493-paper-route-go-no-go-profile-config-refresh-implementation
```

M1493 should be infrastructure only: implement or refresh full matrix configs
and tests. It should not train, replay, run PPO, promote, use private holdout,
export corpus, or change the actor input contract.
