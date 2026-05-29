# M1503 Paper-Route Decisive History Public Planner Smoke

## Summary

M1503 ran the M1502 no-training candidate planner at the public metadata-smoke
scale required by M1501.

Decision:

```text
decisive_history_public_planner_smoke_pass_admit_env_hook_design
```

This milestone does not run simulator replay, train, run PPO, promote, use
private holdout, export a corpus, change actor inputs, or claim simulator
candidate existence.

## Command

```bash
PYTHONPATH=src python -m autodrift.decisive_history_candidate_planner \
  --run-dir runs/m1503_decisive_history_public_planner_smoke \
  --seed-count 11
```

Output:

```text
summary=runs/m1503_decisive_history_public_planner_smoke/summary.json
generated_candidate_rows=66
accepted_count=66
```

## Threshold Audit

Pre-registered M1503 gates:

| Gate | Threshold | Result | Pass |
| --- | ---: | ---: | --- |
| generated candidate rows | >= 64 | 66 | yes |
| accepted rows | >= 16 | 66 | yes |
| accepted T4 rows | >= 4 | 33 | yes |
| accepted T5 rows | >= 4 | 33 | yes |
| unique seeds | >= 4 | 66 | yes |
| unique capability pairs | >= 4 | 8 | yes |
| unique reveal steps | >= 4 | 12 | yes |
| unique geometry keys | >= 4 | 12 | yes |
| max source share | <= 0.35 | 0.015151515151515152 | yes |
| validation errors | 0 | 0 | yes |

Source-family summary:

| Source family | Rows | Accepted | Task | Unique seeds | Capability pairs | Geometry keys |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| t4_actuator_delay_response | 11 | 11 | T4 | 11 | 2 | 2 |
| t4_capability_step_temporal | 11 | 11 | T4 | 11 | 2 | 2 |
| t4_staged_warmup_capability | 11 | 11 | T4 | 11 | 2 | 2 |
| t5_boundary_axis_retarget | 11 | 11 | T5 | 11 | 2 | 2 |
| t5_high_speed_close_obstacle | 11 | 11 | T5 | 11 | 2 | 2 |
| t5_near_boundary_warmup | 11 | 11 | T5 | 11 | 2 | 2 |

## Guardrails

```text
labels_enter_actor_input: false
private_holdout_used: false
actor_input_contract_changed: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
training_corpus_exported: false
level3_self_id_claim_made: false
```

## Interpretation

M1503 shows that the metadata source-plan layer can satisfy the public M1501
candidate-generation scale and diversity gates. It does not show that current
simulator rollouts can realize those T4/T5 decisive-history candidates.

The next milestone should design the current-sim env hooks needed to turn the
planner metadata into no-training simulator candidate-generation probes. That
design must keep replay, training, PPO, promotion, private holdout, actor-input
changes, and corpus export blocked.

## Artifacts

```text
runs/m1503_decisive_history_public_planner_smoke/source_plan_rows.csv
runs/m1503_decisive_history_public_planner_smoke/candidate_rows.csv
runs/m1503_decisive_history_public_planner_smoke/source_family_summary.csv
runs/m1503_decisive_history_public_planner_smoke/summary.json
```

## Next Route

Route to:

```text
m1504-paper-route-decisive-history-env-hook-design
```
