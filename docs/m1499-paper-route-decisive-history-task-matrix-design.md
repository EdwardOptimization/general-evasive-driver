# M1499 Paper-Route Decisive History Task Matrix Design

## Summary

M1499 designs the decisive T4/T5 task matrix after M1498 stopped standard
profile scaling.

Decision:

```text
decisive_history_task_matrix_design_admit_task_harness_implementation
```

This milestone does not train, run PPO, run replay, promote, use private
holdout, export corpus, change actor inputs, or claim profile superiority,
paper-level evidence, recurrent-belief advantage, or level3 self-identification.

## Why This Branch Exists

The standard public profile matrix is useful engineering baseline evidence, but
it did not prove older-history necessity:

```text
finite_window_history_necessity_on_standard_profile: not_supported
online_gru_hidden_advantage_on_standard_profile: not_supported
current_frame_substitution_risk: high
```

The next branch must make the causal question sharper:

```text
Can a deployable actuator-level driver use older command-response history to
choose a better maneuver when current frame and short recent feedback are
insufficient?
```

The branch must be able to return positive, negative, or conditional verdicts.

## Non-Negotiable Contract

All controller families keep the same deployable output:

```text
[steer, throttle, brake]
```

Actor inputs remain P0 human-view/no-wheel/no-oracle:

```text
ego and IMU-like response;
steering/throttle/brake actuator state;
previous physical commands;
ego-frame road/free-space/obstacle geometry;
finite-window history or recurrent hidden state.
```

Actor inputs must not include:

```text
mu, mass, CG, tire stiffness, brake scale, actuator tau;
slip ratio, slip angle, tire force, friction margin;
AEB/AES/drift-required labels, controller mode, oracle feasibility;
TTC, reference trajectory, path error, heading error, required clearance;
collision, success, progress, or any precomputed answer.
```

Privileged values may be used only by samplers, miners, teachers, diagnostics,
and evaluation labels.

## Controller Matrix

The decisive tasks reuse the M1493/M1497 controller families:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L2_window_13_current_tiled
L2_window_25_current_tiled
L2_window_50_current_tiled
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Fairness requirements:

```text
same training budget;
same optimizer family;
same public seed blocks;
same evaluation seed blocks;
same environment families;
no profile-specific tuning;
parameter count, runtime, and latency reported;
private holdout reserved for final promotion only.
```

If T4/T5 later prove that the task demands history but L3 under-trains, then a
separate L3 recipe-repair branch may be admitted. It should not precede the
task-design proof.

## T4: Same-Current Same-Recent Different-Older-History

### Question

Can older command-response history matter when the current observation and
recent window are intentionally matched?

### Construction

T4 generates paired scenarios A/B:

```text
same or tightly matched current ego state;
same or tightly matched current road/obstacle geometry;
same or tiled-matched recent window H_recent;
different older warmup history H_old;
different hidden capability or response evidence in H_old;
same deployable actor input contract.
```

The recent window should have multiple levels:

```text
recent_13  approximately 0.26s
recent_25  approximately 0.50s
recent_50  approximately 1.00s
```

The older-history window should cover:

```text
0.5s to 2.0s before the critical decision point.
```

The task may use privileged hidden capability only to generate pairs and labels.
The actor receives only the deployable observation/history profile.

### Candidate Families

Start with current-sim capability variations that already exist in the project:

```text
low/high friction and friction steps;
brake scale variation;
drive scale variation;
tire stiffness scale variation;
actuator delay or actuator tau variation;
sensor-noise and response-delay stress if supported by existing configs.
```

Wheel-specific faults such as one-wheel grip loss, tire blowout, or half-shaft
failure are useful future high-fidelity task families, but they should not be
pretended in the current single-track simulator unless the simulator explicitly
models the required asymmetry.

### Required Controls

Every T4 candidate must report:

```text
normal history;
current-tiled history;
reset recurrent state;
delayed history;
wrong older history from matched pair;
zero explicit response;
zero action-history fields.
```

The decisive intervention is not reset alone. It is wrong older history under
matched current and recent evidence.

### Acceptance Criteria

T4 candidate selection should require:

```text
current and recent-window distance below pre-registered tolerances;
older-history response distance above a pre-registered threshold;
teacher/oracle or rollout action divergence above threshold;
normal-history terminal margin exceeds wrong-history terminal margin;
wrong-history degradation is margin- or success-relevant, not action-only;
source diversity across seeds, capability pairs, reveal steps, and geometry.
```

Initial public thresholds may be conservative:

```text
accepted rows >= 80 before compact selection;
physical capability pairs >= 8;
seeds >= 5;
reveal/decision steps >= 4;
max single-source share <= 0.35;
mean wrong-history margin gap >= 0.02 or success-drop evidence present.
```

These thresholds are public development gates, not final paper holdout criteria.

## T5: Terminal-Boundary Near-Constraint Avoidance

