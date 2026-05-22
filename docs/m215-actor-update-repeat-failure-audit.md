# M215 Actor-Update Repeat Failure Audit

M215 audits why M214 repeats improved the fixed M212 objective but failed replay
normal-success retention. No PPO was run. No actor update was run in this
milestone.

## Claim Triage

| Claim | Status | Evidence | Action |
| --- | --- | --- | --- |
| M214 is a real failure, not a logging artifact | confirmed | M214 replay gates fail on old M183, refreshed M193, and current M212 surfaces | reject M214 |
| The failure is global behavior collapse | rejected | behavior seeds `9505` and `9506` still keep success `0.8625`; protected key still passes | focus on boundary replay |
| Fixed M212 objective improvement predicts replay retention | rejected | M214 `10052` has best fixed loss but worse replay than M213 | do not promote by objective alone |
| Generic action anchor protects boundary snippets | rejected | anchor MSE stays small, but boundary normal margins become negative | add snippet-level protection |

## Artifacts Inspected

- `docs/m213-m212-guarded-actor-update.md`
- `docs/m214-m212-actor-update-repeat.md`
- `runs/m213_m204_actor_coupling_anchor100_s20_seed10050/summary.json`
- `runs/m214_m204_actor_coupling_anchor100_s20_seed10051/summary.json`
- `runs/m214_m204_actor_coupling_anchor100_s20_seed10052/summary.json`
- `runs/m214_fixed_batch_outcome_eval_seed37/summary.json`
- `runs/m213_m212_m204_replay_gate_seed10040/boundary_replay_rows.csv`
- `runs/m214_10051_m212_m204_replay_gate_seed10040/boundary_replay_rows.csv`
- `runs/m214_10052_m212_m204_replay_gate_seed10040/boundary_replay_rows.csv`
- old M183 and refreshed M193 replay summaries for M213/M214
- `src/autodrift/outcome_intervention_optimize.py`
- `src/autodrift/intervention_objectives.py`

## Objective Results

All three actor-update runs restart from M204:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

All use the same M212 M204 corpus:

```text
runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.npz
```

| Candidate | Seed | Fixed M212 loss | Fixed improvement vs M204 | Replay result |
| --- | ---: | ---: | ---: | --- |
| m213_s20 | 10050 | 0.201354 | 0.003867 | pass |
| m214_10051 | 10051 | 0.201478 | 0.003743 | fail |
| m214_10052 | 10052 | 0.200899 | 0.004322 | fail |

M214 `10052` has the best fixed objective but still fails replay. The fixed
contrast objective is therefore not sufficient as a promotion metric.

## Replay Failure Shape

On the current M212 replay surface:

| Policy | Normal success | Wrong-history success | Success drops | Mean normal margin | Mean margin gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| m204_5209 | 17 / 17 | 0 / 17 | 17 / 17 | 0.006191 | 0.009023 |
| m213_s20 | 17 / 17 | 0 / 17 | 17 / 17 | 0.004568 | 0.008981 |
| m214_10051 | 5 / 17 | 0 / 17 | 5 / 17 | 0.000115 | 0.008327 |
| m214_10052 | 7 / 17 | 0 / 17 | 7 / 17 | 0.001087 | 0.008324 |

The wrong-history side remains collision-producing. The failure is that the
normal-history side loses its tiny near-boundary clearance margin.

The same pattern appears on old replay surfaces. For M183 M168:

| Policy | Normal success | Wrong-history success | Success drops | Mean normal margin |
| --- | ---: | ---: | ---: | ---: |
| m204_5209 | 16 / 16 | 0 / 16 | 16 / 16 | 0.004036 |
| m214_10051 | 3 / 16 | 0 / 16 | 3 / 16 | -0.002602 |
| m214_10052 | 3 / 16 | 0 / 16 | 3 / 16 | -0.001593 |

## Action Drift

Direct snippet preferred-action evaluation on the M212 corpus shows that the
relative outcome objective can move the normal/preferred action away from the
M204 action while still improving contrast loss.

Preferred-hidden action MSE versus M204 preferred action:

| Policy | Mean MSE | Max MSE | Mean delta steer | Mean delta throttle | Mean delta brake |
| --- | ---: | ---: | ---: | ---: | ---: |
| m213_s20 | 0.000102 | 0.000154 | -0.007167 | 0.011791 | 0.010178 |
| m214_10051 | 0.000132 | 0.000164 | -0.006440 | 0.017744 | 0.005705 |
| m214_10052 | 0.000148 | 0.000198 | -0.008029 | 0.017493 | 0.007899 |

Replay first-action deltas versus M204 on the M212 surface:

| Policy | Mean normal action L2 | Mean normal margin delta | Normal failures |
| --- | ---: | ---: | ---: |
| m213_s20 | 0.019896 | -0.001623 | 0 / 17 |
| m214_10051 | 0.022604 | -0.006076 | 12 / 17 |
| m214_10052 | 0.024140 | -0.005104 | 10 / 17 |

M214's normal-action shift is small in aggregate, but the replay rows are
knife-edge cases. A few thousandths of clearance margin are enough to flip many
rows from success to collision.

## Mechanism

The current loss is a relative contrast:

```text
softplus(rejected_log_prob(preferred_action)
         - preferred_log_prob(preferred_action)
         + margin)
```

This can improve by reducing rejected-history logprob more than preferred-history
logprob, even if the preferred action mean drifts away from M204. M213 happened
to stay within the near-boundary margin budget. M214 repeats did not.

The generic action anchor samples rollout states from
`configs/m121_human_view_zero_obstacle_relvel.json`; it does not specifically
anchor the M212 boundary snippets. M214's generic anchor MSE remains small:

| Policy | Generic action-anchor MSE |
| --- | ---: |
| m213_s20 | 0.000017875 |
| m214_10051 | 0.000022536 |
| m214_10052 | 0.000027340 |

That is not enough to protect the actual proof rows.

## Decision

M215 confirms the M214 failure mechanism:

```text
contrast_objective_improves_but_preferred_boundary_action_drift_breaks_normal_success
```

Do not run PPO. Do not chain from M213 or M214. Keep M204 as the retained base:

```text
runs/ppo_m204_stage5_from_m202_seed5209/checkpoint.pt
```

## Next Experiment

Pre-register M216:

```text
m216-snippet-anchored-actor-update-calibration
```

M216 should use the same M204 init and M212 corpus but change the actor-update
recipe:

- lower step count from `20` to `10`;
- lower learning rate from `0.0001` to `0.00005`;
- keep generic action anchor against M204;
- add preferred-only snippet action anchor against M204 on the M212 corpus;
- repeat on the known failing seeds `10051` and `10052`;
- require old M183, refreshed M193, and current M212 replay retention before any
  behavior/protected-key promotion check.

If M216 cannot retain replay on both seeds, the actor-update recipe remains
blocked and the next step should be objective redesign, not PPO.
