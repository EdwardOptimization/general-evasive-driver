# M1670 Paper-Route Controller-Family Decisive Evidence Matrix Design

## Summary

M1670 designs the next paper-route evidence matrix after M1669 audited the
current controller-family state.

Decision:

```text
controller_family_decisive_matrix_design_admit_protocol_preflight
```

This milestone is design-only. It does not train, run replay, run PPO, promote
a checkpoint, use private holdout, change actor inputs, repair the M1663
artifact, or claim paper-level or level3 self-identification evidence.

## Design Question

The project must stop asking only:

```text
Can the online-GRU proof harness preserve a fixed public row?
```

The paper-route question is broader:

```text
Under the same deployable input contract and actuator output contract, when is
current response enough, when is finite-window history enough, and when does an
online recurrent state add measurable value?
```

M1670 therefore designs a controller-family decisive evidence matrix rather
than another artifact repair.

## Non-Negotiable Actor Contract

Every deployable actor uses:

```text
u_t = [steer_command, throttle_command, brake_command]
```

Allowed deployable information:

```text
ego kinematics and IMU-like response;
steering / throttle / brake actuator state;
previous physical commands;
ego-frame road / free-space / obstacle geometry;
finite-window history or recurrent hidden state, depending on controller family.
```

Forbidden deployable inputs:

```text
mu, mass, CG, tire stiffness, brake scale, actuator tau;
slip ratio, slip angle, tire force, friction margin;
AEB/AES/drift-required labels, controller mode, oracle feasibility;
TTC, reference trajectory, path error, heading error, required clearance;
collision, success, progress, or any precomputed answer.
```

Privileged quantities may only appear in samplers, teachers, diagnostics,
metrics, and audit labels.

## Controller Families

The first matrix uses the existing corrected profile configs:

| Family | Config | Purpose |
| --- | --- | --- |
| C0 | `m1207_l0_current_masked.json` | current frame, previous command masked |
| C1 | `m1207_l1_one_step.json` | strong current-response / one-step baseline |
| C2-13 | `m1207_l2_window_13.json` | finite window about 0.26 s |
| C2-25 | `m1207_l2_window_25.json` | finite window about 0.50 s |
| C2-50 | `m1207_l2_window_50.json` | finite window about 1.00 s |
| C2-100 | `m1207_l2_window_100.json` | finite window about 2.00 s |
| C2c-13 | `m1207_l2_window_13_current_tiled.json` | capacity/current-frame control |
| C2c-25 | `m1207_l2_window_25_current_tiled.json` | capacity/current-frame control |
| C2c-50 | `m1207_l2_window_50_current_tiled.json` | capacity/current-frame control |
| C2c-100 | `m1207_l2_window_100_current_tiled.json` | capacity/current-frame control |
| C3 | `m1207_l3_online_gru.json` | online recurrent candidate |
| C3c | `m1207_l3_reset_control_corrected.json` | corrected reset hidden control |

Truncated L3 controls can be added later, but they are not required for the
first preflight because C3c already tests the strongest reset-control null
hypothesis.

## Evidence Layers

### Layer S: Standard Profile Baseline

Source:

```text
runs/m1497_go_no_go_profile_three_seed_public_pilot
```

Use:

```text
reference baseline only;
no rerun unless protocol preflight finds config drift or metrics missing.
```

Interpretation:

```text
standard profile does not support L2 history necessity;
standard profile does not support L3 online advantage over corrected reset;
standard profile remains important engineering coverage.
```

### Layer D: Decisive-History Task Families

Source documents:

```text
docs/m1499-paper-route-decisive-history-task-matrix-design.md
docs/m1509-paper-route-decisive-history-task-matrix-synthesis.md
docs/m1526-paper-route-t5-timing-amplified-branch-synthesis.md
docs/m1548-paper-route-fresh-ambiguity-source-mining-branch-synthesis.md
```

Required task families:

```text
T4: same-current, same-recent-window, different-older-history
T5: terminal-boundary near-constraint avoidance
```

The first matrix should treat the existing T4/T5 artifacts as public
development sources. It must not call them private holdout evidence.

### Layer C: Clean Active-Set Package

Source:

```text
runs/m1615_contour_aware_candidate_corpus
```

Current package:

```text
positive_candidate_count: 39
diagnostic_guardrail_count: 232
positive_rows_all_clean: true
diagnostic_rows_used_as_positive: false
```

Use:

```text
diagnostic active-set layer;
never as private holdout;
never as direct proof that L3 is superior;
never as a positive training corpus without a later manifest.
```

The protocol preflight must check whether the clean package can be mapped to
controller-family comparisons honestly. If the package is too online-GRU
hidden-specific, it remains an L3 proof diagnostic, and the matrix must instead
use the same source families to regenerate controller-family-compatible tasks.

