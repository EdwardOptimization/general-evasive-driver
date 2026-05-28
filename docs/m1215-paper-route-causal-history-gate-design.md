# M1215 Paper-Route Causal History Gate Design

## Summary

M1215 designs the next paper-route evidence gate after M1214 closed the broad
profile-comparison branch.

Decision:

```text
causal_history_gate_design_admit_source_audit
```

No training, PPO, replay, checkpoint repair, promotion, private holdout,
profile tuning, or actor-input change occurs in M1215.

## Motivation

M1209 and M1212 showed that aggregate L0/L1/L2/L3 profile rankings are not a
clean self-identification instrument:

```text
L2 finite-window trends are explained or beaten by current-tiled controls.
L3 online-vs-reset trends are seed-block sensitive.
Reset parity can coexist with useful reactive driving.
```

The next gate must test causal history use directly. The core question is:

```text
When the current observation is matched, does changing command-response
history change action or closed-loop outcome in a source-diverse way?
```

This is stronger than comparing profile returns because it fixes the current
scene/current response and perturbs only the history channel.

## Existing Tool Path

M1215 should reuse the existing history-intervention stack before adding new
infrastructure:

```text
autodrift.matched_current_response_ambiguity
  Mines matched-current pairs with close current response/context but different
  future response targets.

autodrift.matched_history_intervention_gate
  Runs action-level variants:
    reset_hidden
    wrong_matched_history
    delayed_history
    zero_current_response
    zero_action_history

autodrift.persistent_wrong_history_intervention_gate
  Runs outcome-level variants:
    normal
    wrong_once
    wrong_hold_4 / 8 / 16
    wrong_late_* / wrong_reseed_4
    reset_hidden
    zero_current_response

autodrift.outcome_critical_matched_current_selector
  Selects matched-current rows where interventions cause terminal-margin,
  completion, collision, or success degradation.

autodrift.history_value_ablation_runner
  Summarizes L3-vs-level diagnostic outcomes on existing public surfaces.
```

Relevant prior evidence:

```text
M503: source-diverse natural boundary-pressure matched-current surface.
M524: natural surfaces produced event-level L3-vs-L0 history-value signal.
M537/M538: L3 has paired public natural-surface advantage over L0 and aggregate
           advantage over L2, with L3-L2 seed fragility.
M585-M587: BC5660 matched-current surfaces were source-diverse, but wrong or
           delayed hidden-state action effects were negative while current
           response and action-history controls were strong.
```

These results imply that M1215 should not assume wrong-history sensitivity will
exist. It should pre-register both positive and negative routes.

## Gate Definition

The causal history gate has three stages.

### Stage A: Matched-Current Surface

Mine or load pairs satisfying:

```text
current response/context distance is small;
future response target delta is large;
source coverage spans multiple probe seeds, obstacle buckets, left steps, and
targets;
actor input remains P0 human-view no-wheel no-oracle.
```

Recommended initial thresholds:

```text
accepted pairs >= 80
physical pairs >= 20
probe seeds >= 3
left steps >= 5
obstacle buckets >= 4
targets >= 2
max single probe-seed share <= 0.50
max single obstacle-bucket share <= 0.50
```

If existing M503/M524/M537/M538 artifacts cannot be made compatible with the
current corrected-profile checkpoints, M1216 should export a fresh surface
using the same public route family and current corrected checkpoints.

### Stage B: Action-Level Screen

Run action interventions on matched-current pairs:

```text
normal
reset_hidden
delayed_history
wrong_matched_history
zero_current_response
zero_action_history
current_tiled_control where profile-compatible
```

Action-level evidence is only a screen. It can admit outcome rollout if at
least one history-only intervention has non-trivial action effect:

```text
wrong_matched_history or delayed_history:
  action_distance_mean >= 0.01
  above_threshold_count >= 16 with threshold 0.02
  source coverage remains non-singleton
```

Positive controls:

```text
zero_current_response should usually be action-sensitive;
zero_action_history should reveal dependence on previous command slots;
current-tiled controls must remain separate from history-necessity claims.
```

If only zero-current-response or zero-action-history is sensitive, the result
supports current feedback dependence but not accumulated hidden-history
self-identification.

### Stage C: Outcome-Level Causal Gate

Run persistent outcome interventions only for surfaces that pass the Stage B
or have a separately justified near-boundary reason to proceed.

Primary variants:

```text
normal
reset_hidden
delayed_history
wrong_once
wrong_hold_4
wrong_hold_8
wrong_late_4_hold_4
wrong_reseed_4
zero_current_response
```

Primary outcome metrics:

```text
success_drop
collision_gap
obstacle_completion_drop
min_clearance_margin_gap
return_gap
first_action_distance
trajectory_action_distance
termination_reason histogram
```

A row is causal-history positive if:

```text
current match passes;
normal rollout succeeds or is safely near-boundary;
history intervention causes success drop, collision gap, obstacle completion
drop, or margin gap >= 0.03;
the degradation is not reproduced only by current-response ablation;
the row is not dominated by a single seed, bucket, target, or checkpoint.
```

Gate-level positive evidence requires:

```text
accepted outcome-critical rows >= 16
physical pairs >= 10
probe seeds >= 3
targets >= 2
at least one wrong/delayed-history family contributes rows
zero-current-response remains labeled as a positive control, not self-ID proof
```

## Interpretation Rules

Allowed claims from this gate:

```text
matched-current causal-history gate implemented;
history intervention changes action;
history intervention changes closed-loop outcome on public diagnostic surfaces;
negative evidence routes to task/curriculum or surface redesign.
```

Forbidden claims:

```text
paper-level self-identification proof;
private-holdout generalization;
GRU superiority over finite-window;
checkpoint promotion;
real-vehicle readiness;
strong belief-state interpretation from action distance alone.
```

## Failure Taxonomy

M1215 pre-registers these outcomes:

```text
no_matched_current_surface
  No source-diverse matched-current ambiguity can be found.
  Route: expand scenario/curriculum or mine more extreme cases.

current_feedback_only_signal
  zero_current_response or zero_action_history is sensitive, but wrong/delayed
  history is not.
  Route: record current-feedback dependence and redesign tasks that require
  accumulated history.

action_only_history_signal
  wrong/delayed history changes action but not terminal outcome.
  Route: mine nearer terminal-boundary rows before training.

source_narrow_history_signal
  outcome signal exists but is dominated by one seed, bucket, or target.
  Route: refresh source-diverse surface.

causal_history_positive_public_diagnostic
  source-diverse history-only intervention degrades outcome on public rows.
  Route: build matched train/eval corpus and later holdout protocol.
```

## M1216 Route

M1216 should be a source/tooling audit, not training.

It should answer:

```text
Which existing matched-current and history-intervention artifacts are
compatible with the current paper-route checkpoint families?

Can the existing M503/M524/M537/M538/M585-M587 path support M1215 directly, or
is a fresh current-family surface export needed?
```

M1216 deliverables:

```text
artifact inventory;
tool compatibility table;
recommended first causal-history run path;
whether to reuse existing public surfaces or export a fresh surface;
manifest for the first run milestone.
```

## Decision

```text
causal_history_gate_design_admit_source_audit
```

Next blocker:

```text
m1216-paper-route-causal-history-source-audit
```
