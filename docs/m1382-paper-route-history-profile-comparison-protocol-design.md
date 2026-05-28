# M1382 Paper-Route History-Profile Comparison Protocol Design

## Purpose

M1382 designs the fixed fair-comparison protocol for L0/L1/L2/L3 history
profiles after M1381 closed the promoted-base source-rich/comparison-readiness
branch.

This milestone is design-only. It does not train, run PPO, run new evaluation,
promote a checkpoint, use private holdout, export a corpus, change actor inputs,
or claim a profile-ranking result.

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

## Prior Profile Lessons To Preserve

The older finite-window vs GRU branch is still relevant and should not be
forgotten.

M1187 defined the original L0/L1/L2/L3 contract:

```text
L0: current-frame feedback, previous-command fields masked
L1: current-frame + one-step command-response feedback
L2: finite-window command-response history
L3: online recurrent GRU hidden state
```

M1200-M1205 found two important issues:

```text
1. L2 finite-window trends can be current-frame or temporal-GRU capacity effects.
2. L3 reset-control evaluation must honor reset_hidden_policy explicitly.
```

M1202-M1204 implemented the corrected controls:

```text
ObservationMaskSpec.history_transform = current_tiled
ObservationMaskSpec.reset_hidden_policy metadata
profile-aware evaluation reset semantics
```

M1213 then classified the corrected public repeats:

```text
stable_negative_for_finite_window_history_necessity
unstable_L3_family_ranking
weak_positive_for_online_vs_reset_in_M1212
inconclusive_across_blocks
```

Therefore M1382 must not repeat the old mistake of treating a profile aggregate
as history proof. Current-tiled controls, reset-policy-aware evaluation, paired
source diagnostics, and fixed budgets are mandatory.

## Profile Set

The main comparison protocol has four levels plus required controls.

### L0: Current-Only Feedback

Purpose:

```text
test whether current ego response and scene geometry already solve the task.
```

Contract:

```text
canonical human-view frame
previous physical command fields masked to zero
no stacked history
no recurrent hidden state
```

Interpretation:

```text
If L0 is competitive, the task may not require command-response causality or
history. This is not a failure; it bounds the claim.
```

### L1: One-Step Command-Response Feedback

Purpose:

```text
test whether current response plus immediately previous command is enough.
```

Contract:

```text
canonical human-view frame
previous physical command fields retained
actuator state retained
no multi-frame stack
no recurrent hidden state
```

Interpretation:

```text
If L1 matches L2/L3, the correct claim is deployable closed-loop feedback, not
history-based self-identification.
```

### L2: Finite-Window History

Purpose:

```text
test whether explicit finite command-response windows help beyond L1 without
online recurrent memory.
```

Primary windows:

```text
13 steps  ~= 0.25 s
25 steps  ~= 0.50 s
```

Optional later windows:

```text
50 steps  ~= 1.00 s
100 steps ~= 2.00 s
```

Required controls:

```text
L2_window_13_current_tiled
L2_window_25_current_tiled
```

Current-tiled controls preserve observation shape and temporal-GRU capacity but
replace older frames with the current frame. They are required before any
finite-window history-necessity claim.

### L3: Online GRU Recurrent Driver

Purpose:

```text
test whether persistent online recurrent hidden state adds value beyond L1/L2
and beyond reset controls.
```

Primary L3 checkpoint for public-base diagnostics:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Required controls:

```text
L3_online_gru_persistent
L3_reset_control_corrected
L3_zero_action_history
L3_zero_current_response
L3_zero_all_response
```

For architecture-ranking experiments, L3 must also be trained under the same
fixed budget as L0/L1/L2. M1362 can be used as the current public-base L3
diagnostic, but it cannot be compared as a fair training-budget architecture
ranking against newly trained L0/L1/L2 checkpoints.

## Comparison Tiers

The protocol separates three tiers so claims do not mix.

### Tier A: Artifact Inventory And Readiness

Question:

```text
Do we have compatible profile configs, checkpoints, runners, masks, reset
semantics, and source-rich diagnostic hooks for the current M1362 public base?
```

Allowed:

```text
read configs and manifests
verify artifact paths
verify profile metadata
write readiness doc
```

Not allowed:

```text
training
PPO
new evaluation
private holdout
promotion
paper-level ranking
```

### Tier B: Public-Base Diagnostic Comparison

Question:

```text
How does the current public-base L3 checkpoint behave under reset/zero/history
diagnostics and against existing public reference profiles?
```

