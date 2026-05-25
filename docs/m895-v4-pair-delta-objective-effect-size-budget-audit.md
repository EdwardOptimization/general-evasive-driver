# M895 V4 Pair-Delta Objective Effect-Size Budget Audit

## Purpose

M895 audits existing M886/M891/M889/M893 artifacts to answer whether the
repeated proof-safe objective-only movement is large enough to justify scaling,
fresh-corpus work, PPO, or promotion.

M895 uses existing artifacts only:

```text
no training
no replay
no PPO
no promotion
```

## Exact Objective Budget

The accepted alpha `0.1` candidates improve exact train loss and do not regress
the registered exact holdouts:

```text
seed   candidate  train_delta       eval_delta        source_holdout_delta  new_signature_delta
10886  alpha_0.1  -0.0000838604     -0.0000409213    -0.0000751675        -0.0000345707
10887  alpha_0.1  -0.0000839978     -0.0000409646    -0.0000753013        -0.0000346502
```

The raw candidates have roughly `10x` larger exact-objective movement and also
show negative exact holdout deltas, but raw candidates were intentionally not
accepted directly by M885/M886/M891:

```text
seed   candidate  train_delta       eval_delta        source_holdout_delta  new_signature_delta  direct_admissible
10886  raw        -0.0008391377     -0.0004094026    -0.0007514722        -0.0003465017        false
10887  raw        -0.0008406197     -0.0004095923    -0.0007527191        -0.0003470580        false
```

Interpretation:

```text
The direction is repeatable and exact-objective-aligned. The accepted alpha is
very conservative; there may be unused scaling budget, but it has no replay
evidence yet.
```

## Action Movement Budget

Action drift on the exact objective tensors is tiny at the accepted alpha:

```text
seed   candidate  action_l2_mean_all  action_l2_max_all
10886  alpha_0.1  0.0001198419        0.0001266512
10887  alpha_0.1  0.0001200125        0.0001268814
```

Raw candidates are `10x` larger but still small in normalized action space:

```text
seed   candidate  action_l2_mean_all  action_l2_max_all
10886  raw        0.0011987321        0.0012667096
10887  raw        0.0012005469        0.0012692319
```

Interpretation:

```text
alpha_0.1 movement is proof-safe but probably below the threshold for broad
closed-loop behavior change. Raw movement is still modest but large enough to
justify a controlled proof-gated scaling check before changing data or PPO.
```

## Replay Effect Budget

M889 and M893 alpha `0.1` replay gates both passed all six surfaces. The normal
margin movement is consistently positive but small:

```text
surface    M889 normal_margin_delta  M893 normal_margin_delta
M183/M168  +0.0000326381             +0.0000327358
M183/M170  +0.0000343508             +0.0000344530
M193/M189  +0.0000875210             +0.0000877746
M212/M204  +0.0000910832             +0.0000913554
M223/M219  +0.0000910843             +0.0000913551
M267/M264  +0.0000910580             +0.0000913302
```

Success-drop regression:

```text
M889: 0 candidate success-drop regressions
M893: 0 candidate success-drop regressions
```

Interpretation:

```text
The accepted alpha preserves public proof surfaces. The margin deltas are real
but very small; they should be treated as retention-plus-numerical-slack, not
as meaningful driving improvement.
```

## Behavior Effect Budget

Behavior retention on seeds `9505` and `9506` is effectively tied with M568:

```text
run   success_delta  termination_delta  clearance_delta        return_delta
M889  0.0            0.0                +0.0004892324201435  -0.0039986065114590
M893  0.0            0.0                +0.0004909103515290  -0.0040092466785779
```

The zero-all diagnostic remains lower:

```text
M889 zero_all success_mean: 0.7250
M893 zero_all success_mean: 0.7250
```

Interpretation:

```text
Behavior retention passes, but there is no meaningful broad performance gain at
alpha_0.1. The response-dependence diagnostic is preserved.
```

## Effect-Size Classification

Classification:

```text
effect_size_marginal_at_accepted_alpha
```

Reason:

```text
The alpha_0.1 candidates are repeatable and proof-safe, but their action drift
is around 1.2e-4 and their behavior deltas are effectively retention ties.
This is too small to justify PPO, promotion, or fresh generalization claims.
```

However, the result should not be abandoned:

```text
The raw candidates have repeatable 10x larger exact-objective and action
movement, and their exact holdout deltas are still negative. The correct next
question is whether larger movement remains closed-loop proof-safe.
```

## Routing Decision

Decision:

```text
effect_size_marginal_route_to_controlled_scaling_design
```

Next:

```text
m896-v4-pair-delta-controlled-scaling-replay-design
```

M896 should design a controlled scaling gate for existing larger candidates,
starting with the raw candidates from both M886 and M891:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
```

Required order for later execution:

```text
1. exact objective recheck;
2. first replay gates M183/M170 and M267/M264;
3. all six replay/proof surfaces;
4. behavior seeds only if replay passes;
5. no PPO and no promotion.
```

If raw candidates pass, the next branch can consider a bounded scaling or
fresh-source check. If raw candidates fail, the branch should route to a scaling
boundary search or richer/fresher pair-delta corpus design rather than PPO.
