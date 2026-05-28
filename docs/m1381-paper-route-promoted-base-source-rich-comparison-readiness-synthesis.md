# M1381 Paper-Route Promoted-Base Source-Rich Comparison Readiness Synthesis

## Summary

M1381 synthesizes the `paper_route_promoted_base_source_rich_comparison_readiness`
branch from M1372 through M1380.

Synthesis decision:

```text
promote_to_next_branch
```

Closed branch:

```text
paper_route_promoted_base_source_rich_comparison_readiness
```

Opened branch:

```text
paper_route_history_profile_comparison_protocol
```

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

The branch achieved its scoped objective: it verified that the promoted public
base can run through the source-rich capability-step harness and produced a
clear public diagnostic split. Cross-fault wrong-history positives remain sparse,
while temporal-history interventions are positive by row and fault-pair coverage
but still seed-thin.

The next work should not be another blind local source-rich expansion, direct
corpus export, PPO, private holdout, or promotion. It should freeze a fair
L0/L1/L2/L3 history-profile comparison protocol so the project can decide
whether the recurrent/history architecture is actually the evidence-bearing
axis for the paper route.

## Evidence Summary

M1372 designed a no-training promoted-base source-rich public smoke with fixed
claim boundaries:

```text
current-model single-track and axle-level capability faults: allowed
true single-wheel/per-wheel high-fidelity faults: future-only
private holdout: not used
PPO/training/promotion: not allowed
```

M1373 ran the smoke:

```text
scenario_count: 832
matched_pair_count: 768
accepted_rows: 2
reset_only_rows: 174
result_class: cross_fault_wrong_sparse
```

M1375 scaled the public source-rich wave:

```text
scenario_count: 3328
matched_pair_count: 4096
accepted_rows: 3
reset_only_rows: 1281
result_class: cross_fault_wrong_sparse
```

The larger wave mainly increased reset-only rows. It did not create a
source-diverse cross-fault wrong-history corpus.

M1377 then tested temporal sequence interventions over M1375 reset-only rows:

```text
selected_source_rows: 384
accepted_temporal_sequence_rows: 180
unique_temporal_accepted_fault_pairs: 8
unique_temporal_accepted_seeds: 9
accepted_cross_fault_sequence_rows: 0
```

M1379 expanded the sequence probe:

```text
selected_source_rows: 768
accepted_temporal_sequence_rows: 224
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 10
accepted_cross_fault_sequence_rows: 0
```

M1380 audited M1379:

```text
row threshold: passed (224 >= 200)
fault-pair threshold: passed (9 >= 8)
seed threshold: failed (10 < 12)
cross-fault sequence accepted rows: 0
```

The branch therefore supports temporal-history dependence as a public diagnostic
axis, but not cross-fault hidden-condition self-identification or a source-rich
training corpus.

## Supported Claims

This branch supports these claims:

```text
1. The M1362 alpha 0.1 public-gate base is compatible with the source-rich
   capability-step harness.
2. The source-rich harness produces clean public artifacts without training,
   PPO, checkpoint mutation, promotion, private holdout, or actor-input changes.
3. Current cross-fault wrong-history positives are sparse under M1373/M1375.
4. Reset-hidden sensitivity is broad under M1375 source-rich rows.
5. Temporal-history interventions are repeatably positive by row count and
   fault-pair coverage under M1377/M1379.
6. Temporal-history evidence remains seed-thin against the pre-registered
   accepted-seed threshold.
7. Source-rich temporal diagnostics are useful as public comparison axes, not
   as standalone level3 self-identification proof.
```

## Falsified Or Unsupported Claims

This branch falsifies or leaves unsupported these claims:

```text
1. Simple seed scaling is enough to produce a source-diverse cross-fault
   wrong-history corpus.
2. Current cross-fault hidden swaps prove source-rich self-identification.
3. Temporal positives alone satisfy the accepted-seed diversity requirement.
4. The current source-rich rows are ready for corpus export and objective
   training without a separate source-diversity design.
5. The project has true high-fidelity per-wheel, split-mu, puncture, half-shaft,
   or contact-patch fault evidence.
6. The project has private-holdout or paper-level source-rich validation from
   this branch.
7. The branch proves level3 anticipatory recurrent-belief self-identification.
```

## Failure Taxonomy Summary

No milestone in M1372-M1380 failed structurally.

The branch produced negative scientific evidence that should be classified as:

```text
scenario_sampling_failure:
  cross-fault wrong-history accepted rows remain sparse after source expansion.

seed_fragility:
  temporal positives remain below accepted-seed threshold after expansion.

metric_artifact risk:
  using accepted temporal row count alone would overstate source diversity.
```

These are not infrastructure failures. They are constraints on what the next
paper-route claim is allowed to say.

## Public Gate Overfit Risk

Risk:

```text
medium_high
```

Reason:

```text
M1373-M1379 are public diagnostics, and the temporal positives come from a
seed-thin source set. Optimizing directly on those rows would likely turn the
branch into public-row gate fitting before the paper comparison story is clear.
```

The branch should therefore not proceed directly to PPO, corpus export, or
private holdout. Private holdout would also be premature because the public
comparison protocol is not yet frozen.

## Next Branch Decision

Open:

```text
paper_route_history_profile_comparison_protocol
```

First task:

```text
m1382-paper-route-history-profile-comparison-protocol-design
```

The next branch should design the fair comparison protocol before running new
comparisons. It should define fixed budgets, fixed scenario sets, fixed claim
levels, and a fixed interpretation order for:

```text
L0: current-frame/reactive policy or ablation
L1: one-step command-response policy or ablation
L2: finite-window or temporal-history policy
L3: online recurrent GRU policy, using the promoted M1362 public base
```

The protocol should include the source-rich temporal diagnostic as one public
evidence axis, but it must also include broader public proof/generalization and
behavior-retention gates. No profile should get private tuning, threshold
relaxation, hidden parameters, oracle labels, path/reference inputs, TTC, or
required-clearance shortcuts.

## Guardrails

M1381 performs no training, PPO, replay, evaluation, actor update, checkpoint
mutation, private holdout, threshold relaxation, actor-input expansion, source
corpus export, high-fidelity claim, paper-level claim, finite-window-vs-GRU
result claim, or level3 self-identification claim.

## Next

```text
m1382-paper-route-history-profile-comparison-protocol-design
```
