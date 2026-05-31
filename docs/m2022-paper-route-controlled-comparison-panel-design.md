# M2022 Paper-Route Controlled Comparison Panel Design

- status: completed
- decision: `controlled_comparison_panel_design_admit_no_rollout_preflight_implementation`
- governing plans:
  - `docs/self-id-go-no-go-paper-route-plan.md`
  - `docs/paper-route-finite-window-vs-gru-plan.md`
- immediate evidence trigger: `docs/m2021-multi-slice-bounded-diagnostic-comparison-result-audit.md`
- historical infrastructure reused:
  - `src/autodrift/controller_family_decisive_matrix_protocol.py`
  - `src/autodrift/controller_family_rollout_protocol_preflight.py`
  - `docs/m1383-paper-route-history-profile-artifact-inventory.md`
  - `docs/m1680-paper-route-controller-family-bounded-task-source-generation-preflight.md`
  - `runs/m1683_controller_family_bounded_rollout_protocol_preflight/summary.json`
- reset/rollout/measured execution in M2022: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2022 converts the M2021 bounded diagnostic route decision into a concrete
controlled-comparison panel design. It does not execute the panel. The design
exists to prevent the next step from becoming either:

```text
1. another public-slice local search loop, or
2. an unfair controller-family ranking from diagnostic artifacts.
```

The next valid evidence type is a controlled panel where L0/L1/L2/L3 controller
families share the same deployable action/input boundary, same task sources,
same split rules, and explicit claim gates.

## Non-Negotiable Actor Contract

All deployable controller variants must output:

```text
u_t = [steer_command, throttle_command, brake_command]
```

Allowed actor inputs:

```text
ego kinematics and IMU-like response
steering/throttle/brake actuator state
previous physical commands where the profile permits them
ego-frame road/free-space/obstacle geometry
finite-window command-response history or online recurrent hidden state
```

Forbidden actor inputs:

```text
mu, mass, CG, tire stiffness, brake scale, actuator time constants
slip ratio, slip angle, tire force, tire saturation, friction margin
AEB/AES/drift-required feasibility labels
controller mode, reference trajectory, TTC, required clearance
oracle stopping distance, path error, heading error, path curvature
collision, success, progress, or any precomputed answer
```

Training-time miners and audits may use privileged information only outside the
actor input path.

## Controller Matrix

M2022 adopts the corrected profile family already represented in
`controller_family_decisive_matrix_protocol.py`:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Interpretation:

```text
L0_current_masked:
  current deployable frame, with previous-command fields masked.

L1_one_step:
  current deployable frame plus one-step command/actuator response.

L2_window_*:
  explicit finite command-response windows.

L2_window_*_current_tiled:
  capacity controls that keep temporal shape but remove older-history content.

L3_online_gru:
  online recurrent hidden state.

L3_reset_control_corrected:
  same recurrent architecture with reset policy enforced.
```

This matrix is allowed to produce a negative, conditional, or positive self-ID
verdict. The design must not assume that L3 is the final winner.

## Task Families

The panel must cover five task families. A later preflight may fail closed if a
family lacks enough clean source support.

```text
T1_reactive_active_safety:
  stable AEB, stable AES, drift-required recovery, and unavoidable mitigation.
  M2020 supplies the first bounded diagnostic trigger, but its source-kind
  singleton boundary means it is not enough for paper ranking.

T2_same_current_different_older_history:
  matched current frame and matched recent window, but older command-response
  evidence differs and future capability differs.

T3_active_diagnostic_warmup:
  low-amplitude brake taps, steer pulses, lift-off/steer, and natural-policy
  warmup before obstacle reveal.

T4_variable_diagnostic_delay:
  diagnostic cue to obstacle reveal delays at short, medium, and long windows.
  Existing explicit-window tags from M1680/M1683 are reusable here.

T5_source_rich_extreme_dynamics:
  global friction drop, front/rear lateral authority drop, brake authority drop,
  steering authority/delay faults, mass/CG shift, delay/noise faults, and
  combined faults.
```

Future-only high-fidelity faults such as true per-wheel puncture, split-mu
contact patches, half-shaft failure, or wheel-specific blowout must be marked as
future validation tasks until the simulator supports them cleanly.

## Source And Split Rules

The panel should be source-rich before it is allowed to support ranking or
self-ID claims.

Minimum design targets for the full public panel:

```text
task_family_count: 5
controller_profile_count: 12
minimum_clean_sources_per_family: 12
target_clean_sources_per_family: 24
max_single_repair_source_kind_share: 0.35
max_single_source_family_share: 0.25
max_single_obstacle_label_share: 0.35
max_single_seed_share: 0.10
```

