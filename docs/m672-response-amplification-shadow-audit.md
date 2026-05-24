# M672 Response-Amplification Shadow Audit

## Purpose

M672 audits M671 before any actor-coupling design. The goal is to prevent a
frozen shadow-head diagnostic from being overstated as closed-loop driver proof.

This milestone is audit-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## M671 Evidence

M671 was implementation-clean:

```text
shadow_passed:             true
selected_candidate_rows:   648
shadow_corpus_rows:        648
source_count:              216
physical_pair_count:       100
train_rows:                528
source_holdout_rows:       120
source_weight_balanced:    true
actor_parameters_changed:  false
actor_checkpoint_written:  false
ppo_used:                  false
promoted:                  false
```

The shadow corpus is source-balanced and covers both `fresh` and `ood`
surfaces, with targets:

```text
aes_feasible
drift_required
unavoidable
```

## View-Level Result

The key result is view-specific:

```text
fused:                  failed
next_hidden:            failed normal-retention mean, but gap was strong
fused_plus_next_hidden: passed in 2/3 seeds
```

Source-heldout fused-plus-next-hidden metrics:

| seed | pass | normal mean | normal p95 | gap mean | gap p10 | gap ratio | wrong target improvement |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6700 | true | 0.002327 | 0.004224 | 0.012136 | 0.008244 | 4.223965 | 0.910229 |
| 6701 | false | 0.002555 | 0.004801 | 0.012398 | 0.008459 | 4.315166 | 0.897438 |
| 6702 | true | 0.002360 | 0.003834 | 0.012534 | 0.008509 | 4.362418 | 0.902770 |

The failing fused-plus-next-hidden seed is narrow: its normal mean is
`0.002555`, just above the `0.0025` threshold, while all other gap and
wrong-target criteria pass.

## Classification

M671 should be classified as:

```text
shadow_positive_representation_action_boundary_evidence
```

More specifically:

```text
next_hidden_signal_positive
fused_boundary_weak
fused_plus_next_hidden_sufficient_for_shadow_gap
normal_retention_near_threshold
closed_loop_proof_absent
```

This is materially stronger than M658/M652:

```text
M658: no feature view passed absolute wrong-history gap thresholds.
M671: fused-plus-next-hidden passes source-heldout shadow thresholds in 2/3 seeds.
```

It is also narrower than a driver result:

```text
the actor was not mutated;
no closed-loop replay was evaluated from a changed actor;
no outcome margin or success claim is made.
```

## Admitted Next Step

M671 is strong enough to admit an actor-coupling design milestone, but not
strong enough to admit actor training, PPO, or promotion directly.

M673 should be design-only and should specify:

```text
parent checkpoint: BC5660
parent corpus: M671 shadow corpus
allowed feature signal: no new actor observation inputs
normal branch: first-class retention constraint
wrong-history branch: bounded sequence-separation target
trust region: strict actor/action drift limits
evaluation order: exact objective first, closed-loop replay second
promotion: forbidden
```

## Guardrails For Actor Coupling

An implementation after M673 may be considered only if it obeys:

```text
1. no PPO in the first actor-coupling probe;
2. no private holdout use;
3. no actor input contract change;
4. exact M671-style normal-retention and gap metrics must be non-regressing;
5. public replay/protected/behavior gates must be required before any
   checkpoint can be called usable;
6. any checkpoint from the probe is a candidate only, not a promoted driver.
```

The first actor-coupling implementation should be tiny and interpolation-gated.
If normal retention fails, classify as `behavior_regression` or
`objective_overfit`, not as evidence against the whole self-ID direction.

## Rejected Interpretations

Reject:

- `closed_loop_self_id_proven`: no changed actor was replayed.
- `ppo_admissible`: PPO remains blocked.
- `promotion_admissible`: no driver checkpoint may be promoted from shadow
  evidence.
- `fused_features_are_enough`: fused view failed.
- `next_hidden_alone_is_enough`: next-hidden gap is strong, but normal
  retention missed the pre-registered mean threshold in all seeds.

## Decision

```text
response_amplification_shadow_audit_admit_actor_coupling_design
```

## Next

```text
m673-response-amplification-actor-coupling-design
```
