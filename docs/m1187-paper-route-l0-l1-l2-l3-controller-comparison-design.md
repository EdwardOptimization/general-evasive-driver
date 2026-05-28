# M1187 Paper-Route L0/L1/L2/L3 Controller Comparison Design

## Summary

M1187 defines the fair controller comparison contract required before any
GRU-first paper claim or controller training. It is design-only. It does not
train L0/L1/L2/L3 controllers, run PPO, run replay, use private holdout,
promote a checkpoint, or change actor inputs.

The route decision is:

```text
l0_l1_l2_l3_controller_comparison_design_admit_profile_scaffold
```

The next milestone should implement controller-profile scaffolding only:

```text
experiments/manifests/m1188-paper-route-controller-profile-scaffold-implementation.json
```

## Fixed Actor Contract

All variants must use deployable inputs only:

- ego kinematics and IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands where allowed by the level;
- road, free-space, and obstacle geometry in ego frame;
- explicit finite-window history or online recurrent hidden state depending on
  the level.

Forbidden for every deployed actor:

- hidden dynamics parameters such as `mu`, mass, CG, tire stiffness, brake
  scale, and actuator time constants;
- slip ratio, slip angle, tire forces, tire saturation, or friction margin;
- AEB/AES/drift-required feasibility labels;
- controller mode, TTC, required clearance, stopping distance, reference
  trajectory, path error, heading error, or path curvature;
- collision, success, progress, or any precomputed answer.

The action contract is identical for all variants:

```text
u_t = [steer_command, throttle_command, brake_command]
```

## Controller Levels

### L0: Current-Only Feedback

Purpose: test whether current ego response and scene geometry already solve the
task.

Observation:

- canonical 72-value human-view frame;
- previous physical command fields masked to zero;
- no explicit stacked history;
- no recurrent hidden state.

Implementation target:

```text
env.history_length = 1
actor_encoder = mlp
observation_mask = zero_previous_command_fields
```

L0 is intentionally weaker than L1 because it removes command-response
causality. It is still deployable and is the necessary current-frame
substitution control.

### L1: One-Step Command-Response Feedback

Purpose: test whether current response plus the immediately previous command is
enough.

Observation:

- canonical 72-value human-view frame;
- previous physical command fields retained;
- current actuator state retained;
- no explicit multi-frame history;
- no recurrent hidden state.

Implementation target:

```text
env.history_length = 1
actor_encoder = mlp
observation_mask = none
```

L1 is the strongest practical current-feedback baseline. If L1 matches L2 and
L3, the paper should claim deployable closed-loop feedback rather than
history-based self-identification.

### L2: Finite-Window Command-Response History

Purpose: test whether explicit command-response windows help beyond L1 without
using online recurrent memory.

Observation:

- canonical L1 frame stacked over a fixed finite window;
- no hidden state carried beyond the window;
- same deployable input fields as L1;
- optional temporal encoder resets every decision window.

Window lengths are based on the current environment default `dt = 0.02s`:

| Window | Steps |
| ---: | ---: |
| 0.25 s | 13 |
| 0.50 s | 25 |
| 1.00 s | 50 |
| 2.00 s | 100 |

Implementation targets:

```text
L2-flat-short:
  env.history_length = 13 or 25
  actor_encoder = mlp

L2-temporal-window:
  env.history_length = K
  actor_encoder = temporal_gru
  actor_history_length = K
  hidden reset per finite window
```

The primary L2 challenger should be `L2-temporal-window`, because it avoids
making the 2.0s window an enormous flat input while still not using online
memory. Flat-window MLP is useful for 0.25s and 0.50s sanity checks.

### L3: Online GRU Recurrent Belief

Purpose: test whether online recurrent memory adds value beyond practical
finite windows.

Observation:

- canonical 72-value human-view frame;
- previous physical command fields retained;
- `env.history_length = 1`;
- online GRU hidden state persists through the episode.

Implementation target:

```text
actor_encoder = human_view_online_gru
recurrent_sequence_training = true
```

Required controls:

- `L3-reset-control`: same actor but reset hidden at fixed intervals or every
  step;
- `L3-truncated-control`: hidden persists only for a bounded window equivalent
  to L2 lengths;
- report whether L3 gains survive reset/truncation ablations.

## Fairness Controls

### Shared Controls

All variants must share:

- same environment task distribution;
- same action bounds and actuator dynamics;
- same reward for a given experiment family;
- same train/dev/public-eval split;
- same hidden-parameter randomization ranges;
- same optimizer schedule per training stage unless the manifest explicitly
  registers an architecture-specific exception;
- same private-holdout policy.

### Capacity Controls

Every run must report:

- parameter count;
- actor hidden size;
- encoder type;
- observation dimension;
- recurrent state dimension if any;
- mean inference time on CPU;
- optional GPU inference time if used.

Initial capacity tiers:

```text
smoke tier:
  hidden_size = 64
  short runs only

main comparison tier:
  hidden_size = 128
  matched seeds and gate policy
```

If exact parameter matching is not possible, report size and inference cost and
avoid claiming architecture superiority from one size tier alone.