Split discipline:

```text
public_debug:
  allowed for plumbing, schema repair, and runner failures.

public_gate:
  allowed for daily proof/generalization gates after the protocol is frozen.

private_holdout:
  not used in M2022 or the first no-rollout preflight;
  used only after public protocol freeze and never repaired against directly.
```

If a private holdout result guides repair, the holdout must be rotated before a
promotion or paper claim.

## Execution Ladder

The comparison must escalate in stages:

```text
Stage 0: no-rollout panel preflight
  Emit panel_protocol.json, workload_matrix.csv, source_coverage.csv, and
  claim_boundary.csv. No environment reset or policy action.

Stage 1: public routing smoke
  Small source-diverse subset, all 12 profiles, one episode per cell. This
  checks plumbing only and cannot rank profiles.

Stage 2: public full-panel execution
  All admitted public sources and all 12 profiles. This can expose task-quality
  or source-diversity failures, but still cannot be paper-level without audit.

Stage 3: fair training/evaluation repeat
  Same budgets, seeds, rewards, train/eval splits, and profile configs for all
  trained families. Existing fixed checkpoints may be reported as diagnostics
  only unless their training budgets are matched.

Stage 4: private holdout evaluation
  Only after public protocol freeze. No tuning from private failures.
```

Do not jump from M2022 directly to Stage 2 or Stage 3.

## Metrics

Every executed stage after Stage 0 should report:

```text
success rate
collision rate
road-departure/offtrack rate
spin rate
clearance margin mean and lower-tail quantiles
first-critical action quality
control smoothness
recovery time after maneuver
termination reason histogram
parameter count
inference latency
```

History-specific deltas:

```text
L2 normal - L2 current-tiled success and margin delta
L3 online - L3 reset success and margin delta
L3 online - best L2 normal success and margin delta
L1 current-response - history-family success and margin delta
normal history - wrong/delayed/mismatched history terminal-margin delta
```

## Claim Gates

The panel supports only the weakest claim whose gate passes.

### Claim A: Deployable Feedback Driver

Allowed when a deployable actor-level controller performs active-safety tasks
using only P0 human-view no-oracle inputs.

This does not require history advantage.

### Claim B: History-Conditioned Output Feedback

Allowed when finite-window or recurrent history improves first-critical action,
future capability prediction, or terminal margin over current/one-step controls
on source-rich tasks.

### Claim C: Recurrent Belief Advantage

Allowed only when L3 online GRU beats the best practical L2 finite-window
controller and L3 reset control on source-rich delayed or older-history tasks,
with matched budgets and no profile-specific tuning.

### Claim D: Strong Self-Identification

Allowed only when wrong, delayed, reset, or mismatched history degrades
outcome-relevant terminal behavior on source-diverse boundary tasks while
normal history remains successful.

Explicitly forbidden from M2022 alone:

```text
controller-family ranking
finite-window-vs-GRU conclusion
paper-level benchmark result
level3 self-identification
```

## Stop And Pivot Rules

Stop before execution if:

```text
any profile violates the P0 input contract
any task family cannot be mapped to clean source specs
source-kind singleton dominates the panel
current-tiled or reset controls are missing
the workload matrix omits profile/source pairing
the panel uses private holdout for debugging
the design requires profile-specific tuning
```

Pivot rules:

```text
If T1 active-safety is too sparse:
  route to task-quality/source repair, not ranking.

If T2/T3/T4 history tasks are too sparse:
  route to history-task generation repair before self-ID tests.

If T5 source-rich faults remain seed-thin:
  keep source-rich evidence diagnostic and do not claim level3 self-ID.

If L1 or L2 later matches L3:
  report a valid engineering result and stop recurrent-belief overclaim.
```

## M2023 Requirements

M2023 should implement a no-rollout panel preflight. It should read existing
profile metadata and candidate source artifacts, then write:

```text
runs/m2023_paper_route_controlled_comparison_panel_preflight/summary.json
runs/m2023_paper_route_controlled_comparison_panel_preflight/panel_protocol.json
runs/m2023_paper_route_controlled_comparison_panel_preflight/workload_matrix.csv
runs/m2023_paper_route_controlled_comparison_panel_preflight/source_coverage.csv
runs/m2023_paper_route_controlled_comparison_panel_preflight/claim_boundary.csv
```

M2023 must remain no-rollout and must fail closed if profile coverage, source
coverage, actor contract, or claim-boundary checks are incomplete.
