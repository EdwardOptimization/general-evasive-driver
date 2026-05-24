# M576 Moderate-OOD Route Eval Audit

## Purpose

M576 audits the scaled BC evidence after BC5660 passed public, fresh-route, and
moderate-OOD diagnostics.

This milestone is an audit only:

```text
no training
no PPO
no behavior cloning
no evaluation
no checkpoint promotion
```

## Evidence Summary

| Milestone | Surface | BC5660 Success | L2 Success | BC5660 Collision | L2 Collision | BC5660 Margin | L2 Margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M570 | Public natural surfaces | 0.866310 | 0.866310 | 0.133690 | 0.133690 | 1.782199 | 1.777833 |
| M572 | Fresh route seeds `19560..19815` | 0.625000 | 0.621094 | 0.375000 | 0.378906 | 1.064947 | 1.049135 |
| M575 | Moderate-OOD seeds `20560..20815` | 0.628906 | 0.628906 | 0.371094 | 0.371094 | 1.042773 | 1.036858 |

BC5660 is now L2-competitive across all three layers and slightly improves mean
margin in each one. This is the strongest evidence so far that L2-to-L3
distillation can produce a useful online-GRU L3 driver under the P0 actor
contract.

## What This Proves

The positive claim supported by M570/M572/M575 is:

```text
An L3 online-GRU student can distill the L2 finite-window teacher well enough to
match L2 on public natural surfaces, fresh same-distribution route seeds, and a
moderate-OOD route profile, without L2 stack leakage into the deployed actor.
```

This is meaningful because earlier from-scratch L3 PPO branches repeatedly
failed route-screen v2 or public diagnostics, while BC5660 closes that gap.

## What It Does Not Prove

The current evidence is not yet enough for promotion or a self-ID claim:

- Only one selected BC optimizer seed, `5660`, has been evaluated beyond
  route-screen selection.
- The other scaled BC seeds, `5661` and `5662`, have lower validation MSE in
  M568 but have not been tested on M570/M572/M575-style gates.
- M572 and M575 each use one 256-episode seed block. They are useful
  engineering diagnostics, not paper-grade repeated generalization.
- The result shows L3 can imitate L2 behavior, but does not yet prove recurrent
  history necessity for this branch.
- No reset-hidden, wrong-history, zero-response, or delayed-history ablation
  has been run on the scaled BC branch.
- No PPO continuation should start until family stability and recurrent
  dependence are clearer.

## Next Escalation

The next highest-leverage step is a BC seed-family generalization repeat:

```text
M577: design a BC seed-family route/OOD repeat.
M578: run a fresh same-distribution route repeat for BC5660/5661/5662.
M579: run a fresh moderate-OOD route repeat for BC5660/5661/5662 if M578 passes.
```

The repeat should evaluate:

```text
references:
  l0_s3540
  l2_s3540

candidates:
  l3_bc5660
  l3_bc5661
  l3_bc5662
```

Use fresh seed blocks that do not overlap prior route starts:

```text
M578 same-distribution repeat: 21560..21815
M579 moderate-OOD repeat:     22560..22815
```

Promotion remains blocked until the family repeat is understood. A good outcome
would be at least two of three BC seeds remaining L0-safe and L2-competitive on
both repeat distributions, with BC5660 not regressing.

## Decision

```text
moderate_ood_audit_admit_bc_family_repeat_design
```

M576 passes because it records the positive scaled-BC evidence, rejects
immediate promotion/PPO, and identifies BC seed-family route/OOD repeats as the
next escalation.

## Next

```text
M577: design the BC seed-family generalization repeat.
```
