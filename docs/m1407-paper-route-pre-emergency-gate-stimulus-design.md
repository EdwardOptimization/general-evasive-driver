# M1407 Paper-Route Pre-Emergency Gate Stimulus Design

## Summary

M1407 designs the next task route after M1406 blocked training from the M1405
reset-only outcome result.

Decision:

```text
pre_emergency_gate_stimulus_design_admit_staged_obstacle_api_implementation
```

M1407 is design only. It does not implement the task API, run a source smoke,
run outcome interventions, train, run PPO, promote, use private holdout, export
a corpus, or change actor inputs.

## Design Goal

M1405 showed that passive figure-eight curvature can create preferred
near-boundary emergency candidates, but it does not make wrong/delayed warmup
history outcome-critical:

```text
preferred_near_boundary_candidate_rows: 26
warmup_history_positive_rows: 0
wrong_warmup_history_same_reveal outcome-critical rows: 0
delayed_warmup_history outcome-critical rows: 0
```

The next task must create stronger pre-emergency command-response evidence
without handing the actor an oracle answer.

## Actor Contract

Actor input stays P0 human-view:

```text
ego response
actuator state
previous physical commands
road/free-space geometry
obstacle geometry in existing slots
online GRU hidden state
```

Still forbidden:

```text
mu / mass / tire / brake / actuator hidden parameters
oracle feasibility labels
controller mode
speed_ref / beta_target actor inputs
path error / heading error / reference trajectory inputs
TTC / required clearance / stopping distance
scripted controller commands
new actor observation dimensions
```

## Selected MVP

Use a staged primary obstacle/gate API.

Rationale:

```text
multi-slot obstacles are already represented in the 72-dim contract, but the
current actor has mostly seen slot0 active and slots1-3 zero.

The most conservative first implementation is therefore to keep using slot0:
  warmup phase: slot0 shows a mild visible gate obstacle
  transition: warmup gate is passed or times out
  emergency phase: slot0 switches to the emergency obstacle
```

This keeps the actor input dimension and slot semantics stable. The actor sees
ordinary obstacle geometry; no mode label is provided.

## Warmup Gate Geometry

Initial M1408 API should support:

```text
warmup_gate.enabled: bool
warmup_gate.distance_range: [12.0, 30.0]
warmup_gate.lateral_offset_range: [-1.2, 1.2]
warmup_gate.half_width_range: [0.35, 0.85]
warmup_gate.reveal_step: 0
warmup_gate.clear_step_or_pass: true
warmup_gate.max_active_steps: 48 to 72
warmup_gate.collision_penalty_scale: diagnostic only for now
```

The gate should be low-risk but not invisible:

```text
not centered directly on the ego path every time;
wide enough to require steering/brake modulation;
not so wide that it terminates most episodes before emergency reveal;
visible through existing obstacle geometry;
not represented by a rule or controller command.
```

The emergency obstacle remains the real evaluation target:

```text
distance_range: near-boundary pressure from M1404/M1405
half_width_range: M1404 range or tightened after smoke
perception_reveal_distance: 6.0 initially
```

## Source Reconstruction

M1409 source smoke should target matched/bucketed current reveal rows after the
warmup gate has already produced response evidence.

Required source fields:

```text
warmup_gate_active_steps
warmup_gate_passed
warmup_gate_min_clearance
warmup_action_l2
warmup_response_l2
warmup_history_l2
current_hidden_l2
matched_current_pass
bucketed_current_pass
preferred_reveal_bucket
wrong_reveal_bucket
```

Structural thresholds:

```text
source_rows >= 512
matched_or_bucketed_reveal_rows >= 160
unique_source_seeds >= 24
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
finite metrics
warmup_action_l2_p95 >= 0.05
warmup_response_l2_p95 >= 0.05
```

The last two are diagnostic, not promotion claims. They prevent another passive
stimulus that materializes rows but fails to produce meaningful warmup evidence.

## Outcome Criteria

If source smoke passes, the outcome probe must keep M1405-style reporting:

```text
normal_margin_band_summary.csv
variant_summary.csv
accepted_outcome_rows.csv
accepted_warmup_history_rows.csv
strict_bucketed_summary.csv
reveal_step_summary.csv
```

Positive evidence still requires:

```text
warmup_history_positive_rows > 0
wrong_warmup or delayed_warmup rows are present
accepted rows are not seed-singleton
accepted rows appear in broad or preferred near-boundary bands
reset/zero-current controls do not dominate
```

Do not count source materialization or action-only deltas as
self-identification.

## Implementation Route

M1408 should implement only the task API and tests.

Minimal implementation:

```text
1. Add a frozen WarmupGateConfig dataclass.
2. Add it to DriftEnvConfig with default disabled.
3. On reset, sample a warmup gate and emergency obstacle.
4. While warmup gate is active, slot0 shows warmup geometry.
5. After pass or max_active_steps, slot0 shows the emergency obstacle under the
   existing perception reveal rules.
6. Keep collision/min-clearance accounting separated:
   warmup gate diagnostics should not masquerade as emergency success.
```

M1408 should add tests for:

```text
default config keeps old observation behavior;
warmup gate is visible before emergency reveal;
slot0 switches from warmup gate to emergency obstacle;
actor observation shape remains 72;
info includes warmup gate diagnostics;
no privileged actor fields are added.
```

No source smoke should run until those tests pass.

## Stop Conditions

Stop and audit before training if:

```text
staged obstacle API requires actor mode labels;
slot0 switching creates ambiguous or non-finite observations;
warmup gate causes most episodes to terminate before emergency reveal;
source smoke produces no matched/bucketed rows;
outcome probe again yields action-only or reset-only evidence;
accepted warmup-history rows remain seed-singleton.
```

## Guardrails

```text
implementation_started: false
source_smoke_started: false
outcome_probe_started: false
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