### Question

Does correct early belief/history improve terminal safety when the episode is
near a collision, road-boundary, or spin constraint?

### Construction

T5 generates near-boundary tasks:

```text
normal-history rollout succeeds or nearly succeeds;
terminal clearance margin is small but positive;
wrong, delayed, reset, or current-tiled history pushes the same scenario across
the terminal boundary or materially reduces margin;
intervention changes final outcome, not only first action.
```

Near-boundary windows should be pre-registered:

```text
near_pass_margin: 0.0005 to 0.03
near_fail_margin: -0.03 to 0.0
tail metric: p10 and p05 clearance margin, not only mean margin
```

### Candidate Families

T5 should include handling-limit variants:

```text
late obstacle reveal;
close obstacle at high speed;
low-friction or friction-step road;
delayed steering or braking response;
reduced brake/drive capability;
understeer/oversteer-biased tire stiffness;
post-maneuver recovery after large yaw or sideslip;
unavoidable-collision mitigation where lower impact or larger clearance is the
correct outcome metric.
```

The design intentionally includes mitigation. A professional driver-like policy
must handle avoidable and unavoidable cases without an oracle mode flag.

### Required Controls

T5 uses the same controls as T4, plus terminal diagnostics:

```text
normal terminal margin;
reset terminal margin;
current-tiled terminal margin;
wrong-history terminal margin;
delayed-history terminal margin;
zero-current-response terminal margin;
impact speed or severity proxy for unavoidable cases;
spin/unstable and road-departure outcomes.
```

### Acceptance Criteria

T5 candidate selection should require:

```text
normal-history terminal margin inside the near-boundary band;
at least one history intervention reduces margin by >= 0.02 or flips success;
wrong-history or delayed-history causes the largest degradation when applicable;
controls do not explain the effect better than real history;
source diversity across seeds, capability pairs, reveal steps, and geometry.
```

If current response or one-step feedback solves T5 equally well, this is a
negative or conditional result for recurrent self-ID, not a reason to weaken the
claim standard.

## Public Development Versus Private Holdout

T4/T5 should use public development gates first:

```text
public candidate generation;
public preflight;
public bounded replay/probe;
public fixed-budget controller pilot;
public audit.
```

Private holdout is reserved for final promotion or paper-grade evidence. If a
private holdout failure is used to repair the task or controller, rotate the
holdout before claiming unbiased evidence.

## Metrics

Every T4/T5 run must report:

```text
success_rate;
collision_rate;
road_departure_rate;
spin_or_unstable_rate;
clearance_margin_mean;
clearance_margin_p10 and p05;
min_clearance_margin;
impact severity proxy for unavoidable cases;
first-critical action distance;
normal-vs-wrong terminal margin gap;
normal-vs-reset terminal margin gap;
normal-vs-current-tiled terminal margin gap;
normal-vs-delayed terminal margin gap;
source diversity and max source share;
training seed and eval seed sensitivity.
```

## Verdict Rules

Positive level3 evidence requires all of:

```text
source-diverse T4 or T5 tasks;
normal history beats reset/current-tiled/wrong/delayed controls in terminal
margin or success;
wrong-history degradation is outcome-relevant;
L3 or an explicit-history model beats L0/L1 under fair budgets;
private holdout confirmation after public development stabilizes.
```

Negative evidence is recorded if:

```text
current-response or one-step feedback matches history models on T4/T5;
current-tiled controls match finite-window history;
reset hidden matches online GRU;
wrong/delayed history changes actions but not terminal outcomes;
source-diverse T4/T5 construction fails under honest constraints.
```

Conditional evidence is recorded if:

```text
history helps only under delayed response, late reveal, friction-step, or
terminal-boundary subsets;
finite windows match or beat online GRU;
GRU helps only after recipe repair and not under the fixed-budget matrix.
```

## Implementation Route

M1500 should implement a no-training decisive task harness, not a training run:

```text
1. T4/T5 task spec dataclasses or JSON schemas.
2. Candidate generation entry point with public seed controls.
3. Geometry/current/recent-window matching diagnostics.
4. Intervention label schema for normal/reset/current-tiled/wrong/delayed.
5. Source-diversity and max-source-share summaries.
6. Runtime smoke with tiny candidate count and no promotion.
```

After M1500:

```text
M1501: public T4/T5 candidate-generation smoke.
M1502: audit candidate diversity and current/recent matching.
M1503: bounded replay/probe design if M1502 passes.
M1504+: fixed-budget controller pilot only after no-training task evidence is
        source-diverse and control-clean.
```

## Guardrails

```text
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
profile_specific_tuning: false
actor_input_contract_changed: false
training_corpus_exported: false
profile_superiority_claimed: false
self_identification_claimed: false
paper_level_claimed: false
next_branch: paper_route_decisive_history_task_matrix
next: m1500-paper-route-decisive-history-task-harness-implementation
```
