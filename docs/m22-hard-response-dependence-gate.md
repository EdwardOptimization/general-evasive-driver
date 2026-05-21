# M22 Hard Response-Dependence Gate

Last updated: 2026-05-21

## Motivation

M21 improves aggregate obstacle avoidance but still does not prove that the
policy depends on deployable response channels. The response-critical actor can
solve many near-threshold cases using context plus a default recurrent state:
zeroing response channels does not reliably reduce success.

The next gate should make that shortcut fail. Instead of only changing the
actor, M22 should mine or construct paired scenarios where the visible geometry
is identical but the correct steering and drive/brake correction differs
because of hidden tire, actuator, brake, or road response.

## Requirement

M22 must preserve the clean project rule:

- no privileged actor inputs;
- no `mu`, vehicle parameters, `speed_ref`, `beta_target`, explicit `beta`, or
  scenario label in actor observations;
- no checkpoint shape compatibility path;
- response dependence is measured by ablation, not assumed from architecture.

## Proposed Work

1. Mine a hard paired corpus from existing scenario seeds and hidden
   randomization ranges.
2. Keep only pairs where `m21_503` or `m21_602` normal inference succeeds in at
   least one hidden condition and a response-masked or reset variant changes the
   outcome.
3. Add a training or fine-tuning config that oversamples this hard corpus while
   preserving the current clean 15-value actor frame.
4. Evaluate normal, reset, zero-current-response, and zero-all-response
   policies on actuator-response, friction, and same-corpus gates.

## Pass Criteria

The next checkpoint must improve or preserve M21 aggregate performance while
making response ablation visibly worse:

- same-corpus obstacle success at least `0.500`;
- actuator-response perturbed success at least `0.450`;
- M13 friction perturbed success at least `0.450`;
- response-masked success at least `0.050` below normal on a hard paired gate;
- hidden-reset success at least `0.050` below normal on a hard paired gate.

If the mined corpus is too sparse, the blocker should be documented as a gate
construction problem before adding more model complexity.
