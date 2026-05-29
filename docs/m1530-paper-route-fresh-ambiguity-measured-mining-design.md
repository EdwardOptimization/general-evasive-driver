# M1530 Paper-Route Fresh Ambiguity Measured-Mining Design

## Summary

M1530 designs the measured public source-mining step admitted by M1529.

Decision:

```text
fresh_ambiguity_measured_mining_design_admit_bounded_implementation
```

The measured miner should test whether the M1528 source-diverse dry grid
contains real fixed-policy rollout rows where:

```text
scene/current state are similar;
older response evidence or hidden capability differs;
measured action choice, terminal margin, or recovery behavior differs.
```

This is design only. It does not run measured mining, materialize candidates,
export a corpus, train, run PPO, promote, use private holdout, alter actor
inputs, or claim self-identification.

## Inputs

Use public development inputs:

```text
source grid:
  M1528 fresh ambiguity source specs or default_source_specs(seed=1531)

checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

actor contract:
  P0 human-view no-wheel 72-dim frame with online GRU hidden state

seeds:
  public source-mining seed namespace only
```

Privileged simulator fields may be logged for filtering and diagnostics. They
must not enter actor observation or actor hidden state.

## Measured Pipeline

M1531 should implement a bounded fixed-policy measured miner:

```text
1. Load a bounded subset of M1528 source specs.
2. Convert each spec row into a public env hook/config attempt.
3. Run fixed-policy rollouts with the public checkpoint.
4. Snapshot reveal, reveal_plus_4, decision_minus_8, decision, and
   post_decision_plus_8 windows.
5. Compute measured scene/context and current-ego distances from observations.
6. Pair rows by matched scene/current state and hidden-capability difference.
7. Run bounded intervention continuations on matched pairs.
8. Write accepted and rejected measured pair artifacts.
9. Route to audit before any candidate materialization.
```

The first implementation may not support every M1528 source family. Unsupported
families must produce explicit source failure rows rather than silent drops.

## Trace Schema

Measured trace rows should include:

```text
trace_id
source_family
task_family
source_row_id
seed
hidden_capability_pair
geometry_key
simulator_scope
proxy_fault_family
closed_t5_subset
reveal_step
decision_step
step
phase
observation_0..observation_71 or compact observation checksums
action_steer
action_throttle
action_brake
hidden_norm
hidden_checksum
terminated
truncated
reward
```

Allowed diagnostic metadata:

```text
obstacle label
active obstacle body x/y
min clearance margin
collision
obstacle completed
mu / brake scale / drive scale / actuator tau scale
terminal reason
```

These metadata fields are for filtering and diagnosis only.

## Pairing Metrics

### Scene Context Distance

Compute from deployable context fields:

```text
road/free-space geometry;
obstacle presence and ego-frame position/size;
obstacle relative velocity only if the current actor profile includes it, with
an explicit context_proxy flag.
```

### Current Ego Distance

Compute from current-frame response and actuator fields:

```text
vx, vy, yaw_rate;
ax, ay;
steer angle/rate;
throttle/brake actuator state;
previous physical commands.
```

### Recent-Window Distance

Use the last 8/16/32 measured frames before the anchor:

```text
response stream;
actuator state;
previous commands;
action deltas.
```

### Older-Evidence Distance

Use pre-recent command-response history:

```text
braking response;
steering/yaw response;
actuator tracking error;
acceleration/yaw authority estimate;
warmup or pre-emergency response evidence.
```

Older evidence should differ while scene/current/recent distances remain small.

## Pair Acceptance Targets

Initial measured pairing thresholds:

```text
max_scene_context_distance: 0.10
max_current_ego_distance: 0.10
max_recent_window_distance: 0.12
min_older_evidence_distance: 0.12
min_hidden_capability_distance: 0.15
min_first_action_l2: 0.04
min_prefix_action_l2: 0.08
min_terminal_margin_gap: 0.02
near_boundary_margin_min: -0.05
near_boundary_margin_max: 0.20
```

These are public smoke thresholds. A later candidate-export gate can tighten
them after measured viability is known.

## Intervention Variants

Required continuation variants:

```text
normal
reset_hidden_once_at_anchor
reset_hidden_every_step_from_anchor
zero_current_response_from_anchor
zero_action_history_from_anchor
delayed_hidden_8_at_anchor
delayed_hidden_16_at_anchor
wrong_history_donor_hidden_at_anchor
donor_response_action_stream_from_anchor
```

The audit must distinguish:

```text
reset/zero-current sensitivity;
wrong-history sensitivity;
donor response/action sensitivity;
same-current measured pairing quality.
```

Reset or zero-current positives are useful controls, but they are not enough for
level3 self-identification.

## Bounded Smoke Scope

M1531 should be deliberately bounded:

```text
source_family_cap: 14
seed_count_per_family: 1 or 2
max_rollout_steps: 128
max_pair_candidates: 64
max_intervention_targets: 32
max_continuation_steps: 64
checkpoint: M1362 alpha 0.1
private_holdout_used: false
```

If runtime is too high, reduce seeds before reducing source-family diversity.

## Artifact Contract

M1531 should write:

```text
measured_source_spec_rows.csv
measured_trace_rows.csv
measured_snapshot_rows.csv
measured_pair_candidates.csv
measured_intervention_rows.csv
measured_rejected_pairs.csv
measured_source_family_summary.csv
measured_guardrail_summary.csv
summary.json
```

Each summary must include:

```text
attempted_source_families
reached_reveal_source_families
reached_decision_source_families
measured_pair_candidate_count
accepted_measured_pair_count
intervention_row_count
max_single_source_family_share
max_closed_t5_subset_share
proxy_fault_family_count
target_replay_failure_count
donor_replay_failure_count
guardrail_violation_count
```

Guardrail fields:

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Public Smoke Gates

Pass conditions for a measured smoke:

```text
all artifacts written;
attempted_source_families >= 8;
reached_decision_source_families >= 4;
proxy_fault_family_count >= 3;
max_closed_t5_subset_share <= 0.20;
guardrail_violation_count == 0;
candidate_materialized == false;
training/replay/PPO/promoted/private holdout all false;
all source failures have explicit failure_type.
```

Evidence-quality targets:

```text
measured_pair_candidate_count >= 8;
accepted_measured_pair_count >= 2;
at least one non-closed-T5 source family contributes an accepted measured pair;
wrong-history or donor response/action intervention is measured, even if null.
```

Failure to hit evidence-quality targets should route to audit, not direct
training.

## Failure Taxonomy

Use:

```text
scenario_sampling_failure:
  measured rollouts do not produce matched scene/current-state ambiguous pairs.

metric_artifact:
  measured distances are dominated by context proxies, labels, or reset/zeroing
  controls rather than history/capability ambiguity.

contract_violation:
  hidden parameters, labels, TTC, required clearance, or feasibility enter actor
  input.

training_instability:
  not expected in this branch; if seen, it indicates a forbidden training path.
```

## Next Milestone

Next:

```text
m1531-paper-route-fresh-ambiguity-measured-mining-implementation
```

M1531 should implement the bounded measured miner and run one public smoke. It
must still block candidate materialization, corpus export, training, PPO,
promotion, private holdout, actor-input changes, and self-identification claims.
