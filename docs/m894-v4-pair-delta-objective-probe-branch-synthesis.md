# M894 V4 Pair-Delta Objective-Probe Branch Synthesis

## Purpose

M894 synthesizes the `v4_pair_delta_objective_probe` branch before any further
repeat, generalization gate, PPO, or promotion work.

Covered milestones:

```text
M885-M893
```

M894 is synthesis-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Evidence Summary

M885 designed a tiny no-PPO objective-only probe:

```text
base checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
objective corpus: M880 enriched pair-delta rows
train scope: narrow actor-coupling parameters only
steps: 32 Adam steps
acceptance: exact-objective interpolation with no holdout regression
forbidden: PPO, promotion, actor-input changes, residual-head mutation
```

M886 implemented the first probe with seed `10886`:

```text
tensor_rows_reconstructed: 247 / 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
raw_train_weighted_loss_delta: -0.0008391377425962521
exact_admissible_alpha_count: 7
best_exact_admissible_alpha: 0.1
best_exact_admissible_train_delta: -0.00008386037042074079
```

M887/M888 audited that result and designed the replay/proof gate stack.

M889 ran the proof gate for M886 alpha `0.1` and passed:

```text
exact_recheck_rows: 247 / 247
replay_gates_passed: 6 / 6
candidate_success_drop_regressions: 0
behavior_seed_success: 0.8125
behavior_seed_termination: 0.1875
aggregate_clearance_delta_vs_M568: +0.0004892324201435372
```

M890 correctly limited the claim to a single-seed proof-gate positive and
routed to a fresh objective-only seed before any stronger claim.

M891 repeated the objective-only probe with seed `10887`:

```text
tensor_rows_reconstructed: 247 / 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
raw_train_weighted_loss_delta: -0.0008406196871111327
exact_admissible_alpha_count: 7
best_exact_admissible_alpha: 0.1
best_exact_admissible_train_delta: -0.00008399784564971924
```

M892 audited M891 as a clean objective-level repeat and admitted replay/proof
gate execution.

M893 ran the proof gate for M891 alpha `0.1` and passed:

```text
exact_recheck_rows: 247 / 247
replay_gates_passed: 6 / 6
candidate_success_drop_regressions: 0
behavior_seed_success: 0.8125
behavior_seed_termination: 0.1875
aggregate_clearance_delta_vs_M568: +0.0004909103515290392
```

The two proof-gate runs are closely matched:

```text
seed      exact_best_alpha  replay_pass  behavior_success  clearance_delta_vs_M568
10886     0.1               6 / 6        0.8125            +0.0004892324201435372
10887     0.1               6 / 6        0.8125            +0.0004909103515290392
```

## Supported Claims

The branch supports these claims:

```text
The enriched pair-delta objective-only update is repeatable across two
optimizer/minibatch seeds at the exact-objective level.

The exact-admissible alpha selection is stable across the two tested seeds:
both choose alpha 0.1 and both find 7 nonzero exact-admissible alphas.

The alpha 0.1 candidates preserve M568-relative six-surface replay/proof gates
for both tested seeds.

The alpha 0.1 candidates retain the registered behavior seeds 9505/9506 versus
M568: success and termination do not regress.

The actor input contract and M761 residual head remain unchanged.
```

This is real progress over a single public proof row. The branch now has a
repeatable no-PPO objective step that does not immediately wash out the public
proof stack.

## Falsified Claims

The branch falsifies or weakens these claims:

```text
The first exact-objective pass is enough to justify replay/proof claims.

One optimizer seed is enough to establish objective-only update stability.

Replay retention can be inferred from exact-objective metrics alone.

The objective-only candidates already demonstrate meaningful driver
improvement.

The objective-only branch is ready for PPO or public-base promotion.
```

The two accepted candidates are proof-safe but extremely small. Their behavior
retention metrics are effectively tied with M568; this is retention evidence,
not a broad driving-performance gain.

## Failure Taxonomy Summary

`seed_fragility`:

```text
Reduced for the exact objective and public replay/proof stack. Two seeds
matched on admissible alpha count, best alpha, replay pass, and behavior
retention.
```

`proof_washout`:

```text
Not observed at alpha 0.1. All six replay surfaces passed for both candidates
with zero candidate success-drop regression.
```

`behavior_regression`:

```text
Not observed on the registered behavior seeds. Success and termination are
unchanged versus M568 for both M889 and M893.
```

`objective_overfit`:

```text
Still a serious risk. The objective corpus, replay surfaces, and behavior seeds
are public workflow artifacts. The branch has not shown fresh-source or private
holdout generalization.
```

`metric_artifact`:

```text
Reduced by exact recheck and replay execution, but still present if the tiny
objective deltas are overinterpreted as meaningful driving improvement.
```

`contract_violation`:

```text
Not observed. The P0 human-view no-wheel actor contract is unchanged.
```

`lineage_invalid`:

```text
Not observed. M885-M893 consistently root the branch in M568 diagnostic BC,
M880 enriched rows, and M761 residual-head fixed evaluation.
```

## Public Gate Overfit Risk

Public gate overfit risk remains high:

```text
The branch optimized and evaluated against public objective/replay surfaces.
The behavior seeds are retention diagnostics, not private generalization.
The accepted movement is small enough that broad behavior may remain unchanged.
The branch is rooted at M568 diagnostic BC, not the current public-gate base.
```

Controls required before any stronger claim:

```text
Quantify effect size before adding more gates.
Do not run PPO yet.
Do not promote either alpha 0.1 checkpoint.
Do not treat public replay retention as generalization.
Do not tune against private holdouts.
Require a fresh-source or effect-size branch before public-base integration.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close current branch:

```text
v4_pair_delta_objective_probe
```

Open new branch:

```text
v4_pair_delta_objective_effect_size
```

Next milestone:

```text
m895-v4-pair-delta-objective-effect-size-budget-audit
```

Rationale:

```text
M885-M893 answered the first question: the no-PPO enriched pair-delta
objective-only step can be repeated and can preserve public proof gates.

The next blocker is not another same-style replay repeat. The next blocker is
whether the objective direction has enough effect-size budget to justify
scaling, fresh-source generalization, or later PPO integration.
```

M895 should aggregate the M886/M891 interpolation and action-drift artifacts
plus M889/M893 replay/behavior deltas. It should decide whether to:

```text
continue with controlled objective scaling,
pivot to richer/fresher corpus design,
or stop the branch because movement is too small to matter.
```

M895 must not train, run replay, run PPO, or promote.
