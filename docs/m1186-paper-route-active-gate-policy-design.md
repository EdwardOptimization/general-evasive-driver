# M1186 Paper-Route Active Gate Policy Design

## Summary

M1186 turns the M1185 gate utility matrix into an active gate policy for the
paper route. The policy is written in:

```text
docs/active-gate-policy.md
```

This milestone is process-only. It does not run candidate replay, train, run
PPO, use private holdout, promote, delete gates, or change actor inputs.

## Decision

```text
active_gate_policy_design_admit_l0_l1_l2_l3_controller_comparison_design
```

## Policy

The policy separates gate usage into:

```text
Stack A: daily engineering and controller-comparison admission.
Stack B: active public proof gate for public-base and mechanism-route work.
Stack C: extended historical regression for promotion, synthesis, paper freeze,
         and difficult failure localization.
Legacy: diagnostic-only unless reinstated by manifest.
Deprecated: not allowed as training or promotion objective without a new
            reinstatement manifest.
```

## Practical Effect

The immediate effect is not gate deletion. The effect is scheduling discipline:

- docs, process, and controller-comparison design milestones use Stack A
  process gates;
- new driver checkpoints and engineering behavior claims require Stack A
  behavior/fresh/OOD evidence;
- public-base hardening, guarded PPO admission, source-rich proof conversion,
  or mechanism claims require Stack B;
- promotion audits, branch synthesis, and paper table freeze require Stack C as
  extended regression;
- legacy singleton diagnostics remain available but should not be single-row
  global blockers;
- deprecated sign-wrong or metric-artifact objectives cannot guide future
  training without reinstatement.

## Why This Is Needed

M1185 showed that Stack A is core but insufficient for proof. M1069 and M1112
passed broad behavior gates while proof surfaces washed out. It also showed
that Stack C contains real failure detectors but is too lineage-specific to
veto every future engineering baseline or finite-window comparison. Stack B is
therefore the default active public proof route.

## Follow-Up

M1186 pre-registers the next paper-route design milestone:

```text
experiments/manifests/m1187-paper-route-l0-l1-l2-l3-controller-comparison-design.json
```

M1187 should define fair controller families, observation windows, model
budgets, training/evaluation splits, and gate usage for:

```text
L0-current
L1-one-step feedback
L2-finite-window command-response history
L3-GRU recurrent belief
```

M1187 should remain design-only. No controller training should begin until the
comparison contract is fixed.

## Guardrail Audit

M1186 did not:

- run candidate replay;
- delete or demote gates;
- train actor weights;
- run PPO;
- promote a checkpoint;
- use private holdout;
- change actor inputs;
- claim driver-performance progress;
- claim recurrent-belief or self-identification evidence.
