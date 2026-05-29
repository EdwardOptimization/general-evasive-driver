# M1491 Paper-Route Neighbor Viability Replay Result Audit

## Summary

M1491 audits the M1490 calibrated neighbor-viability bounded replay result.

Decision:

```text
neighbor_viability_replay_audit_source_singleton_control_sensitive_pivot_to_go_no_go_matrix
```

Failure type:

```text
scenario_sampling_failure
```

M1491 does not run replay, train, run PPO, promote, use private holdout, export
corpus, or change actor inputs.

## Audit Finding

M1490 succeeded as a bounded replay smoke:

```text
selected_candidate_rows: 68
actual_replay_rows: 204
history_positive_rows: 7
control_positive_rows: 12
normal_failed_rows: 147
```

The actual replay set was source-diverse:

```text
actual_replay_unique_source_seeds: 5
actual_replay_unique_capability_pairs: 6
actual_replay_unique_reveal_buckets: 6
actual_replay_unique_variants: 5
max_single_seed_share: 0.352941
max_single_capability_pair_share: 0.176471
```

But the history-positive rows did not become source-diverse:

```text
history_positive_unique_source_seeds: 1
history_positive_unique_capability_pairs: 1
history_positive_unique_reveal_buckets: 1
history_positive_unique_variants: 1
max_single_seed_share: 1.0
max_single_capability_pair_share: 1.0
```

All history positives remain one source family:

```text
seed: 141901
source_index: 24
capability_pair: brake_authority_drop->mass_cg_shift
reveal_bucket: vx6|yaw-2|steer-4|ox0|oy0
variant: warmup_removed
```

The control positives are also concentrated on the same family:

```text
control_positive_rows: 12
control_positive_unique_source_seeds: 1
control_positive_unique_capability_pairs: 1
control_positive_unique_reveal_buckets: 1
control_positive_unique_variants: 2
control_variants: reset_hidden, zero_current_response
```

## Candidate Versus Positive Split

The selected candidate set did include neighbor-source pressure:

```text
selected_candidate_rows: 68
selected_neighbor_source_rows: 60
selected_original_source_rows: 8
selected_viability_classes:
  too_hard: 36
  too_easy: 24
  near_boundary: 8
```

The replay stage therefore tested a diverse candidate pool, but the positives
collapsed back to the original near-boundary source family. The source-diverse
neighbor rows mostly failed to become normal-viable, outcome-critical
history-positive rows.

The important distinction is:

```text
actual replay diversity: present
history-positive source diversity: absent
control-positive source diversity: absent
```

## Interpretation

Supported:

```text
The calibrated neighbor-viability route can generate geometry-valid replay rows.
The M1490 replay is live and can produce history-positive rows.
The original local boundary family remains a real outcome-sensitive surface.
```

Unsupported:

```text
M1490 provides source-diverse history-positive replay evidence.
M1490 positives are ready for corpus export, training, PPO, or promotion.
M1490 supports paper-level recurrent belief or level3 self-identification.
The source-diverse pressure branch should continue with another replay loop.
```

The same source family produces both history positives and reset/zero-current
controls. This does not invalidate the local evidence, but it blocks stronger
claims: the outcome can still be explained by a fragile local terminal boundary
or current-response/control intervention sensitivity rather than source-diverse
accumulated-history necessity.

## Hard Stop

M1488 pre-registered a hard stop:

```text
After the next replay audit, if positives remain source-singleton or
control-explained, stop this source-diverse pressure loop and pivot to the
L0/L1/L2/L3 go/no-go matrix.
```

M1490 matches that stop condition:

```text
positives_source_singleton: true
controls_same_family: true
source_diverse_corpus_ready: false
```

Therefore the source-diverse pressure validation loop should stop here. The
next step should not be another replay retargeting pass. It should compare
controller families under a fair go/no-go matrix and let the project decide
whether the paper route is recurrent self-ID positive, negative, or conditional.

## Next Design Requirement

M1492 should design the self-ID go/no-go matrix:

```text
controller families:
  L0-current
  L1-one-step
  L2-finite-window at 0.25s, 0.5s, 1.0s, and 2.0s
  L2-current-tiled controls
  L3-online-GRU
  L3-reset/truncated controls

task families:
  T1 reactive emergency avoidance
  T2 delayed actuator/response feedback
  T3 diagnostic warmup followed by obstacle reveal
  T4 same-current same-recent-window different-older-history
  T5 terminal-boundary near-constraint avoidance

requirements:
  same actor input boundary
  same actuator-level output [steer, throttle, brake]
  same training budgets and seeds
  no private holdout tuning
  report parameter count, latency, success, collision, margin tail, and
  history-intervention action and margin gaps
```

M1492 should be a design milestone only. It should not train, replay, promote,
export a corpus, use private holdout, or change actor inputs.

## Guardrails

M1491 guardrail status:

```text
replay_started: false
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1492-paper-route-self-id-go-no-go-matrix-design
```
