"""Rung 2 — full-linkage constrained-DAE (NOT BUILT; gated on the T3a falsification, design §6).

INTERFACE (when greenlit): expose the same flat-module surface pwr3/tier_a do
(make_*_param_batch / init_state / physics_step / IDX / STATE_DIM) so rungs/__init__.ModuleModel wraps
it unchanged. The engine is the §2.4 fixed-iteration projected constraint solver over per-axle dense
blocks, reusing pwr3's TMeasy/sigma/gear leaf ops verbatim.

T3a STATUS (2026-06): the cheap falsification (inject geometric load transfer into tier_a) did NOT
close the drift regression (0.0756 -> 0.0748, 2%) — leaning NO-GO, but that first-cut injection was
numerically unstable in the avoid regime (vx_rmse 8.2), so the verdict is being re-run cleanly through
this interface before T3 is committed. Do NOT build the 6-12wk solver until T3a is a clean GO.
"""
raise NotImplementedError("rung2_dae: not built — gated on the T3a falsification (design §6 T3a).")
