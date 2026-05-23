# M468 Near-Boundary Task-Family Redesign

## Purpose

M468 selects the next implementation path after M467 showed that the current
wrong-history surface has near-boundary states but no wrong-history outcome
effect. The goal is to avoid retuning selector thresholds and instead change
how wrong histories are constructed.

No training, PPO, checkpoint update, actor-input change, or checkpoint
promotion is performed.

## M467 Failure Mode

M467 classified the M465 wrong-history candidate rows as:

```text
wrong-history rows:             199
near-boundary candidates:        35
proof candidates:                 0
near-boundary no-effect rows:    35
high-slack diagnostics:           7
```

The near-boundary rows are not empty:

```text
drift_required: 20
unavoidable:    15
probe seeds:    10200, 10300, 10400
```

But wrong history does not degrade these rows. The only positive margin rows
are high-slack `aes_feasible` diagnostics with normal margin above `3.5 m`.

## Diagnosis

### 1. The left states are useful; the injected histories are weak

M467 proves that the branch contains low normal-margin states. Those states are
good anchors for self-ID proof. The failure is that the chosen right-side
history does not alter the actor enough to change outcome.

### 2. One matched right history per left state is too weak

M464 selected one source-diverse targeted pair per row under broad diversity
caps. That is good for triage, but not adversarial enough for proof. For each
near-boundary left state, the full `candidate_pairs.csv` pool often contains
many possible right histories. The next step should search those alternatives.

### 3. The next branch should be adversarial but still human-view safe

The search can use offline mining metadata such as `target_z_delta`,
`response_hidden_minus_current_response_distance`, labels, and visible
distance. None of these enter the actor. They only choose which already
recorded matched-current pair to probe.

## Redesign

Implement an adversarial wrong-history pair search over:

```text
near-boundary left states:
  runs/m467_near_boundary_wrong_history_selector/near_boundary_no_effect.csv

full matched-current candidate pool:
  runs/m462_late_reveal_matched_current_fresh_seed10200/candidate_pairs.csv
```

The search should join by:

```text
probe_seed
target
left_seed
left_step
```

and then rank all possible right histories for that left state.

Hard filters:

```text
target_z_delta >= 1.0
visible_distance <= row visible_threshold
left_episode != right_episode
normal_margin from near-boundary anchor:
  0 < normal_margin <= 0.75
```

Adversarial score:

```text
score =
  response_hidden_minus_current_response_distance
+ response_hidden_more_separated_than_current_response bonus
+ target_z_delta
+ visible similarity bonus
+ right label disagreement / high-dynamics-contrast bonus
```

The output should preserve source diversity but prefer the strongest wrong
history per low-margin left state.

Expected artifacts:

```text
runs/m469_adversarial_wrong_history_pair_search/adversarial_pairs.csv
runs/m469_adversarial_wrong_history_pair_search/search_candidates.csv
runs/m469_adversarial_wrong_history_pair_search/summary.json
```

## M469 Pass Criteria

M469 should pass if it exports a source-diverse adversarial pair surface:

```text
adversarial_pairs >= 64
near_boundary_left_state_count >= 16
probe_seed_count >= 3
left_obstacle_label_count >= 2
target_count >= 2
single_seed_share <= 0.50
single_label_share <= 0.70
```

M469 still does not prove self-ID. If M469 passes, M470 should run action and
outcome gates on those adversarial pairs. If M469 fails, the M457 late-reveal
family is likely exhausted and the next redesign should modify scenario
generation itself.

## Decision

```text
admit_m469_adversarial_wrong_history_pair_search
```

Do not run PPO. First search for stronger wrong histories for already
near-boundary left states.
