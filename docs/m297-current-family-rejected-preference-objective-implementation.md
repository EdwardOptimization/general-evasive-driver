# M297 Current-Family Rejected-Preference Objective Implementation

M297 implements the rejected-history preference objective designed in M296 and
runs exact no-PPO objective sanity. No PPO or actor update was run, no
checkpoint is promoted, and actor inputs are unchanged.

## What Changed

New implementation:

```text
src/autodrift/intervention_objectives.py
src/autodrift/rejected_history_preference_objective.py
tests/test_rejected_history_preference_objective.py
```

The new corpus schema adds `rejected_action` and row-level labels to the
existing outcome-intervention inputs:

```text
observation
preferred_hidden
rejected_hidden
preferred_action
rejected_action
preferred_score
rejected_score
score_delta
normal_margin
wrong_history_margin
margin_floor
weight
row_id
group_index
target_index
```

The exact loss compares the same observation under correct and wrong histories:

```text
logp_cp = log pi(preferred_action | observation, preferred_hidden)
logp_wp = log pi(preferred_action | observation, rejected_hidden)
logp_wr = log pi(rejected_action  | observation, rejected_hidden)

L_pref_separation = softplus(logp_wp - logp_cp + m_pref)
L_wrong_preference = softplus(logp_wp - logp_wr + m_wrong)
L = weighted_mean(L_pref_separation + L_wrong_preference)
```

This is deliberately not a stronger trajectory action anchor. The rejected
action is preferred only under the wrong-history hidden state.

## Exact Objective Sanity

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.rejected_history_preference_objective --checkpoint-policy m290x64_a500=runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt --checkpoint-policy m291raw=runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt --checkpoint-policy m294raw=runs/ppo_m294_current_family_rejected_repair_smoke_seed5232/checkpoint.pt --source-npz runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz --source-csv runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv --base-replay-csv runs/m294_current_family_rejected_repair_ppo_smoke/gates/raw_m267_m264/boundary_replay_rows.csv --base-policy m290x64_a500 --failed-row-ids 6,15,16 --recovered-row-ids 11 --failed-row-bonus 4.0 --recovered-row-bonus 2.0 --max-weight 100.0 --device cpu --run-dir runs/m297_current_family_rejected_preference_objective
```

Artifacts:

```text
runs/m297_current_family_rejected_preference_objective/summary.json
runs/m297_current_family_rejected_preference_objective/policy_summary.csv
runs/m297_current_family_rejected_preference_objective/per_row_losses.csv
runs/m297_current_family_rejected_preference_objective/focused_row_losses.csv
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.csv
```

Policy summary:

| Policy | Exact weighted loss | Preferred separation mean | Wrong preference mean |
| --- | ---: | ---: | ---: |
| m290x64_a500 | 1.191800 | 0.688732 | 0.714810 |
| m291raw | 1.192550 | 0.689222 | 0.715312 |
| m294raw | 1.192730 | 0.689327 | 0.715421 |

The base ranks ahead of both PPO washout checkpoints:

```text
m291raw - m290x64_a500 = +0.000750
m294raw - m290x64_a500 = +0.000930
```

## Focused Rows

Rows 6, 15, and 16 are the M294 failed rows; row 11 is the M294 recovered row.
All four focused rows have per-row diagnostics in
`focused_row_losses.csv`.

| Row | m290 loss | m291 raw loss | m294 raw loss |
| ---: | ---: | ---: | ---: |
| 6 | 1.398588 | 1.399482 | 1.399719 |
| 11 | 1.347050 | 1.348104 | 1.348348 |
| 15 | 1.426355 | 1.426871 | 1.427026 |
| 16 | 1.427472 | 1.427990 | 1.428093 |

The row-level signal is aligned with the aggregate result: both PPO washout
checkpoints are worse than M290 on the focused proof rows.

## Interpretation

M297 is a qualified positive. It satisfies the M296 sanity requirement because
the new preference loss ranks the current M290 public-gate base below both PPO
washout checkpoints and reports the required focused rows.

The margin is small, so this does not justify PPO. It only admits a no-PPO
objective-only update or projection probe to test whether the gradient is useful
without breaking replay gates.

## Decision

Decision:

```text
admit_no_ppo_rejected_preference_objective_only_probe
```

Next step:

```text
m298-rejected-preference-objective-only-probe
```
