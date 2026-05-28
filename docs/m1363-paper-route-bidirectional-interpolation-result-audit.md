# M1363 Paper-Route Bidirectional Interpolation Result Audit

## Summary

M1363 audits the M1362 interpolation preflight result.

Decision:

```text
bidirectional_interpolation_audit_route_to_broader_public_replay_design
```

The M1362 selected checkpoint is useful enough to leave the two-surface preflight
stage, but it is not a promoted driver and should not go directly to PPO or
private holdout.

## Supported Evidence

Selected checkpoint:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Selected alpha:

```text
0.1
```

Exact metrics at alpha `0.1`:

```text
combined_loss_delta_vs_base: -0.5148637349
group_min_joint_margin_delta_vs_base: +0.5245143565
eval_fold_4_group_min_joint_margin_delta_vs_base: +0.4884667957
```

Replay preflight:

```text
M267/M264: pass
M183/M170: pass
```

This is materially stronger than M1352's alpha `0.005` diagnostic while keeping
the two public replay preflight surfaces intact.

## Limits

M1362 has not run:

```text
M183/M168 replay
M193/M189 replay
M212/M204 replay
M223/M219 replay
protected key diagnostics
behavior seeds 9505 and 9506
private holdout
fresh scenario distribution
PPO continuation
```

So the supported claim is narrow:

```text
M1362 alpha 0.1 is a two-surface replay-preflight candidate with meaningful
exact source-history lift.
```

It is not a public-gate base, not a driver-performance result, and not strong
self-identification evidence.

## Route Decision

The next task should be a broader public replay design, not another local alpha
tweak.

M1364 should define an escalation gate for the M1362 selected checkpoint:

```text
1. exact source-history metrics remain non-regressing versus M1154
2. six public replay surfaces pass versus M1154
3. only after six replay surfaces pass, run protected-key diagnostics
4. only after protected diagnostics pass or are classified, run behavior seeds
5. no private holdout or promotion until this public stack is complete
```

This keeps the project from overfitting to the two preflight surfaces while also
not throwing away a direction that now has clear exact and replay-preflight
support.

## Guardrails

M1363 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1364-paper-route-bidirectional-broader-public-replay-design
```