## Task Families

### Family 1: Reactive Evasive Driving

Purpose: engineering baseline.

Expected possible outcome:

```text
L1 or L2 approximately matches L3
```

This is not a failure. It means current deployable feedback may be enough for
that task family.

Metrics:

- success rate;
- collision rate;
- road departure rate;
- spin or instability rate;
- clearance margin mean and lower-tail;
- control smoothness;
- recovery after obstacle pass.

### Family 2: Same-Current Same-Recent-Window Different-Older-History

Purpose: isolate history beyond current and recent finite windows.

Construction requirement:

```text
current frame matched
previous command and actuator state matched
recent K-step window matched
older history differs
future capability differs
```

K values:

```text
0.25s, 0.50s, 1.00s
```

This family is the main test for whether L3 can use evidence outside practical
L2 windows.

### Family 3: Diagnostic Warmup

Purpose: make history informative in a deployable way.

Warmup modes:

```text
brake_tap
steer_pulse
brake_plus_steer
lift_off_plus_steer
micro_countersteer
natural_policy
```

Each warmup must stay within safe low-amplitude commands and must not use
hidden state in the actor.

### Family 4: Variable Diagnostic Delay

Purpose: test the finite-window versus GRU tradeoff.

Diagnostic-to-obstacle delay:

```text
0.2s, 0.5s, 1.0s, 2.0s, 3.0s
```

Interpretation:

- if long L2 matches L3, the result supports finite-window history;
- if practical L2 windows fail but L3 succeeds, the result supports recurrent
  belief under delayed evidence;
- if L1 matches all, the task does not require history.

### Family 5: Source-Rich Extreme Dynamics

Purpose: replace stale proof rows with richer hidden-dynamics stress.

Current-model faults:

- global friction drop;
- front or rear lateral authority drop;
- brake authority drop;
- steering authority or lag fault;
- mass and CG shift;
- combined faults within existing simulator support.

Future-only faults such as single-wheel blowout, split-mu, stuck caliper, and
halfshaft loss should be documented as simulator-fidelity extensions, not
claimed in the current model unless implemented.

## Splits

M1187 does not allocate private holdout. It defines only public design splits.

Initial split proposal:

```text
train/dev construction seeds:
  118800-119199

public debug/eval seeds:
  119200-119455

public stress seeds:
  119456-119599

private holdout reserve:
  119900+
```

Private holdout must not be used until controller scaffolding, dataset
construction, and public gates are stable. If private-holdout failures guide
repair, the holdout must rotate before paper claims.

## Gate Usage

Use the policy in `docs/active-gate-policy.md`.

For design and scaffolding:

```text
Stack A process subset
```

For controller training smoke:

```text
Stack A behavior and fresh/OOD checks
```

For any mechanism claim:

```text
Stack B active public proof and source-diverse intervention diagnostics
```

For promotion or paper table freeze:

```text
Stack B + Stack C + private holdout protocol
```

## Metrics

Primary behavior metrics:

- success rate;
- collision rate;
- road departure rate;
- spin or instability rate;
- clearance margin mean and tail;
- recovery time;
- control smoothness.

History and capability metrics:

- future braking deceleration envelope error;
- future yaw authority error;
- future lateral acceleration response error;
- actuator lag proxy error;
- first-critical action distance to local target or teacher;
- terminal-boundary margin under matched history intervention;
- reset/truncate/wrong-history degradation.

Compute metrics:

- parameter count;
- observation dimension;
- hidden state dimension;
- CPU inference latency;
- optional GPU inference latency;
- training wall-clock and sample count.

## Decision Rules

If L1 matches L2 and L3:

```text
engineering route: current-response feedback
paper claim: deployable closed-loop feedback is strong
GRU route: research-only
```

If L2 matches L3:

```text
engineering route: finite-window history-conditioned controller
paper claim: command-response history helps but GRU is not necessary
```

If L3 wins only in delayed or variable-memory tasks:

```text
engineering route: choose L2 or L3 by robustness and latency
paper claim: recurrent belief has conditional advantage
```

If L3 wins broadly:

```text
engineering route: recurrent driver remains primary
paper claim: recurrent belief improves hidden-dynamics evasive driving
```

If no history model beats L1:

```text
stop GRU-first proof repair
return to scenario design and diagnostic warmup
```

## Implementation Gaps

Before any training, the repo needs a small controller-profile scaffold:

- profile names for `L0_current_masked`, `L1_one_step`, `L2_window_K`,
  `L2_temporal_window_K`, `L3_online_gru`, and `L3_reset_control`;
- observation masking for L0 previous-command fields;
- config generation for finite-window history lengths;
- parameter-count and observation-dimension reporting;
- a smoke command that instantiates each profile without training;
- tests that no profile uses hidden or oracle actor inputs.

This is the next milestone:

```text
m1188-paper-route-controller-profile-scaffold-implementation
```

## What Is Not Claimed

M1187 does not claim:

- any controller is trained;
- finite-window is better;
- GRU is better;
- self-identification has been proven;
- source-rich proof exists;
- private holdout is ready;
- driver performance improved.
