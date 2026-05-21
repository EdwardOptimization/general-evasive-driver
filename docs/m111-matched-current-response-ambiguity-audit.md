# M111 Matched Current-Response Ambiguity Audit

## Question

M109/M110 showed that the existing future-envelope probe is often solvable from
the current response frame. M111 asks a narrower question before another
objective sweep:

```text
Can we find states where current response and scene are close, but future
handling-envelope targets differ enough that a history/belief signal should be
needed?
```

This is a proof-surface audit, not a new driver candidate.

## Harness

Added:

```text
src/autodrift/matched_current_response_ambiguity.py
tests/test_matched_current_response_ambiguity.py
```

The harness:

1. collects frozen-policy hidden-envelope samples with
   `collect_hidden_envelope_dataset`;
2. matches samples on standardized `current_response + context`;
3. rejects same-episode pairs;
4. selects nearest visible pairs whose future-envelope target differs by at
   least a z-score threshold;
5. reports distances in current response, policy features, carried response
   hidden, reset response hidden, and full observation.

The actor input contract is unchanged. No hidden parameter or oracle label is
fed to the actor.

## Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --probe-seeds 9510 \
  --episodes 8 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 180 \
  --nearest-k 6 \
  --max-visible-quantile 0.10 \
  --min-target-z-delta 0.75 \
  --max-pairs-per-target 50 \
  --min-accepted-pairs 10 \
  --device cpu \
  --run-dir runs/m111_smoke_matched_current_response_ambiguity_seed9510
```

Result:

```text
candidate_pair_count: 2547
accepted_pair_count: 47
accepted_by_target:
  future_braking_deceleration: 21
  future_yaw_response: 18
  future_lateral_accel_response: 8
ambiguity_surface_found: true
```

## Formal Audit

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --probe-seeds 9510,9511 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --nearest-k 10 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 200 \
  --min-accepted-pairs 30 \
  --device cpu \
  --run-dir runs/m111_matched_current_response_ambiguity_seed9510
```

Artifacts:

```text
runs/m111_matched_current_response_ambiguity_seed9510/summary.json
runs/m111_matched_current_response_ambiguity_seed9510/candidate_pairs.csv
runs/m111_matched_current_response_ambiguity_seed9510/matched_pairs.csv
runs/m111_matched_current_response_ambiguity_seed9510/target_summary.csv
```

Top-level result:

```text
candidate_pair_count: 89343
accepted_pair_count: 702
accepted_by_target:
  future_braking_deceleration: 303
  future_yaw_response: 184
  future_lateral_accel_response: 215
ambiguity_surface_found: true
```

## Aggregate Readout

| target | accepted pairs | mean target z delta | mean visible distance | hidden-more-separated fraction | current corr | hidden corr |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| future_braking_deceleration | 303 | 1.385 | 0.194 | 0.554 | 0.056 | -0.097 |
| future_yaw_response | 184 | 1.819 | 0.191 | 0.475 | -0.065 | -0.382 |
| future_lateral_accel_response | 215 | 2.286 | 0.194 | 0.521 | 0.066 | -0.539 |

By checkpoint:

| checkpoint | accepted pairs | hidden-more-separated fraction | mean target z delta |
| --- | ---: | ---: | ---: |
| M62 | 227 | 0.457 | 1.952 |
| M102 | 242 | 0.545 | 1.771 |
| M105 | 233 | 0.549 | 1.767 |

## Interpretation

M111 found a useful ambiguity surface. The current simulator/task can produce
states where the current response plus visible scene are close but future
braking, yaw, or lateral envelope targets differ by more than one target
standard deviation.

However, the current recurrent hidden state is not admitted as the solution to
that ambiguity. On the accepted pairs, carried response hidden is only slightly
more separated than current response for braking and lateral, and not for yaw.
Its pair-distance correlation with the target delta is negative on all three
aggregate targets.

So the M110 blocker is now sharper:

```text
The proof surface exists, but current M62/M102/M105 hidden states do not
systematically encode the ambiguity.
```

## Decision

Status: completed, mixed negative.

M111 satisfies the audit requirement because matched-current-response rows were
mined and current-response/history feature comparisons were recorded. It does
not admit another PPO continuation or hidden objective by itself.

Next task: M112 should turn the M111 matched pairs into a stronger intervention
gate or training corpus. The key test should not be only feature distance; it
should replay matched pairs with normal, reset, delayed, zero-action, and wrong
matched histories and measure action or clearance degradation.
