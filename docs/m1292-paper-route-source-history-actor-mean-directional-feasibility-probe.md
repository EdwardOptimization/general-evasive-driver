# M1292 Paper-Route Source-History Actor-Mean Directional Feasibility Probe

## Summary

M1292 implements and runs the no-PPO actor-mean directional feasibility probe
designed in M1291.

Decision:

```text
source_history_actor_mean_directional_feasibility_mixed_route_to_result_audit
```

Result class:

```text
source_history_actor_mean_directional_feasibility_mixed
```

M1292 is a mixed diagnostic result. It shows that actor_mean-only is not a
complete dead end, because some rows become both-positive, but it is also not
strong enough for PPO, promotion, or public replay escalation.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_directional_feasibility_probe.py
```

Result:

```text
1 passed in 1.67s
```

Probe:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_directional_feasibility_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --m1288-checkpoint runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1292_source_history_actor_mean_directional_feasibility_probe \
  --device cpu \
  --steps 300 \
  --lr 0.0003 \
  --target-margin 0.05
```

## Implementation

Added:

```text
src/autodrift/source_history_directional_feasibility_probe.py
tests/test_source_history_directional_feasibility_probe.py
```

The probe:

```text
loads the M1154 base checkpoint;
loads the M1288 diagnostic checkpoint as a second initialization;
replays M1280 histories through the fixed recurrent actor;
keeps only actor_mean trainable;
optimizes a row-wise directional min-margin loss;
writes candidate summaries, directional rows, train trace, and diagnostic checkpoints;
does not run PPO or promote.
```

## Candidate Results

Base initialization:

```text
both_directional_fraction: 0.1578947368
both_positive_count: 24
mutually_exclusive_fraction: 0.7631578947
min_margin_mean: -0.3929710263
min_margin_p10: -1.8836293221
candidate_class: actor_mean_directional_mixed
```

M1288 initialization:

```text
both_directional_fraction: 0.1842105263
both_positive_count: 28
mutually_exclusive_fraction: 0.7763157895
min_margin_mean: -0.3045456347
min_margin_p10: -1.8071264267
candidate_class: actor_mean_directional_mixed
```

Best candidate:

```text
best_init_name: m1288_init
best_candidate_class: actor_mean_directional_mixed
best_both_directional_fraction: 0.1842105263
best_both_positive_count: 28
best_mutually_exclusive_fraction: 0.7763157895
best_min_margin_mean: -0.3045456347
best_min_margin_p10: -1.8071264267
```

## Guardrails

Mutation guard:

```text
any_non_actor_mean_mutation_detected: false
```

Blocked shortcuts:

```text
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
labels_enter_actor_input: false
```

## Interpretation

M1292 rules out the strongest negative interpretation:

```text
actor_mean-only is not completely incapable of changing directional row signs.
```

It also rules out immediate success:

```text
The best candidate reaches only 28/152 both-positive rows and leaves 118/152
rows mutually exclusive.
```

Therefore the result is mixed:

```text
Fixed source-history features contain some directional signal, but the current
actor_mean-only min-margin probe is not sufficient to repair the source-history
gate.
```

## Decision

Do not promote:

```text
diagnostic checkpoints are not driver checkpoints.
```

Do not start PPO:

```text
best_both_directional_fraction is only 0.1842105263.
```

Do not immediately escalate to public replay gates:

```text
the source-history directional relation remains weak.
```

Next:

```text
m1293-paper-route-source-history-actor-mean-feasibility-result-audit
```

M1293 should decide whether to route to:

```text
pair-group directional objective design;
trainable-scope escalation design;
or corpus relabel/refresh audit.
```

The recommended next step from the run is:

```text
route to pair-group directional objective design
```

## Claim Discipline

M1292 supports:

```text
Actor_mean-only directional optimization can create a partial both-positive
signal on the public source-history rows.
```

M1292 does not support:

```text
actor_mean-only feasibility as solved;
PPO readiness;
promotion;
closed-loop driver improvement;
paper-level evidence;
level3 anticipatory self-identification.
```

PPO and promotion remain blocked.
