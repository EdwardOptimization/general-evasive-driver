# M826 V4 Extreme Hidden-Dynamics Data Route Audit

## Purpose

M826 audits M825 before any further route expansion or training.

The audit question is:

```text
Was M825 sparse because of a contract/runtime failure, because the route lacks
the decisive wrong-history intervention, or because the current policy is not
strongly response-history sensitive under this route?
```

M826 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m825_v4_extreme_hidden_dynamics_data_route/summary.json
runs/m825_v4_extreme_hidden_dynamics_data_route/diversity_summary.json
runs/m825_v4_extreme_hidden_dynamics_data_route/history_intervention_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/accepted_self_id_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/accepted_mitigation_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/gate_summary.csv
docs/m825-v4-extreme-hidden-dynamics-data-route-implementation.md
```

M825 result class:

```text
v4_extreme_hidden_dynamics_data_route_sparse
```

## Artifact Consistency

M825 produced the expected route artifacts:

```text
fault_specs: 18
source_groups: 64
source_snapshots: 64
candidate_plan_rows: 512
normal_replay_rows: 512
history_intervention_rows: 3072
matched_pair_rows: 256
replay_errors: 0
```

The supported intervention rows are complete:

```text
reset_hidden_each_step: 512
reset_hidden_then_normal: 512
zero_command_obs: 512
command_shift_obs: 512
response_delay_obs: 512
wrong_cross_fault_history: 512 unsupported diagnostic rows
```

This is not a reconstruction or runtime failure.

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Checksums match before and after:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

The actor input contract was not changed. Hidden fault labels are used only for
source mining and logging, not actor inputs.

## Sparse Evidence Audit

M825 required:

```text
min_self_id_rows: 120
```

M825 found:

```text
accepted_self_id_raw_rows: 47
accepted_self_id_rows: 18
accepted_mitigation_raw_rows: 40
accepted_mitigation_rows: 12
history_sensitive_candidate_rows: 47
```

Accepted self-ID diversity:

```text
rows: 18
unique_seed_count: 2
unique_source_group_count: 3
unique_source_index_count: 3
unique_fault_family_pair_count: 3
unique_fault_family_count: 3
unique_fidelity_class_count: 2
unique_onset_bucket_count: 2
unique_warmup_mode_count: 1
max_seed_dominance: 0.6666666666666666
max_source_group_dominance: 0.3333333333333333
max_fault_family_pair_dominance: 0.3333333333333333
max_warmup_mode_dominance: 1.0
```

The accepted self-ID rows are concentrated in:

```text
fault families: brake_authority_drop, combined_fault, steering_fault
onset buckets: pre_emergency, mid_maneuver
warm-up mode: natural_policy only
```

The full normal replay population is much broader:

```text
normal rows: 512
unique seeds: 12
unique source groups: 64
unique fault-family pairs: 9
unique warm-up modes: 4
unique onset buckets: 4
```

So the source generator is broad enough to create coverage, but the accepted
history-sensitive subset collapses strongly after the intervention gate.

## Intervention Audit

Maximum normal-minus-intervention margin gaps:

```text
zero_command_obs:         0.028255885109984114
reset_hidden_each_step:   0.012439503461971757
command_shift_obs:        0.005916646036354667
reset_hidden_then_normal: 0.003019702661738677
response_delay_obs:       0.00006529045199066275
```

Mean margin gaps:

```text
zero_command_obs:         0.004356127360268502
reset_hidden_each_step:   0.0019966236227270456
command_shift_obs:        0.000564596918329822
reset_hidden_then_normal: 0.00023029618744243056
response_delay_obs:      -0.00008629321548608892
```

Maximum action-prefix gaps:

```text
zero_command_obs:       0.05710723623633385
reset_hidden_each_step: 0.030276766046881676
command_shift_obs:      0.013632885180413723
response_delay_obs:     0.0040514362044632435
```

Audit interpretation:

- `zero_command_obs` is the dominant signal.
- `reset_hidden_each_step` has some signal.
- delayed response is weak and slightly negative on mean margin gap.
- command-shift is below the pre-registered action threshold at maximum.

This means M825 cannot be read as strong response-history self-ID evidence.
The current positives are closer to command-history sensitivity plus some
hidden-state reset sensitivity.

## Matched Pair Audit

M825 found diagnostic matched action-divergent proxy pairs:

```text
matched_pair_rows: 256
unique_fault_family_pair_count: 16
unique_fidelity_pair_count: 3
unique_left_fault_family_count: 7
unique_right_fault_family_count: 5
unique_left_warmup_mode_count: 3
unique_right_warmup_mode_count: 3
unique_onset_pair_count: 6
```

This is the most useful positive artifact from M825. It suggests there are
same-apparent-geometry / different-hidden-dynamics cases with different first
actions.

But these rows are still diagnostic pairs only:

```text
wrong_cross_fault_history: unsupported
```

They do not yet prove that injecting the wrong history causes margin/action
degradation.

## Failure Taxonomy

### scenario_sampling_failure

The accepted self-ID rows are sparse and source-concentrated even though the
normal replay pool is broad. The accepted subset fails the pre-registered
source-diversity gates.

### metric_artifact

Zero-command sensitivity is useful, but it is not enough to claim full
closed-loop response-history self-identification. Treating it as a pass would
overstate the evidence.

### not contract_violation

Actor and residual-head checksums are unchanged, no training occurred, and the
proxy-fault boundary is documented.

## Supported Claims

M825 supports:

- the extreme hidden-dynamics no-training route is implemented and runnable;
- the route can evaluate reset-hidden, zero-command, shifted-command, and
  delayed-response interventions at scale;
- M568+M761 behavior has some command-history and reset-hidden sensitivity;
- matched action-divergent proxy pairs exist and are worth turning into a real
  wrong-history intervention corpus;
- current-model and proxy-fault classes are logged distinctly.

## Unsupported Claims

M825 does not support:

- source-diverse self-ID evidence;
- response-delay sensitivity as a strong signal;
- wrong-cross-fault history sensitivity;
- PPO admission;
- checkpoint promotion;
- physical single-wheel or split-mu fault fidelity claims.

## Decision

Decision:

```text
admit_wrong_cross_fault_history_intervention_design
```

Rationale:

```text
Do not expand sampling first and do not run PPO. The missing decisive control
is wrong-cross-fault history injection. M825 already found 256 matched
action-divergent proxy pairs; the next step is to design how to replay current
geometry with hidden/history from a matched different-fault source and measure
whether margin or action degrades.
```

Next:

```text
m827-v4-wrong-cross-fault-history-intervention-design
```

PPO, checkpoint promotion, learned gating, and threshold relaxation remain
blocked.
