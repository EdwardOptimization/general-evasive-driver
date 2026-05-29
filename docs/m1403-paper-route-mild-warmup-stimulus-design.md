# M1403 Paper-Route Mild Warmup Stimulus Design

## Summary

M1403 designs a non-oracle mild warmup stimulus route after M1402 classified
late reveal alone as action-only and insufficient for outcome pressure.

Decision:

```text
mild_warmup_stimulus_design_admit_config_source_smoke
```

M1403 is design only. It does not train, run PPO, run a new source sweep,
promote, use private holdout, export a corpus, or change actor inputs.

## Design Constraint

The warmup stimulus must be something a deployable perception/control stack
could see or feel:

```text
allowed:
  road/free-space geometry in ego frame
  mild curvature before emergency reveal
  mild lane/corridor pressure through track geometry
  hidden dynamics/faults as simulator-side sampling labels only
  ego response and previous commands through existing P0 observation

forbidden:
  actor mode labels
  reference trajectory or path-error inputs
  oracle feasibility labels
  direct hidden params
  scripted control commands
  any new actor observation channel
```

The policy still directly outputs steer/throttle/brake.

## Why Mild Stimulus

M1401 shows that current interventions can strongly change action sequences:

```text
action_critical_rows: 1464
reset_hidden sequence_action_l2_mean: 0.9791
warmup_removed sequence_action_l2_mean: 0.6298
```

But the task does not convert those action differences into clearance or success
differences:

```text
accepted_outcome_rows: 0
preferred_near_boundary_candidate_rows: 0
```

The next task should therefore create useful command-response evidence before
the obstacle reveal and place the later emergency closer to the outcome
boundary.

## Source Design

Use a new config family with:

```text
track_kind: figure_eight
track_radius: 70.0 to 80.0
track_width: 6.5 to 7.0
speed_range: 13.5 to 18.0
obstacle distance_range: 4.0 to 20.0
obstacle half_width_range: 0.90 to 1.65
perception_reveal_distance: 6.0
obstacle_relative_velocity_mode: zero
history_length: 1 actor frame, online GRU unchanged
```

Rationale:

```text
figure_eight creates natural curvature variation during warmup;
narrower track and wider obstacle increase outcome pressure;
distance range stays close but not so late that source reconstruction collapses;
relative velocity remains zero to avoid reintroducing ego-motion proxies.
```

Fault families should initially reuse M991:

```text
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
delay_noise_fault
mass_cg_shift
combined_fault
```

No actor input changes are admitted.

## Source Smoke

M1404 should create:

```text
configs/ppo_m1404_mild_warmup_figure_eight.json
configs/m1404_mild_warmup_stimulus_source_wave.json
```

Then run:

```text
python -m autodrift.warmup_latched_config_smoke
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
  --config configs/m1404_mild_warmup_stimulus_source_wave.json
  --seed-start 140400
  --seed-count 48
  --reveal-steps 48,56,64,72,80
  --history-length 56
  --min-warmup-evidence-steps 16
  --max-source-rows 6144
  --device cpu
  --run-dir runs/m1404_mild_warmup_stimulus_source_smoke
```

M1404 should be source smoke only. No outcome interventions yet.

## Structural Thresholds

Source smoke pass:

```text
source_rows >= 512
matched_or_bucketed_reveal_rows >= 160
unique_source_seeds >= 24
unique_capability_pairs >= 8
unique_reveal_buckets >= 8
finite metrics
```

Additional diagnostics:

```text
matched/bucketed unique_source_seeds
matched/bucketed reveal-step distribution
warmup_history_l2 p95
current_hidden_l2 p95
strict matched-current share
bucketed-current share
rejection reasons by reveal step
```

The design should not require all reveal steps to pass. It should identify which
reveal steps are viable before outcome probing.

## Later Outcome Criteria

If M1404 source smoke passes, a later outcome probe should report:

```text
normal_margin bands
accepted rows split by strict/bucketed matching
accepted rows split by reveal step
accepted rows split by track/fault/capability pair
wrong_warmup and same_recent_wrong_warmup rows separately from
warmup_removed/shortened rows
```

Near-boundary target:

```text
broad: 0.00 <= normal_margin <= 0.50
preferred: 0.02 <= normal_margin <= 0.25
```

Positive evidence requires source-diverse outcome rows, not merely action
differences.

## Stop Conditions

Stop and audit before another branch if:

```text
figure_eight source smoke collapses source diversity;
matched/bucketed rows are mostly absent;
near-boundary candidates remain zero after outcome probing;
accepted rows remain action-only;
accepted history rows are seed-singleton;
the required stimulus needs actor oracle labels or scripted controls.
```

## Guardrails

```text
training_started: false
evaluation_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```
