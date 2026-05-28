# M1391 Paper-Route Causal History Source Miner Implementation

## Summary

M1391 implements and runs a no-training causal-history source miner.

Decision:

```text
causal_history_source_miner_structural_pass_admit_candidate_outcome_probe
```

M1391 performs no training, PPO, promotion, private holdout, actor-input
expansion, or training-corpus export.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.causal_history_source_miner \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv \
  --max-source-rows 768 \
  --per-fault-pair-cap 96 \
  --history-length 12 \
  --recent-window-length 2 \
  --device cpu \
  --run-dir runs/m1391_causal_history_source_miner
```

Artifacts:

```text
runs/m1391_causal_history_source_miner/summary.json
runs/m1391_causal_history_source_miner/candidate_rows.csv
runs/m1391_causal_history_source_miner/evaluated_rows.csv
runs/m1391_causal_history_source_miner/rejected_rows.csv
runs/m1391_causal_history_source_miner/distance_summary.csv
```

## Result

Run class:

```text
result_class: causal_history_source_structural_pass
structural_smoke_pass: true
```

Core counts:

```text
selected_source_rows: 768
evaluated_rows: 768
finite_metric_rows: 768
matched_current_pairs: 631
candidate_rows: 631
same_recent_window_candidates: 631
rejected_rows: 137
```

Guardrails:

```text
actor_parameters_changed: false
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

## Source Diversity

Candidate diversity:

```text
rows: 631
unique_source_seeds: 46
unique_fault_pairs: 9
unique_preferred_fault_families: 7
unique_wrong_fault_families: 5
max_single_seed_share: 0.04913
max_single_fault_pair_share: 0.15055
```

Structural thresholds from M1390:

| Metric | Threshold | Observed | Status |
| --- | ---: | ---: | --- |
| candidate rows | 200 | 631 | pass |
| matched-current pairs | 80 | 631 | pass |
| unique source seeds | 12 | 46 | pass |
| unique fault/capability pairs | 6 | 9 | pass |
| finite metric rows | all | 768 / 768 | pass |

M1391 therefore materializes enough source-diverse public candidates for the
next no-training intervention probe.

## Matching Diagnostics

Distance summary over all evaluated rows:

| Metric | Mean | P90 | P95 | Max |
| --- | ---: | ---: | ---: | ---: |
| ego response | 0.01397 | 0.05690 | 0.09109 | 0.13860 |
| actuator state | 0.01575 | 0.06968 | 0.09245 | 0.16118 |
| previous command | 0.00288 | 0.01008 | 0.01626 | 0.04737 |
| road boundary | 0.00292 | 0.00944 | 0.01794 | 0.05878 |
| obstacle position | 0.00053 | 0.00000 | 0.00000 | 0.20484 |
| scene context | 0.00243 | 0.00689 | 0.01310 | 0.14260 |
| full observation | 0.00679 | 0.02613 | 0.03333 | 0.13721 |
| recent window | 0.00670 | 0.02642 | 0.03240 | 0.13678 |
| older history | 0.00493 | 0.01869 | 0.02730 | 0.05217 |
| current hidden | 0.02024 | 0.07712 | 0.10404 | 0.23762 |

Important limitation:

```text
older_history_l2 is low in this source family.
```

The candidate rows are useful because current-frame matching and source
diversity are strong, not because M1391 itself proves older observation-history
divergence. Many candidates pass same-recent selection through fault-family
difference and reset sensitivity. The causal claim still depends on an
outcome-intervention probe that compares normal, delayed, wrong, reset, and
zero-current variants.

## Interpretation

Supported:

```text
1. The no-training source miner is implemented and runnable.
2. M1375 reset-only rows can be converted into source-diverse matched-current
   candidate rows for causal-history probing.
3. Current-frame matching is measurable from reconstructed full observations.
4. The source set is broad enough for a public candidate outcome probe.
```

Not supported:

```text
1. history necessity;
2. recurrent-belief advantage;
3. level3 self-identification;
4. training-corpus export;
5. checkpoint promotion;
6. paper-level evidence.
```

## Failure Taxonomy

No structural failure occurred.

The main risk is:

```text
metric_artifact risk if M1391 is overclaimed as history proof.
```

Mitigation:

```text
Treat M1391 as source materialization only. Require M1392 outcome-intervention
probe before any corpus export, training, or self-ID claim.
```

## Next Route

Admit:

```text
m1392-paper-route-causal-history-candidate-outcome-probe
```

M1392 should run no-training outcome interventions over M1391
`candidate_rows.csv`:

```text
normal
reset_hidden
delayed_history_4 / 8 / 12
wrong_same_current_history
same_recent_wrong_older_history
zero_current_response_positive_control
```

M1392 must report success drops, margin gaps, action distances, terminal reason
histograms, source diversity of accepted rows, and whether any accepted rows are
not merely reset-only or zero-current-response artifacts.

## Decision

```text
causal_history_source_miner_structural_pass_admit_candidate_outcome_probe
```

Next:

```text
m1392-paper-route-causal-history-candidate-outcome-probe
```
