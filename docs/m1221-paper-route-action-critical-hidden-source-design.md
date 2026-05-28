# M1221 Paper-Route Action-Critical Hidden Source Design

## Summary

M1221 audits existing action-critical and wrong-history source-mining tools
after M1220 found this split:

```text
functional hidden path: yes
real current-family wrong/delayed matched-history action signal: no
```

Decision:

```text
select_current_family_normal_success_boundary_source_smoke
```

No source mining run, outcome intervention, training, PPO, checkpoint repair,
promotion, private holdout, profile tuning, or actor-input change occurs in
M1221.

## Evidence From M1220

M1220 ruled out one simple explanation:

```text
the actor head cannot use recurrent hidden state
```

Positive controls:

| Variant | Action Mean | Above Threshold |
| --- | ---: | ---: |
| `random_hidden_unit` | `0.057720` | `713` |
| `reset_hidden` | `0.041795` | `629` |
| `scaled_hidden_2_0` | `0.038319` | `509` |

Real-history variants:

| Variant | Action Mean | Above Threshold |
| --- | ---: | ---: |
| `wrong_matched_history` | `0.001075` | `0` |
| `delayed_history` | `0.000154` | `0` |
| `shuffled_history` | `0.002597` | `14` |

Interpretation:

```text
The actor can react to hidden state, but the M1217 current-family matched
histories are not action-critical enough for causal-history outcome rollout.
```

## Tool Audit

### `natural_wrong_history_action_sensitive_selector`

Purpose:

```text
Re-score existing matched-current pairs at decision offsets and short-horizon
wrong-history continuations.
```

Strengths:

- consumes a candidate-pairs CSV directly;
- can test offsets such as `0,2,4,8`;
- records first-action and short-horizon trajectory distance.

Limitation for the current blocker:

```text
It still starts from M1217-like matched-current pairs. M1218/M1220 already show
that this source is weak for real wrong/delayed history action signal.
```

Use as fallback only if a cheap offset sweep is needed. Do not make it the next
main route.

### `adversarial_wrong_history_pair_search`

Purpose:

```text
Given near-boundary anchors plus a larger candidate-pair pool, search stronger
wrong histories for those anchors.
```

Strengths:

- useful when a near-boundary outcome CSV already exists;
- can keep source caps over anchor, seed, target, label, and obstacle bucket.

Limitation for the current blocker:

```text
M1217/M1220 did not produce current-family near-boundary outcome anchors.
Using this now would require another outcome source first.
```

Not selected for M1222.

### `action_divergent_wrong_history_corpus`

Purpose:

```text
Turn matched-current pairs into preferred/rejected action-sequence rows by
replaying normal and wrong-history branches.
```

Strengths:

- produces an explicit NPZ corpus contract;
- checks action-sequence and margin thresholds;
- useful after a better matched source exists.

Limitation for the current blocker:

```text
It is a corpus converter, not a new source generator. Running it on M1217 rows
would likely reproduce M1220's action-equivalence result.
```

Keep it downstream, not first.

### `action_critical_wrong_history_source_miner`

Purpose:

```text
Build a broader snapshot bank and search compatible wrong histories by action
and outcome evidence.
```

Relevant precedent:

```text
M664 found larger action gaps than M661 but accepted 0 rows because the
action-divergent windows were already failed under normal history.
```

Strengths:

- broad source generation;
- action/outcome-first scoring;
- preserves actor input contract.

Limitation:

```text
Without a normal-success prepass, it can waste budget on too-late or
already-failed source windows.
```

Not selected as the immediate M1222 route.

### `normal_success_boundary_source_miner`

Purpose:

```text
Build a broad decision-window snapshot bank, replay normal history first, keep
only normal-success near-boundary left snapshots, then test compatible wrong
histories for action/outcome divergence.
```

Relevant precedent:

```text
M667 proved this source order can find valid normal-success near-boundary
windows, even though the older BC5660 actor still lacked outcome sensitivity.
```

Why it is the best current route:

```text
M1220 says the actor has a hidden path, but the M1217 source is not
action-critical. M1222 should therefore search a broader current-family source
with normal-success boundary filtering before any outcome gate or training.
```

Selected.

### Extreme/fault scenario corpus

Purpose:

```text
Generate explicit cross-fault / capability-step dynamics scenarios.
```

Strengths:

- relevant to the long-term extreme-dynamics research route;
- can create stronger hidden-condition differences than natural same-family
  histories.

Limitation for the immediate causal-history gate:

```text
It changes the source distribution before we have exhausted a current-family
normal-success boundary source screen.
```

Use as fallback if current-family normal-success boundary mining is negative.

## Selected M1222 Route

Run a current-family normal-success boundary source smoke with the M1212 L3
checkpoint that showed the strongest hidden-action sensitivity in M1220:

```text
runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
```

Use a fresh public seed range:

```text
122700:122763
```

Use the corrected L3 online-GRU config:

```text
configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
```

M1222 should:

1. build a broad obstacle-visible decision-window bank;
2. replay normal history first;
3. keep only normal-success near-boundary source windows;
4. pair compatible wrong histories from the same current-family surface;
5. accept only rows with sustained action-sequence and margin/success evidence.

## Pre-Registered M1222 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --surface-config l3_current=configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --surface-seed-range l3_current=122700:122763 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 45.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 96 \
  --max-candidate-pairs-per-surface 2400 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 768 \
  --max-snapshots-per-seed 8 \
  --sample-stride 3 \
  --max-continuation-steps 12 \
  --device cpu \
  --run-dir runs/m1222_current_family_normal_success_boundary_source_smoke
```

## M1222 Pass Criteria

M1222 should pass source mining only if:

```text
near_boundary_preferred_snapshots >= 40
accepted_rows >= 40
accepted_physical_pairs >= 8
accepted_left_seeds >= 6
accepted_right_seeds >= 6
source_holdout_nonempty == true
mean_preferred_vs_rejected_action_mean_l2 >= 0.010
mean_margin_gap >= 0.010 or accepted_success_drop_rate >= 0.25
actor checksum unchanged
no actor checkpoint written
no optimizer/PPO used
```

If these fail, M1222 must classify the failure:

```text
no_near_boundary_normal_success_windows
near_boundary_exists_but_no_action_gap
near_boundary_action_gap_but_no_outcome_gap
source_diversity_failure
```

## Rejected Shortcuts

Do not:

- run persistent outcome rollout from M1217 rows;
- train from reset/random/scaled hidden perturbations;
- weaken action or margin thresholds inside M1222;
- promote any checkpoint;
- use private holdout;
- add hidden/oracle actor inputs;
- claim self-identification from M1222 source mining alone.

## Decision

```text
select_current_family_normal_success_boundary_source_smoke
```

Next blocker:

```text
m1222-paper-route-current-family-normal-success-boundary-source-smoke
```