### Layer R: Artifact-Route Regression Evidence

Source:

```text
runs/m1666_fusion_actor_artifact_replay_first_check/summary.json
docs/m1668-paper-route-proposal-projection-artifact-branch-synthesis.md
```

Use:

```text
negative evidence and guardrail;
do not repair this artifact inside the controller-family matrix branch.
```

## Matrix Stages

### Stage 0: Protocol Preflight

Goal:

```text
build a machine-readable matrix protocol without training or replay.
```

Checks:

```text
all 12 corrected profile configs exist;
all configs obey P0/no-oracle contract metadata;
standard M1497 aggregate metrics are readable;
M1615 clean package and diagnostic guardrails are readable;
M1666 regression summary is readable;
task families are assigned to public development layers;
private holdout remains unused;
no profile-specific tuning is admitted.
```

Artifact:

```text
runs/m1671_controller_family_decisive_matrix_protocol/summary.json
runs/m1671_controller_family_decisive_matrix_protocol/matrix_protocol.json
```

### Stage 1: One-Seed Public Plumbing Pilot

Run only after Stage 0 audit passes.

Purpose:

```text
confirm that each controller family can be trained/evaluated on the selected
decisive public task layer with finite metrics under equal budget.
```

Interpretation:

```text
plumbing only;
no controller ranking;
no paper-level claim.
```

### Stage 2: Three-Seed Public Decisive Matrix

Run only after Stage 1 audit passes.

Rules:

```text
same training steps;
same optimizer family;
same env count and rollout settings;
same public eval seeds;
same reward and terminal metrics;
same task-family sampling policy;
no profile-specific tuning.
```

The matrix reports trends but cannot promote a checkpoint or use private
holdout.

### Stage 3: Source-Diverse Decisive Holdout Design

Only after Stage 2 is stable, design a holdout. Do not use private holdout to
repair the public protocol.

## Metrics

Every matrix result must report:

```text
success_rate
collision_rate
road_departure_rate
spin_or_unstable_rate
clearance_margin_mean
clearance_margin_p10
clearance_margin_p05
min_clearance_margin
control_smoothness
parameter_count
inference_latency_proxy
```

History-specific metrics:

```text
L2 normal - L2 current-tiled success/margin delta;
L3 online - L3 reset success/margin delta;
L3 online - best L2 normal success/margin delta;
L3 online - best L1/L2 baseline collision delta;
normal-history versus wrong-history terminal margin gap where applicable;
normal-history versus delayed-history terminal margin gap where applicable;
reset/zero-current/zero-action control degradation reported separately.
```

## Claim Rules

### Negative Or Reactive Result

If C1 one-step current-response matches C2 and C3 on decisive tasks:

```text
claim: deployable current-response feedback is sufficient for this task family;
do not claim history necessity or GRU self-ID.
```

### Finite-Window Result

If C2 normal beats C2 current-tiled and matches or beats C3:

```text
claim: finite-window command-response history is useful;
do not claim recurrent belief advantage.
```

### Recurrent Advantage Result

If C3 beats best C2 and C3c reset under source-diverse decisive tasks:

```text
claim: online recurrent state adds measurable value beyond practical finite windows;
still require wrong/delayed history interventions before level3 self-ID claims.
```

### Strong Self-ID Result

Only if source-diverse wrong/delayed history interventions degrade terminal
outcomes while normal-history remains successful:

```text
claim: mechanism evidence for history-dependent belief-like control.
```

This cannot be claimed from Stage 0 or Stage 1.

## Stop Rules

Stop and audit before implementation escalation if:

```text
any actor profile violates P0/no-oracle input contract;
L2 current-tiled controls are missing or dimension-mismatched;
L3 reset-control semantics are not honored;
M1615 package cannot be mapped without leaking L3-specific hidden labels;
task sources are too public-row-specific for a controller-family comparison;
the design requires profile-specific tuning to make one family viable;
private holdout is used for repair or protocol shaping.
```

If clean active-set mapping fails, do not force it. Route to a controller-family
compatible T4/T5 source-generation design.

## Next Step

Admit exactly one no-training protocol preflight:

```text
m1671-paper-route-controller-family-decisive-matrix-protocol-preflight
```

M1671 should implement or run the smallest tooling needed to write the matrix
protocol and verify source/config availability. It must not train, replay,
evaluate policies, repair checkpoints, use private holdout, or claim
controller-family results.

## Guardrails

```text
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
artifact_repair_started: false
profile_specific_tuning_admitted: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1671-paper-route-controller-family-decisive-matrix-protocol-preflight
```
