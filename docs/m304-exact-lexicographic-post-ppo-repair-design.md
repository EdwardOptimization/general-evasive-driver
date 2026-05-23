# M304 Exact Lexicographic Post-PPO Repair Design

M304 designs the repair path after M302 showed that a sampled
training-time rejected-history preference auxiliary loss is not enough to
preserve exact full-corpus proof objectives. No PPO was run, no actor update
was run, and actor inputs are unchanged.

## Starting Point

Current public-gate base:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Rejected PPO proposal:

```text
runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
```

Exact proof corpora:

```text
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

M302 regressed both exact objectives versus M299:

| Objective | M299 base | M302 raw | Delta |
| --- | ---: | ---: | ---: |
| Exact M297 rejected-history preference | 1.189609528 | 1.190309286 | +0.000699759 |
| Exact M270 source-balanced outcome | 0.677945912 | 0.678388774 | +0.000442863 |

The M297 regression covered `17 / 17` rows, and every nonzero interpolation
from M299 toward M302 raw also regressed both exact objectives. Therefore the
next PPO continuation cannot be accepted by scalar train-time aux metrics.

## Design Decision

Treat PPO as a proposal generator only. Any post-PPO candidate must pass an
exact full-corpus lexicographic repair or projection before closed-loop replay
gates are allowed.

The selected path is:

```text
M302 raw PPO proposal
  -> exact full-corpus repair/projection
  -> exact M297 no-regression gate
  -> exact M270 no-regression gate
  -> first replay gates
  -> full public gate stack
```

This separates exploration from feasibility restoration. PPO may create a
direction worth testing, but exact proof objectives and replay gates decide
whether any repaired checkpoint is admissible.

## Exact Objectives

M305 should implement deterministic full-batch objective components. The
training-time sampled losses remain useful for wiring diagnostics but are not
promotion evidence.

### Exact M297 Preference Loss

Use every row in the M297 rejected-history preference corpus:

```text
L297 = weighted_mean(
  softplus(logp_wrong_hidden(preferred_action)
           - logp_correct_hidden(preferred_action)
           + preferred_margin)
  + wrong_coef * softplus(logp_wrong_hidden(preferred_action)
                          - logp_wrong_hidden(rejected_action)
                          + wrong_margin),
  weight
)
```

This objective preserves the counterfactual relation:

```text
correct history should keep the correct-history action likely;
wrong history should not also make that correct-history action likely;
wrong history should keep its rejected-history action more likely.
```

### Exact M270 Outcome Loss

Use every row in the M270 source-balanced multi-surface corpus:

```text
L270 = weighted_mean(
  softplus(logp_rejected_hidden(preferred_action)
           - logp_preferred_hidden(preferred_action)
           + logprob_margin),
  weight
)
```

M270 remains necessary because M297 is current-family focused. M270 carries the
older M183/M193/M212/M223 surfaces and the protected-key source into the repair
objective.

## Repair Objective

The optimizer may use a weighted penalty, but acceptance is lexicographic. The
candidate generator should support:

```text
hinge297 = relu(L297(theta) - L297(base) - tol297)
hinge270 = relu(L270(theta) - L270(base) - tol270)

J(theta) =
  lambda297 * hinge297^2
+ lambda270 * hinge270^2
+ lambda_anchor * action_anchor_to_base(theta)
+ lambda_param * param_l2_to_base(theta)
+ lambda_raw * param_l2_to_raw(theta)
```

Interpretation:

- `lambda297` and `lambda270` must dominate; they restore exact feasibility.
- `action_anchor_to_base` protects replay-sensitive action surfaces.
- `param_l2_to_base` prevents broad actor drift.
- `param_l2_to_raw` is optional and only expresses a preference for keeping
  useful PPO movement after exact feasibility is restored.

The repair tool must report all terms separately. A lower weighted `J` is not a
promotion criterion unless the exact lexicographic gates also pass.

## Trust Region And Anchors

M305 should use the M299 public-gate base as the anchor checkpoint.

Required support:

```text
base checkpoint action anchor on M270 snippets
parameter L2 distance to M299 base for trainable actor scope
optional parameter L2 distance to M302 raw proposal
```

Recommended optional support:

```text
trajectory action anchors from prior row16/current-family repair surfaces
```

These optional anchors should stay disabled in the first implementation probe
unless exact repair passes but replay gates fail. They are repair tools, not
new actor inputs.

## Candidate Starts

M305 should support three start modes, but M306 should evaluate them in this
order:

| Start | Meaning | Expected use |
| --- | --- | --- |
| `line_search_boundary` | interpolate M299 -> M302 raw and pick the least-bad exact boundary start | confirms whether any PPO movement survives exact gates |
| `repair_from_raw` | initialize from rejected M302 raw and project back to exact feasibility | tests whether the PPO proposal has recoverable value |
| `repair_from_base` | initialize from M299 and take an exact objective-only repair step | control condition when the raw PPO direction is useless |

If repair only returns to M299 with negligible action movement and no objective
improvement, classify the result as a non-promotable projection diagnostic.

## Acceptance Order

M306 may run closed-loop gates only after exact gates pass.

1. Actor contract unchanged: P0 human-view no-wheel 72-dim frame plus online
   GRU hidden state.
2. Exact M297 must be no worse than M299 within tolerance:

   ```text
   L297(candidate) <= L297(M299) + 1e-7
   ```

3. Exact M270 must be no worse than M299 within tolerance:

   ```text
   L270(candidate) <= L270(M299) + 1e-7
   ```

4. M183/M170 first replay gate must retain normal success and wrong-history
   success drops.
5. M267/M264 first replay gate must retain `17 / 17` wrong-history success
   drops.
6. Full public replay stack must pass.
7. Protected-key diagnostic must pass.
8. Behavior seeds `9505` and `9506` must not regress.

Promotion is blocked if any earlier tier fails. Private holdout is not used in
M304-M306.

## Failure Classification

Use these failure labels:

| Failure | When to use |
| --- | --- |
| `objective_overfit` | exact objectives improve but replay gates fail |
| `proof_washout` | replay success-drop proof is lost |
| `metric_artifact` | sampled or weighted repair metric improves but exact gates fail |
| `seed_fragility` | one repair seed passes and a fresh repeat fails |
| `promotion_gate_failure` | exact and replay gates pass but full public promotion fails |

## M305 Implementation Contract

M305 should implement an exact post-PPO repair/projection tool and focused
tests. It should not run PPO and should not promote a checkpoint.

Minimum output artifacts:

```text
summary.json
train_metrics.csv
candidate_summary.csv
exact_m297_policy_summary.csv
exact_m270_policy_summary.csv
```

The tool must make the full-batch exact M297 and M270 values first-class
outputs for every candidate. M306 will use those outputs to decide whether to
run replay gates.

## Decision

Admit:

```text
m305-exact-post-ppo-repair-projection-implementation
```

Decision:

```text
admit_exact_repair_projection_implementation
```
