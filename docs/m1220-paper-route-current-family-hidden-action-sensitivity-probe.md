# M1220 Paper-Route Current-Family Hidden-Action Sensitivity Probe

## Summary

M1220 probes whether the M1212 corrected L3 online-GRU actors have an action
path from recurrent hidden state after M1218 found no real wrong/delayed
matched-history action signal.

Decision:

```text
hidden_path_exists_but_real_matched_histories_are_action_equivalent
```

No outcome intervention, training, PPO, checkpoint repair, promotion, private
holdout, profile tuning, or actor-input change occurs in M1220.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_hidden_action_sensitivity_probe \
  --checkpoint-policy l3_s111600=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt \
  --checkpoint-policy l3_s111601=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --pairs-csv runs/m1217_current_family_matched_current_export/matched_pairs.csv \
  --surface m1217_current_family \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-target 120 \
  --pair-label-mode matching \
  --device cpu \
  --run-dir runs/m1220_current_family_hidden_action_sensitivity_probe
```

Artifacts:

```text
runs/m1220_current_family_hidden_action_sensitivity_probe/summary.json
runs/m1220_current_family_hidden_action_sensitivity_probe/variant_summary.csv
runs/m1220_current_family_hidden_action_sensitivity_probe/correlation_summary.csv
runs/m1220_current_family_hidden_action_sensitivity_probe/action_sensitivity_rows.csv
runs/m1220_current_family_hidden_action_sensitivity_probe/weight_chunk_summary.csv
```

## Run Counts

```text
input matched pairs:       762
action rows:              8382
variant summary rows:       99
correlation summary rows:   99
weight summary rows:         3
skipped labels:              0
```

## Actor Fusion Weight Audit

The final fusion layer assigns comparable norm to hidden, context, and
hidden-context interaction chunks:

| Checkpoint | Hidden Share | Context Share | Interaction Share |
| --- | ---: | ---: | ---: |
| `l3_s111600` | `0.334327` | `0.335129` | `0.330544` |
| `l3_s111601` | `0.335236` | `0.334500` | `0.330264` |
| `l3_s111602` | `0.333810` | `0.337658` | `0.328532` |

This is only a structural check. It says the actor has a hidden path; it does
not prove that natural history differences are behaviorally necessary.

## Aggregate Variant Results

Action distance threshold:

```text
0.02
```

| Variant | Hidden Mean | Action Mean | Action P90 | Max Action | Above Threshold | Wrong Closer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `random_hidden_unit` | `2.582879` | `0.057720` | `0.086297` | `0.158012` | `713` | `0.000000` |
| `reset_hidden` | `1.842438` | `0.041795` | `0.044901` | `0.080238` | `629` | `0.000000` |
| `scaled_hidden_2_0` | `1.842438` | `0.038319` | `0.041472` | `0.079167` | `509` | `0.000000` |
| `scaled_hidden_0_5` | `0.921219` | `0.020578` | `0.022145` | `0.040174` | `270` | `0.000000` |
| `scaled_hidden_1_5` | `0.921219` | `0.019678` | `0.021260` | `0.039881` | `270` | `0.000000` |
| `zero_current_response` | `0.000000` | `0.017431` | `0.018817` | `0.021021` | `20` | `0.000000` |
| `zero_action_history` | `0.000000` | `0.013854` | `0.014237` | `0.015767` | `0` | `0.000000` |
| `random_hidden_fit` | `0.348715` | `0.007282` | `0.013778` | `0.082557` | `13` | `0.000000` |
| `shuffled_history` | `0.107201` | `0.002597` | `0.007982` | `0.082572` | `14` | `0.000000` |
| `wrong_matched_history` | `0.044677` | `0.001075` | `0.001673` | `0.002415` | `0` | `0.891076` |
| `delayed_history` | `0.007916` | `0.000154` | `0.000212` | `0.015598` | `0` | `0.000000` |

## Checkpoint Split

The positive off-manifold/reset controls are not from a single checkpoint:

| Variant | `l3_s111600` Action / Above | `l3_s111601` Action / Above | `l3_s111602` Action / Above |
| --- | ---: | ---: | ---: |
| `reset_hidden` | `0.028094 / 239` | `0.019633 / 120` | `0.073236 / 270` |
| `random_hidden_unit` | `0.039320 / 217` | `0.047862 / 223` | `0.082412 / 273` |
| `scaled_hidden_2_0` | `0.028140 / 239` | `0.009490 / 0` | `0.072570 / 270` |

The real-history variants stay action-equivalent for every checkpoint:

| Variant | `l3_s111600` Action / Above | `l3_s111601` Action / Above | `l3_s111602` Action / Above |
| --- | ---: | ---: | ---: |
| `wrong_matched_history` | `0.000941 / 0` | `0.000827 / 0` | `0.001410 / 0` |
| `delayed_history` | `0.000231 / 0` | `0.000059 / 0` | `0.000171 / 0` |
| `shuffled_history` | `0.001444 / 4` | `0.001767 / 2` | `0.004331 / 8` |

## Target Split

The same pattern holds for the two dense targets:

| Target | Wrong Action / Above | Delayed Action / Above | Reset Action / Above | Random Unit Action / Above |
| --- | ---: | ---: | ---: | ---: |
| `future_braking_deceleration` | `0.001001 / 0` | `0.000070 / 0` | `0.041675 / 324` | `0.058014 / 340` |
| `future_yaw_response` | `0.001135 / 0` | `0.000248 / 0` | `0.040101 / 272` | `0.055312 / 332` |
| `future_lateral_accel_response` | `0.001199 / 0` | `0.000069 / 0` | `0.057337 / 33` | `0.075834 / 41` |

The lateral target is still underrepresented at 42 pairs, so it should not be
used as the main interpretation anchor.

## Interpretation

M1220 falsifies the simple explanation that the actor head cannot use recurrent
hidden state at all. Reset, scaled, and random hidden perturbations produce
large action shifts, and the fusion layer structurally gives hidden comparable
weight to context.

M1220 also confirms the M1218 negative result for the actual current-family
matched histories:

```text
wrong_matched_history: action-equivalent
delayed_history:       action-equivalent
shuffled_history:      mostly action-equivalent
```

Therefore the current M1217 source is not yet a usable causal-history outcome
gate source. It is future-response ambiguous, but it is not action-critical for
these actors.

## Blocked Claim

Do not claim:

```text
the actor performs online self-identification from real command-response history
```

The strongest supported claim is narrower:

```text
the actor has a functional hidden path, but the current natural matched
histories are too close or too action-equivalent to prove history necessity.
```

## Selected Next Route

Do not run persistent wrong-history outcome rollout from M1217/M1220 rows.

The next route is an action-critical hidden-history source mining design. It
should inspect and choose among existing source-mining tools before running a
new gate:

```text
autodrift.natural_wrong_history_action_sensitive_selector
autodrift.adversarial_wrong_history_pair_search
autodrift.action_divergent_wrong_history_corpus
autodrift.action_critical_wrong_history_source_miner
```

The next milestone should answer:

```text
Which current-family or cross-family source can produce source-diverse
matched-current pairs where real wrong/delayed/shuffled histories cause
above-threshold action differences before any outcome rollout is attempted?
```

## Decision

```text
hidden_path_exists_but_real_matched_histories_are_action_equivalent
```

Next blocker:

```text
m1221-paper-route-action-critical-hidden-source-design
```
