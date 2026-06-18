"""BEST self-ID avoid driver: RMA with a LEARNED z-encoder (fixes the fragile single-head) + DAgger (fixes the
BC closed-loop cap -> A-comparable). NO vehicle label at deploy. All faithful on Chrono.
  teacher: ExtrinsicsEncoder(2->16) + FiLMZ(z_dim=16), jointly BC on (obs, extrinsics(v) -> oracle action).
  phi    : (obs,prev_action) history window -> z_hat(16), regressed to encoder(extrinsics).detach().
  DAgger : deploy phi-z_hat policy on Chrono, relabel student-visited states with the oracle, augment frames AND
           phi sequences (student trajectories), retrain teacher + phi. K rounds.
Validate phi-z_hat (deploy, NO label) AND true-z (encoder(extrinsics)) each round."""
import sys, json, time, threading, argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, torch
sys.path.insert(0,'src'); sys.path.insert(0,'scripts/feasibility_audit')
import distill_both_final_integrated as INT
import distill_both_3vehicle as d3v
import phase4_f2_train as f2
import selfid_models as M
RUN=Path('runs/feasibility_audit/phase4_f2'); SEQ=RUN/'selfid_avoid_seqs'; VEH=["sedan","uazbus","bmw"]
W=M.AdaptationMLP().window; ZD=M.RICH_Z

