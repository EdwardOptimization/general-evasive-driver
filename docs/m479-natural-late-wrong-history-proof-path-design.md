# M479 Natural Late Wrong-History Proof Path Design

## Purpose

M479 designs the next proof path after M478 showed that clamped persistent
wrong hidden state can create source-diverse outcome degradation, while the
standard one-shot wrong-history intervention still produces zero proof rows.

No training, PPO, actor-input change, proof expansion, or checkpoint promotion
is performed.

## What M478 Proved And Did Not Prove

M478 proved a mechanism:

```text
wrong_hold_16:
  proof-style rows: 25
  success/collision/completion rows: 10
  probe seeds: 6
  labels: 2
  targets: 2
```

M478 also kept the original one-shot baseline:

```text
wrong_once:
  proof-style rows: 0
```

This means hidden belief can be outcome-critical if the wrong hidden state is
held active during the emergency window. It does not mean the deployable actor
naturally depends on history strongly enough, because clamping the hidden state
for multiple steps is an artificial causal intervention.

## Design Goal

The next diagnostic should reduce artificiality before any training or proof
claim. The cleanest next test is:

```text
late one-shot wrong-history injection
```

Instead of clamping the wrong hidden state for K steps, inject it once at a
later continuation step, then let recurrent dynamics update normally:

```text
at continuation step S:
  action_hidden = right.hidden
  next_hidden_after_action = model update from the current left observation

all other steps:
  normal recurrent hidden update
```

This tests whether one-shot wrong belief becomes outcome-critical when it is
applied closer to the actual emergency maneuver.

## M480 Implementation Choice

Extend the existing M478 module:

```text
src/autodrift/persistent_wrong_history_intervention_gate.py
```

Add late one-shot variants:

```text
wrong_late_2_once
wrong_late_4_once
wrong_late_8_once
wrong_late_12_once
```

These are represented by:

```text
injection_start_step = S
hold_steps = 1
clamp_hidden = false
family = wrong_late_once
```

Keep the existing variants in the same tool:

```text
wrong_once
wrong_hold_4 / 8 / 16
wrong_late_*_hold_*
reset_hidden
zero_current_response
```

This keeps M480 directly comparable to M478.

## M480 Smoke

Run the updated gate on the same M474 adversarial pair surface:

```text
runs/m474_combined_fresh_anchor_adversarial_search/adversarial_pairs.csv
```

Use the same checkpoint and config:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
configs/m457_history_necessity_late_reveal_zero_relvel.json
```

## Pass / Fail Interpretation

M480 is still diagnostic. It is closer to natural history dependence than
clamped hold variants, but it is still an intervention.

Positive natural-late evidence:

```text
at least one wrong_late_*_once variant has:
  proof_candidate_count >= 16
  success_or_collision_or_completion_rows >= 4
  probe_seed_count >= 6
  obstacle_label_count >= 2
  target_count >= 2
  single_seed_share <= 0.50
  single_label_share <= 0.70
```

Interpretation if positive:

```text
wrong belief is outcome-critical when injected at the critical instant;
the original wrong_once failure is mostly injection timing.
```

Interpretation if negative while hold variants remain positive:

```text
the policy needs wrong belief to persist across multiple emergency steps before
outcome changes. The next path should be shorter-emergency task design or
training/evaluation that tests natural belief persistence, not more one-shot
history swaps.
```

## Guardrails

M480 must not:

```text
train or update a checkpoint
promote a checkpoint
change actor inputs
call late one-shot intervention deployable proof
relax near-boundary thresholds
count clamped hold rows as natural-late proof
```

## Decision

```text
admit_m480_late_once_wrong_history_implementation
```

No checkpoint is promoted.
