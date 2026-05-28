# M1371 Paper-Route Post Public-Base Promotion Synthesis

## Summary

M1371 synthesizes the `paper_route_public_base_promotion_generalization` branch
from M1368 through M1370.

Synthesis decision:

```text
promote_to_next_branch
```

Closed branch:

```text
paper_route_public_base_promotion_generalization
```

Opened branch:

```text
paper_route_promoted_base_source_rich_comparison_readiness
```

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Previous public-gate base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

The promotion/generalization branch achieved its scoped objective: M1362 alpha
`0.1` is now the official public-gate base. The next work should not be local
alpha tuning or immediate PPO. It should establish the next evidence branch from
the promoted base.

## Evidence Summary

M1368 defined the no-training gate that separated:

```text
core promotion gates:
  actor contract
  exact source-history retention
  public proof replay
  source-diverse protected diagnostics
  fresh/OOD public generalization
  behavior and ablation retention

research-only diagnostics:
  old singleton keys
  row15/row16 cliff explanations

extended-regression evidence:
  source-rich extreme scenarios
  private holdout
  L0/L1/L2/L3 comparisons
  guarded PPO continuation
```

M1369 implemented and ran the generic gate. All tiers passed:

```text
exact_pass: true
proof_pass: true
source_diverse_pass: true
generalization_pass: true
behavior_pass: true
```

Key M1369 deltas against M1154:

```text
combined_loss_delta_vs_base: -0.5148637358
group_min_joint_margin_delta_vs_base: +0.5245143158
eval_fold_4_group_min_joint_margin_delta_vs_base: +0.4884667325
fresh public comparisons: 3 / 3 pass
moderate-OOD comparisons: 2 / 2 pass
behavior seeds: 4 / 4 pass
```

M1370 accepted the evidence and promoted M1362 alpha `0.1` as the public-gate
base, while preserving the claim boundary.

## Supported Claims

The branch supports these claims:

```text
1. M1362 alpha 0.1 is a valid public-gate base successor to M1154.
2. The promotion preserved human-view actor input contract and did not mutate
   forbidden parameters or log_std.
3. The promoted checkpoint improves exact materialized source-history metrics
   relative to M1154.
4. The promoted checkpoint retains all tested public proof replay surfaces and
   source-diverse protected diagnostics.
5. The promoted checkpoint does not regress M1154 on the public fresh/OOD
   comparisons used in M1369.
6. The promoted checkpoint retains public behavior/ablation ordering.
```

## Unsupported Or Still-Pending Claims

The branch does not support these claims:

```text
1. private-holdout generalization;
2. source-rich extreme public or holdout validation;
3. high-fidelity asymmetric wheel/contact-patch fault validation;
4. PPO continuation stability from the promoted base;
5. paper-level simulation evidence;
6. finite-window vs GRU superiority;
7. level3 anticipatory recurrent-belief or strong self-identification.
```

These are not negative results. They are missing evidence by design.

## Failure Taxonomy Summary

No M1368-M1370 milestone failed.

Resolved blockers:

```text
M1368:
  prevented direct PPO/private holdout/promotion without formal gate design.

M1369:
  converted the broad-public-replay candidate into a promotion-audit candidate.

M1370:
  converted promotion-audit candidacy into an official public-gate base.
```

Remaining risks:

```text
public-gate overfit risk: medium
```

Reason:

```text
The promoted checkpoint passed a broader public gate and fresh/OOD public
comparisons, but those are still public. The checkpoint has not been evaluated on
source-rich extreme public distributions under the promoted-base protocol, has
not touched private holdout, and has not been compared across L0/L1/L2/L3
controller families.
```

## Next Branch Decision

Open:

```text
paper_route_promoted_base_source_rich_comparison_readiness
```

First task:

```text
m1372-paper-route-promoted-base-source-rich-generalization-design
```

This branch should answer the next paper-route evidence question:

```text
Does the newly promoted public-gate base retain behavior on source-rich extreme
public scenarios, and how should that evidence be staged before L0/L1/L2/L3
comparisons or PPO continuation?
```

M1372 should design the source-rich public generalization gate first. It should
use the promoted M1362 base, preserve the current human-view/no-oracle actor
contract, keep private holdout unused, and keep high-fidelity true per-wheel
fault claims out of scope unless a higher-fidelity vehicle model is actually
introduced.

After the source-rich branch is designed or run, the project should refresh the
L0/L1/L2/L3 fair-comparison protocol so the promoted L3 recurrent checkpoint is
compared against current-only, one-step, and finite-window alternatives under a
fixed, fair budget.

## Guardrails

M1371 performs no training, PPO, replay, evaluation, actor update, checkpoint
mutation, private holdout, threshold relaxation, actor-input expansion,
source-rich run, high-fidelity claim, paper-level claim, finite-window-vs-GRU
claim, or level3 self-identification claim.

## Next

```text
m1372-paper-route-promoted-base-source-rich-generalization-design
```
