"""Rung 2 — full-linkage constrained-DAE (NOT BUILT; gated on the T3a falsification, design §6).

INTERFACE (when greenlit): expose the same flat-module surface pwr3/tier_a do
(make_*_param_batch / init_state / physics_step / IDX / STATE_DIM) so rungs/__init__.ModuleModel wraps
it unchanged. The engine is the §2.4 fixed-iteration projected constraint solver over per-axle dense
blocks, reusing pwr3's TMeasy/sigma/gear leaf ops verbatim.

T3a VERDICT (2026-06): NO-GO. Four independent fidelity/DOF additions (tier_a kinematic suspension,
pwr5 driveline inertia, pwr6 front slip, tier_a_geom geometric transfer) ALL certified null/negative at
the gate (design doc 'T3a VERDICT'). The 'higher order closes the residuals' premise is refuted to the
extent cheaply testable; the full-linkage DAE is NOT built. The multi-fidelity spectrum is delivered by
rung-0 (fast) + the T2 longitudinal-fidelity rung, not a full multibody. Re-open only if a clean two-pass
geometric injection overturns the four converging nulls.
"""
raise NotImplementedError("rung2_dae: not built — gated on the T3a falsification (design §6 T3a).")