def load_base():
    """oracle avoid demo sequences per vehicle (successful only)."""
    out={v:[] for v in VEH}
    for v in VEH:
        d=np.load(SEQ/f'avoid_{v}.npz', allow_pickle=True)
        for obs,act,succ in zip(d["obs"],d["act"],d["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(succ): out[v].append((obs,act))
    return out

def frames_from(seqs):
    OBS=[];EX=[];ACT=[]
    for v in VEH:
        ex=M.vehicle_extrinsics(v)
        for obs,act in seqs[v]:
            OBS.append(obs); ACT.append(act); EX.append(np.tile(ex,(obs.shape[0],1)))
    return (torch.tensor(np.concatenate(OBS,0)), torch.tensor(np.concatenate(EX,0).astype(np.float32)),
            torch.tensor(np.concatenate(ACT,0)))

def windows_from(seqs, stride=3):
    XS=[];EX=[]
    for v in VEH:
        ex=M.vehicle_extrinsics(v)
        for obs,act in seqs[v]:
            T=obs.shape[0]; prev=np.zeros_like(act); prev[1:]=act[:-1]; step=np.concatenate([obs,prev],1)
            for t in range(1,T,stride):
                lo=max(0,t-W+1); ch=step[lo:t+1]
                if ch.shape[0]<W: ch=np.concatenate([np.zeros((W-ch.shape[0],75),np.float32),ch],0)
                XS.append(ch.reshape(-1)); EX.append(ex)
    return torch.tensor(np.stack(XS)), torch.tensor(np.stack(EX).astype(np.float32))

def train_teacher(seqs, *, epochs, enc=None, film=None, lr=1e-3):
    OBS,EX,ACT=frames_from(seqs); N=OBS.shape[0]
    enc=enc or M.ExtrinsicsEncoder(z_dim=ZD); film=film or M.FiLMZActorCritic(z_dim=ZD)
    opt=torch.optim.Adam(list(enc.parameters())+list(film.parameters()), lr=lr); enc.train(); film.train()
    for ep in range(epochs):
        idx=torch.randint(0,N,(512,)); z=enc(EX[idx]); X=torch.cat([OBS[idx],z],1)
        loss=((film.actor_forward(X)-ACT[idx])**2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    enc.eval(); film.eval(); return enc, film, float(loss.item())

def train_phi(seqs, enc, *, epochs, phi=None, lr=1e-3):
    X,EX=windows_from(seqs); N=X.shape[0]; phi=phi or M.AdaptationMLP(z_dim=ZD)
    with torch.no_grad(): Z=enc(EX)
    opt=torch.optim.Adam(phi.parameters(), lr=lr); phi.train()
    for ep in range(epochs):
        idx=torch.randint(0,N,(1024,))
        loss=((phi(X[idx])-Z[idx])**2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    phi.eval(); return phi, float(loss.item())

class PhiDeploy:
    """deploy phi-z_hat (NO label); optionally RECORD (obs, oracle_action) + the student (obs,prev_act) sequence."""
    def __init__(self, film, phi, oracle=None):
        self.film=film; self.phi=phi; self.oracle=oracle
        self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
        self.obs_log=[]; self.lab=[]; self.seq=[]
    def __call__(self, s, obs):
        obs=np.asarray(obs,np.float32); step_in=np.concatenate([obs,self.prev])
        self.hist.append(step_in); self.seq.append(step_in.copy())
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win) if pad>0 else np.concatenate(win)
        with torch.no_grad(): zhat=self.phi(torch.tensor(flat.astype(np.float32)).unsqueeze(0)).numpy()[0]
        if self.oracle is not None and f2._obstacle_visible(obs, {}):
            self.obs_log.append(obs.copy()); self.lab.append(np.clip(self.oracle(s,obs),-1,1).astype(np.float32))
        a=self.film.act(np.concatenate([obs,zhat.astype(np.float32)])); self.prev=a; return a

def true_z_policy(film, enc, vehicle):
    with torch.no_grad(): z=enc(torch.tensor(M.vehicle_extrinsics(vehicle)).unsqueeze(0)).numpy()[0]
    return lambda s,obs,_z=z.astype(np.float32): film.act(np.concatenate([np.asarray(obs,np.float32),_z]))

def run_cells(clients, vehicle, builder, specs, kind, collect_oracle=False):
    """Returns (mean_success, recovery_frames[(obs,lab)], student_sequences[(obs,act)])."""
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock(); rec_obs=[]; rec_lab=[]; seqs=[]
    shared=builder(vehicle) if kind=="stateless" else None
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]
            if kind=="stateless": pol=shared
            else:
                oracle=f2.make_avoidance_teacher(reveal=float(cell["reveal"]),mu=float(cell["mu"])).factory() if collect_oracle else None
                pol=builder(vehicle, oracle)
            r=f2.run_episode(c, sp["scenario"], "avoidance", pol, seed=int(sp["seed"]),
                             mu=float(cell["mu"]), reveal=float(cell["reveal"]))
            res[i]=bool(r["success"])
            if kind=="perep" and collect_oracle and isinstance(pol,PhiDeploy):
                with lock:
                    if pol.obs_log: rec_obs.append(np.stack(pol.obs_log)); rec_lab.append(np.stack(pol.lab))
                    if len(pol.seq)>=2:
                        sq=np.stack(pol.seq); seqs.append((sq[:,:72].copy(), sq[:,72:75].copy()))
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    mean=float(np.mean([x for x in res if x is not None]))
    return mean, (np.concatenate(rec_obs,0) if rec_obs else None, np.concatenate(rec_lab,0) if rec_lab else None), seqs

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rounds",type=int,default=2)
    ap.add_argument("--teacher-epochs",type=int,default=1500); ap.add_argument("--phi-epochs",type=int,default=2000)
    a=ap.parse_args(); torch.manual_seed(0)
    avoid_all=INT._load_avoid_cells(); mus=sorted(set(round(c['mu'],3) for c in avoid_all))
    val_cells=[c for c in avoid_all if round(c['mu'],3) in {mus[1],mus[2]}]   # 19-cell validation
    dag_cells=avoid_all                                                        # DAgger over all 36
    seqs=load_base(); frames_added={v:[] for v in VEH}
    clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_rma_w{w}_stderr.log') for w in range(8)]
    log={"rounds":[]}; t0=time.time()
    try:
        enc=film=phi=None
        for rd in range(a.rounds+1):
            enc,film,bl=train_teacher(seqs, epochs=a.teacher_epochs, enc=enc, film=film)
            phi,pl=train_phi(seqs, enc, epochs=a.phi_epochs, phi=phi)
            # validate
            row={"round":rd,"teacher_bc":bl,"phi_z_mse":pl,"phi":{}, "truez":{}}
            for v in VEH:
                d3v._install_vehicle(v)
                vspecs=INT._select_specs(v, [], val_cells, n_drift=0, n_avoid=3, namespace=f"rmaval{rd}")
                ph,_,_=run_cells(clients, v, lambda vv, orc=None: PhiDeploy(film,phi), vspecs, "perep")
                tz,_,_=run_cells(clients, v, lambda vv: true_z_policy(film,enc,vv), vspecs, "stateless")
                row["phi"][v]=ph; row["truez"][v]=tz
            mphi=float(np.mean(list(row["phi"].values()))); mtz=float(np.mean(list(row["truez"].values())))
            print(f"ROUND {rd}: teacher_bc={bl:.3e} phi_z_mse={pl:.3e} | phi-z avoid={row['phi']} (mean {mphi:.3f}) | "
                  f"true-z avoid={row['truez']} (mean {mtz:.3f})  [{time.time()-t0:.0f}s]", flush=True)
            log["rounds"].append(row)
            torch.save({"enc":enc.state_dict(),"film":film.state_dict(),"phi":phi.state_dict()},
                       RUN/f'selfid_rma_round{rd}.pt')
            if rd==a.rounds: break
            # DAgger collection: deploy phi-z_hat, relabel oracle, augment frames + phi sequences
            for v in VEH:
                d3v._install_vehicle(v)
                dspecs=INT._select_specs(v, [], dag_cells, n_drift=0, n_avoid=2, namespace=f"rmadag{rd}")
                _,(ro,rl),student_seqs=run_cells(clients, v, lambda vv,orc: PhiDeploy(film,phi,oracle=orc),
                                                 dspecs, "perep", collect_oracle=True)
                if ro is not None:
                    seqs[v].append((ro.astype(np.float32), rl.astype(np.float32)))  # recovery frames as a 'sequence'
                seqs[v].extend(student_seqs)  # student trajectories for phi distribution-match
                print(f"  [DAgger r{rd} {v}] +{0 if ro is None else ro.shape[0]} recovery frames, +{len(student_seqs)} student seqs", flush=True)
    finally:
        for c in clients:
            try: c.close()
            except Exception: pass
    Path(RUN/'_selfid_rma_full.json').write_text(json.dumps(log,indent=2))
    print(f"\nDONE {time.time()-t0:.0f}s. final round phi-z mean={mphi:.3f} true-z mean={mtz:.3f}")
if __name__=="__main__": main()
