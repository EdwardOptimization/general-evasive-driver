# M1128 V4 Public Base Row15 Projection Branch Synthesis

## Purpose

M1128 synthesizes the `failed_wrong_history_retention_repair` branch after
M1127 passed the expanded full public gate for alpha `0.15`.

This milestone is process-only. It does not train actor weights, run PPO, run
replay, run objective optimization, mine rows, promote a checkpoint, use private
holdout, or change actor inputs.

## Evidence Summary

M1118 ran the M1116-designed retention-aware actor-coupling probe from the
current public-gate base. All three seeds passed pre-replay exact, anchor, and
parameter-scope gates. The best seed was `111800`:

```text
checkpoint: runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
exact M1107 improvement: 0.003012359
target-base-only trajectory-anchor MSE: 0.000001498
```

M1120 rejected this candidate at first replay. The failure was narrow:

```text
passed surfaces: 2/6
failed surfaces: 4/6
failed row: 15
physical pair: 9530:21:9550:21
normal_lost_events: 0
wrong_history_safe_events: 4
```

M1121 audited the failure and found that row15 was not missing from the M1115
target-base trajectory anchor:

```text
row15 target-base anchor rows: 170
surfaces covered: 5
step range: 0..33
```

Therefore the branch falsified the idea that low rejected-trajectory MSE alone
is enough to preserve the remaining near-boundary wrong-history proof. The
unresolved failure was terminal wrong-history margin crossing.

M1122 designed a no-training unsafe-margin projection. M1123 ran it and selected
alpha `0.15`:

```text
checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

exact M1107 delta vs base: -0.000417471
target-base trajectory MSE: 0.0000000336
combined trajectory MSE: 0.0000050340
row15 unsafe-margin gate: pass
six-surface first replay: pass
```

M1125 then ran M1061 family-intersection replay:

```text
short61049: 25/25 success drops retained
short61050: 27/27 success drops retained
short61051: 27/27 success drops retained
overall_pass: true
actor_inputs_changed: false
```

M1127 ran the pre-registered exact recheck and expanded full public gate:

```text
M1107 exact:
  proof_current loss: 0.679117322
  alpha_0_15 loss:   0.678699851
  delta:             -0.000417471

expanded full public gate:
  exact_pass: true
  proof_pass: true
  family_intersection_pass: true
  source_diverse_pass: true
  generalization_pass: true
  behavior_pass: true
  actor_inputs_changed: false
  ppo_used: false
  promoted: false
  private_holdout_used: false
```

## Supported Claims

This branch supports these claims:

```text
1. The M1115 target-base rejected-history trajectory anchor covered row15, but
   generic action-MSE retention did not guarantee wrong-history terminal
   margin retention.
2. The row15 failure can be repaired by a direct unsafe-margin projection
   without training, PPO, or actor-input changes.
3. Alpha_0_15 preserves exact M1107 improvement while restoring row15
   wrong-history failure on the old public/source-diverse first-replay stack.
4. Alpha_0_15 passes M1061 family-intersection replay.
5. Alpha_0_15 passes the expanded public gate stack: exact/contract, old public
   replay, family-intersection, source-diverse, fresh/OOD, and behavior.
6. Alpha_0_15 is ready for a separate public-gate promotion audit scoped to
   proof-base hardening.
```

## Falsified Or Unsupported Claims

This branch falsifies or does not support these claims:

```text
1. The full M1118 seed111800 actor update is acceptable after pre-replay gates.
2. Low rejected-trajectory action MSE is enough to preserve near-boundary
   wrong-history terminal-margin proof.
3. The branch proves PPO readiness or medium/long PPO stability.
4. The branch proves scenario-distribution performance improvement.
5. The branch proves private-holdout or paper-level generalization.
6. The branch proves level3 anticipatory self-identification.
7. The branch justifies changing actor inputs, using hidden parameters, or
   weakening the human-view/no-privileged contract.
```

The supported self-identification claim remains level2: public proof surfaces
show history-encoded reactive sensitivity to wrong matched histories. The
branch does not prove anticipatory self-identification.

## Failure Taxonomy Summary

The branch's main negative result was:

```text
proof_washout:
  M1120 showed that the M1118 exact-improving actor update made row15
  wrong-history branches safe on four replay surfaces.

objective_overfit:
  M1118 optimized exact objective plus trajectory anchors, but the pre-replay
  gates were still insufficient for terminal wrong-history margin retention.
```

The branch did not show:

```text
behavior_regression:
  M1127 behavior gates passed.

contract_violation:
  M1127 actor inputs and allowed parameter-surface contract passed.

training_instability:
  The accepted M1123 projection is no-training interpolation.

private_holdout_contamination:
  No private holdout was used.
```

M1123 converted the failure into a direct terminal-margin projection and M1127
verified it under the expanded public gate.

## Public-Gate Overfit Risk

The branch uses public proof surfaces heavily. That is acceptable for
public-base proof hardening but cannot be reported as unbiased private
generalization.

Overfit controls in this branch:

```text
M1120 first replay before escalation
M1121 failure audit before repair
direct row15 unsafe-margin thresholds pre-registered in M1122
M1123 selected a nonzero alpha only after exact and unsafe-margin gates
M1125 family-intersection replay before full gate
M1127 expanded full public gate across proof, generalization, and behavior
no PPO, no private holdout, no actor-input change
```

Remaining risks:

```text
1. Alpha_0_15 is a public proof-hardening candidate, not a performance-trained
   driver improvement.
2. It was tuned against public proof surfaces, so future promotion must be
   scoped as public-gate base hardening only.
3. After any promotion, the next research branch should refresh proof surfaces
   or run a promotion-scope audit before new PPO.
4. Private holdout should remain unused until a paper-level promotion protocol
   is explicitly designed.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Closed branch:

```text
failed_wrong_history_retention_repair
```

Opened branch:

```text
row15_projection_promotion_audit
```

The next milestone should audit whether alpha `0.15` should become the current
public-gate base. The audit must keep the claim scoped to public proof-base
hardening, not PPO performance, private-holdout generalization, or paper-level
evidence.

## Decision

```text
row15_projection_branch_synthesis_route_to_promotion_audit
```

Next milestone:

```text
m1129-v4-public-base-row15-projection-promotion-audit
```
