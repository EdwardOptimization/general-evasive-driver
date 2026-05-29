# M1583 Paper-Route History Pairability Source-Miner Result Audit

## Summary

M1583 audits M1582 before any history intervention design.

Decision:

```text
history_pairability_audit_admit_source_diverse_intervention_design_with_high_speed_caveat
```

M1582 cleanly answers the branch prerequisite:

```text
matched-current hidden-divergent public pairs exist in the current P0 source set.
```

This removes the M1579 pairability shortfall for the broad source-generation
route. It does not prove history necessity, self-identification, high-speed
history sensitivity, or deployable performance.

## M1582 Evidence

Public smoke gates passed:

```text
source_spec_count: 480
anchor_candidate_count: 640
replay_ok_anchor_count: 509
pair_screen_candidate_count: 20000
tier_a_pair_count: 20000
tier_b_pair_count: 20000
pairable_source_edge_count: 24
pairable_target_source_family_count: 8
pairable_window_count: 6
high_speed_or_late_pair_count: 108
max_single_pairable_source_edge_share: 0.0742
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

The capped pair set is source-diverse:

```text
source edges: 24
endpoint source families: 8
endpoint windows: 6
max source-edge share: 0.0742
```

This is much stronger than M1579, where high-speed/late-only pressure produced
zero accepted matched-current hidden-divergent pairs.

## Capped-Top-Pair Caveat

M1582 writes the top `20000` ranked pair rows. All written rows are tier A:

```text
classification_counts:
  tier_a_strict: 20000
```

This means the capped set is good enough for the next design, but it should not
be interpreted as the full pairability distribution. The next design should use
source-edge and window caps instead of simply taking the first rows by score.

## Source-Subset Caveat

The source generator covered `11` families at source-spec and anchor-candidate
time:

```text
actuator_delay_step
brake_fade_or_loss_proxy
capability_step_down
capability_step_up
curved_boundary_obstacle
drive_loss_proxy
grip_loss_proxy
late_reveal_boundary
t5_boundary_axis_retarget
t5_high_speed_close_obstacle
t5_near_boundary_warmup
```

The capped pair set covers `8` endpoint families. Missing from the capped top
pair endpoints:

```text
t5_high_speed_close_obstacle
brake_fade_or_loss_proxy
grip_loss_proxy
```

The `high_speed_or_late_pair_count` of `108` is entirely late-reveal endpoint
coverage:

```text
late_reveal_boundary endpoint pairs: 108
t5_high_speed_close_obstacle endpoint pairs: 0
```

This is not a failure of M1582 because the pre-registered broad public gates
passed. It is a caveat for M1584: do not claim high-speed pairability or
high-speed history sensitivity from this result. Track high-speed as an explicit
diagnostic/null subset.

## Supported Claims

M1583 supports:

```text
M1582 is a valid pairability prerequisite pass;
the broad P0 source set can produce source-diverse matched-current hidden-divergent pairs;
the next branch step may design a bounded source-diverse wrong-history intervention over the pairable set;
the high-speed endpoint subset remains unresolved and must not be bundled into a success claim.
```

## Unsupported Claims

M1583 does not support:

```text
history necessity;
source-diverse self-identification;
high-speed history sensitivity;
brake-fade or grip-loss endpoint pairability in the capped top set;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level result;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
none
```

M1582 is not a failed source miner. The audit simply scopes the result: broad
pairability passed, high-speed remains a diagnostic gap.

## Route Decision

Admit a design-only milestone:

```text
m1584-paper-route-source-diverse-pairability-history-intervention-design
```

The design should:

```text
select a source-edge/window capped intervention subset from M1582 pair rows;
run no simulator in the design milestone;
keep wrong-history, donor-hidden, donor-response/action, reset, zero-current, zero-action, and delayed-history controls separate;
pre-register high-speed as an unresolved diagnostic subset, not a pass gate;
block candidate materialization, training corpus export, PPO, promotion, private holdout, actor-input changes, and level3 self-ID claims.
```

Do not route directly to implementation, materialization, training, or PPO.

## Guardrails

```text
history_interventions_executed: false in M1583
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1584-paper-route-source-diverse-pairability-history-intervention-design
```