Allowed claim:

```text
public-base diagnostic only
```

Blocked claim:

```text
architecture superiority, because M1362 and old profile checkpoints do not share
a fair training budget or objective lineage.
```

### Tier C: Fair Fixed-Budget Profile Refresh

Question:

```text
Under the same training budget, seeds, env distribution, reward, evaluation
seeds, and public gates, which history profile family is stronger?
```

Required before this tier:

```text
profile configs generated from a single template
same training seeds for every profile
same public evaluation seeds for every checkpoint
same reward/env/randomization
same optimizer schedule unless pre-registered
same metric and artifact schema
current-tiled L2 controls included
corrected L3 reset-control included
```

This tier can produce public profile-ranking evidence, but not private-holdout
or paper-level claims by itself.

## Scenario And Gate Stack

Use a fixed order:

```text
1. actor input contract and profile metadata checks
2. finite metrics and artifact completeness
3. public behavior/generalization diagnostics
4. public proof replay or source-history diagnostics where applicable
5. source-rich temporal diagnostics as secondary public evidence
6. no private holdout until public protocol is stable
```

Required public scenario families:

```text
standard emergency avoidance public eval
fresh public route/generalization seeds
moderate-OOD public seeds
behavior seeds used by the public-base gate
source-rich temporal diagnostic rows from M1377/M1379, clearly marked public
```

Source-rich diagnostics remain secondary because M1379 is seed-thin. They may
support history-dependence discussion, but they must not decide architecture
promotion alone.

## Metrics

Report per profile and seed:

```text
success_rate
collision_rate
road_departure_rate
spin_or_unstable_rate
clearance_margin_mean
clearance_margin_p10
return_mean
termination_reason_histogram
control_smoothness
runtime_seconds
parameter_count
observation_dim
history_length
reset_hidden_policy
history_transform
```

Report causal-history diagnostics where applicable:

```text
L3_online_vs_reset_delta
L3_online_vs_zero_action_history_delta
L3_online_vs_zero_current_response_delta
L3_online_vs_zero_all_response_delta
L2_window_vs_current_tiled_delta
source_rich_temporal_sequence_gap
cross_fault_wrong_history_gap
```

## Claim Interpretation

The protocol pre-registers the weakest valid claims.

```text
L0 competitive:
  current-frame feedback is strong; history necessity not shown.

L1 competitive:
  one-step command-response feedback is enough for the tested distribution.

L2 beats current-tiled controls:
  finite-window history may matter for the tested distribution.

L2 does not beat current-tiled controls:
  finite-window aggregate gains are likely current-frame/capacity effects.

L3 beats corrected reset and L2 under fixed budget:
  online recurrent hidden state has public evidence of utility.

L3 only beats reset on source-rich temporal rows:
  level2 history-encoded reactive evidence, not level3 self-ID.

Cross-fault wrong-history remains zero/sparse:
  cross-fault self-identification remains unsupported.
```

Level3 anticipatory self-identification remains blocked until same-current or
matched-current diagnostics show that wrong/delayed/counterfactual history
changes future behavior and outcome in a source-diverse way.

## Fairness Rules

No profile may receive:

```text
hidden dynamics parameters
slip or tire-force oracle channels
oracle feasibility labels
controller mode labels
path/reference errors
TTC
required clearance
oracle stopping distance
profile-specific reward shaping
profile-specific private tuning
post-hoc threshold relaxation
```

If architecture-specific hyperparameters are unavoidable, they must be
pre-registered, reported, and kept out of architecture-superiority claims until a
matched sensitivity audit is done.

## Route Decision

Decision:

```text
history_profile_comparison_protocol_design_admit_artifact_inventory
```

Next milestone:

```text
m1383-paper-route-history-profile-artifact-inventory
```

M1383 should not train or evaluate. It should inventory:

```text
existing profile configs under configs/paper_route_profiles
corrected profile control support
existing L0/L1/L2/L3 checkpoints and their lineage
whether M1362 can be used as public-base L3 diagnostic only
which new fixed-budget checkpoints would be needed for fair architecture ranking
which runner should implement Tier B/Tier C
```

Only after M1383 should the project choose between a public-base diagnostic run
and a full fixed-budget profile refresh.

## Guardrails

M1382 performs no training, PPO, new evaluation, actor update, checkpoint
mutation, promotion, private holdout, threshold relaxation, actor-input
expansion, corpus export, high-fidelity claim, paper-level comparison result, or
level3 self-identification claim.
