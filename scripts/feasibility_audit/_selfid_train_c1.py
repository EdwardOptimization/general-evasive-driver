"""STEP C1 (RMA two-phase) + B (no-ID floor), all from the pooled avoid sequences.
  TEACHER : FiLMZ conditioned on z=extrinsics(vehicle) (the privileged 'feel' the student must learn to infer).
            frame BC on [obs72 | z_extrinsics] -> oracle action. Should ~match the one-hot ceiling.
  PHI     : adaptation module phi((obs72,prev_action) window of length W) -> z_hat, regressed to z_extrinsics.
  B no-ID : SAME FiLMZ architecture but z == zeros for ALL vehicles (no vehicle info) -> the no-ID floor.
Deploy (validator) uses TEACHER policy + z_hat=phi(history) (NO label); B uses z=zeros."""
import sys, json, time
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); SEQ=RUN/'selfid_avoid_seqs'
VEH=["sedan","uazbus","bmw"]; W=M.AdaptationMLP().window  # 20

def load():
    eps=[]
    for v in VEH:
        d=np.load(SEQ/f'avoid_{v}.npz', allow_pickle=True)
        for obs,act,succ in zip(d["obs"],d["act"],d["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(succ): eps.append((obs,act,v))
    return eps

def frame_pool(eps, z_of):
    """Pool (X=[obs72|z], Y=oracle_action) frames. z_of(v)->z vector."""
    Xs=[]; Ys=[]
    for obs,act,v in eps:
        z=np.tile(z_of(v), (obs.shape[0],1)).astype(np.float32)
        Xs.append(np.concatenate([obs,z],1)); Ys.append(act)
    return torch.tensor(np.concatenate(Xs,0)), torch.tensor(np.concatenate(Ys,0))

def bc_filmz(X, Y, *, tag, epochs=600, lr=1e-3, bs=512):
    m=M.FiLMZActorCritic(); opt=torch.optim.Adam(m.parameters(), lr=lr); N=X.shape[0]; t0=time.time()
    m.train()
    for ep in range(epochs):
        idx=torch.randint(0,N,(bs,))
        loss=((m.actor_forward(X[idx])-Y[idx])**2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        if ep%150==0 or ep==epochs-1: print(f"  [{tag}] ep {ep:4d} bc_mse={loss.item():.4e} ({time.time()-t0:.0f}s)", flush=True)
    m.eval(); return m

def phi_windows(eps, z_of, *, stride=3):
    """Build (flattened [obs|prev_act] window length W ending at t) -> z target, subsampled by stride."""
    Xs=[]; Zs=[]
    for obs,act,v in eps:
        T=obs.shape[0]; prev=np.zeros_like(act); prev[1:]=act[:-1]
        step=np.concatenate([obs,prev],1)  # (T, 75)
        z=z_of(v)
        for t in range(1,T,stride):
            lo=max(0,t-W+1); chunk=step[lo:t+1]
            if chunk.shape[0]<W: chunk=np.concatenate([np.zeros((W-chunk.shape[0],75),np.float32),chunk],0)
            Xs.append(chunk.reshape(-1)); Zs.append(z)
    return torch.tensor(np.stack(Xs)), torch.tensor(np.stack(Zs))

def main():
    torch.manual_seed(0)
    eps=load(); print(f"loaded {len(eps)} sequences", flush=True)
    # TEACHER (z = real extrinsics)
    Xt,Yt=frame_pool(eps, M.vehicle_extrinsics)
    teacher=bc_filmz(Xt,Yt, tag="C1-teacher", epochs=800)
    torch.save({"state_dict":teacher.state_dict()}, RUN/'selfid_c1_teacher_policy.pt')
    # B no-ID (z = zeros)
    zero_of=lambda v: np.zeros(M.Z_DIM, np.float32)
    Xb,Yb=frame_pool(eps, zero_of)
    bmod=bc_filmz(Xb,Yb, tag="B-noID", epochs=800)
    torch.save({"state_dict":bmod.state_dict()}, RUN/'selfid_b_noid_policy.pt')
    # PHI (history -> z_hat regression)
    Xp,Zp=phi_windows(eps, M.vehicle_extrinsics)
    phi=M.AdaptationMLP(); opt=torch.optim.Adam(phi.parameters(), lr=1e-3); N=Xp.shape[0]; t0=time.time()
    print(f"  phi training set: {N} windows (W={W})", flush=True); phi.train()
    for ep in range(1500):
        idx=torch.randint(0,N,(1024,))
        loss=((phi(Xp[idx])-Zp[idx])**2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        if ep%300==0 or ep==1499: print(f"  [phi] ep {ep:4d} z_mse={loss.item():.4e} ({time.time()-t0:.0f}s)", flush=True)
    phi.eval()
    torch.save({"state_dict":phi.state_dict(),"window":W}, RUN/'selfid_c1_phi.pt')
    # report phi's per-vehicle z_hat separation (does it actually identify the vehicle?)
    with torch.no_grad():
        for v in VEH:
            ev=[e for e in eps if e[2]==v][:20]
            Xv,_=phi_windows(ev, M.vehicle_extrinsics, stride=5)
            zh=phi(Xv).mean(0).numpy(); print(f"  z_hat[{v}] mean={np.round(zh,3)}  (true z={np.round(M.vehicle_extrinsics(v),3)})", flush=True)
    print("saved selfid_c1_teacher_policy.pt, selfid_b_noid_policy.pt, selfid_c1_phi.pt", flush=True)
if __name__=="__main__": main()
