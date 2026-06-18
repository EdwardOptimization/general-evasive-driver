"""FULL-SCENARIO label-free self-ID driver: ONE gated FiLMZ (gate + drift head + avoid head), z inferred from
(obs,action) history, masters drift+avoid across 3 vehicles with NO vehicle label. Tests the VoI two-regime law in
the self-ID dimension: avoid needs z (self-ID valuable), drift is vehicle-general (self-ID redundant) -> drift should
hold regardless. DAgger on avoid only (drift BC-sufficient). Gate supervised by regime (known at train: drift=1/avoid=0)."""
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
RUN=Path('runs/feasibility_audit/phase4_f2'); ASEQ=RUN/'selfid_avoid_seqs'; DSEQ=RUN/'selfid_drift_seqs'
VEH=["sedan","uazbus","bmw"]; W=M.AdaptationMLP().window; ZD=M.RICH_Z
pv=json.load(open('runs/feasibility_audit/spectrum_s1/feasibility_precheck_per_vehicle.json'))

def load_seqs():
    """per vehicle: list of (obs,act,regime) with regime in {'drift','avoid'} (successful only)."""
    out={v:[] for v in VEH}
    for v in VEH:
        da=np.load(ASEQ/f'avoid_{v}.npz',allow_pickle=True)
        for obs,act,s in zip(da["obs"],da["act"],da["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(s): out[v].append((obs,act,"avoid"))
        dd=np.load(DSEQ/f'drift_{v}.npz',allow_pickle=True)
        for obs,act,s in zip(dd["obs"],dd["act"],dd["success"]):
            obs=np.asarray(obs,np.float32); act=np.asarray(act,np.float32)
            if obs.shape[0]>=2 and bool(s): out[v].append((obs,act,"drift"))
    return out

def frames_from(TF):
    OBS=[];EX=[];ACT=[];REG=[]
    for v in VEH:
        ex=M.vehicle_extrinsics(v)
        for obs,act,reg in TF[v]:
            OBS.append(obs); ACT.append(act); EX.append(np.tile(ex,(obs.shape[0],1)))
            REG.append(np.full(obs.shape[0], 1.0 if reg=="drift" else 0.0, np.float32))
    return (torch.tensor(np.concatenate(OBS,0)), torch.tensor(np.concatenate(EX,0).astype(np.float32)),
            torch.tensor(np.concatenate(ACT,0)), torch.tensor(np.concatenate(REG,0)))

def windows_from(PS, stride=3):
    XS=[];EX=[]
    for v in VEH:
        ex=M.vehicle_extrinsics(v)
        for obs,act,reg in PS[v]:
            T=obs.shape[0]; prev=np.zeros_like(act); prev[1:]=act[:-1]; step=np.concatenate([obs,prev],1)
            for t in range(1,T,stride):
                lo=max(0,t-W+1); ch=step[lo:t+1]
                if ch.shape[0]<W: ch=np.concatenate([np.zeros((W-ch.shape[0],75),np.float32),ch],0)
                XS.append(ch.reshape(-1)); EX.append(ex)
    return torch.tensor(np.stack(XS)), torch.tensor(np.stack(EX).astype(np.float32))

def train_teacher(TF, *, epochs, enc=None, film=None, lr=1e-3, gate_w=0.3):
    OBS,EX,ACT,REG=frames_from(TF); N=OBS.shape[0]
    enc=enc or M.ExtrinsicsEncoder(z_dim=ZD); film=film or M.FiLMZActorCritic(z_dim=ZD)
    opt=torch.optim.Adam(list(enc.parameters())+list(film.parameters()),lr=lr); enc.train(); film.train()
    bce=torch.nn.BCELoss()
    d_idx=torch.nonzero(REG>0.5).squeeze(-1); a_idx=torch.nonzero(REG<0.5).squeeze(-1)   # BALANCE regimes
    for ep in range(epochs):
        idx=torch.cat([d_idx[torch.randint(0,len(d_idx),(256,))], a_idx[torch.randint(0,len(a_idx),(256,))]])  # 256 drift + 256 avoid
        z=enc(EX[idx]); X=torch.cat([OBS[idx],z],1)
        h=film._trunk(X); g=torch.sigmoid(film.actor_gate(h)).squeeze(-1)
        mean=torch.tanh(g.unsqueeze(-1)*film.drift_head(h)+(1-g).unsqueeze(-1)*film.avoid_head(h))
        loss=((mean-ACT[idx])**2).mean() + gate_w*bce(g.clamp(1e-6,1-1e-6), REG[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    enc.eval(); film.eval(); return enc,film,float(loss.item())

def train_phi(PS, enc, *, epochs, phi=None, lr=1e-3):
    X,EX=windows_from(PS); N=X.shape[0]; phi=phi or M.AdaptationMLP(z_dim=ZD)
    with torch.no_grad(): Z=enc(EX)
    opt=torch.optim.Adam(phi.parameters(),lr=lr); phi.train()
    for ep in range(epochs):
        idx=torch.randint(0,N,(1024,)); loss=((phi(X[idx])-Z[idx])**2).mean(); opt.zero_grad(); loss.backward(); opt.step()
    phi.eval(); return phi,float(loss.item())

class PhiDeploy:
    def __init__(self, film, phi, oracle=None):
        self.film=film; self.phi=phi; self.oracle=oracle; self.hist=deque(maxlen=W); self.prev=np.zeros(3,np.float32)
        self.obs_log=[]; self.lab=[]; self.seq=[]
    def __call__(self,s,obs):
        obs=np.asarray(obs,np.float32); step_in=np.concatenate([obs,self.prev]); self.hist.append(step_in); self.seq.append(step_in.copy())
        win=list(self.hist); pad=W-len(win)
        flat=np.concatenate(([np.zeros(75,np.float32)]*pad)+win) if pad>0 else np.concatenate(win)
        with torch.no_grad(): zh=self.phi(torch.tensor(flat.astype(np.float32)).unsqueeze(0)).numpy()[0]
        if self.oracle is not None and f2._obstacle_visible(obs,{}):
            self.obs_log.append(obs.copy()); self.lab.append(np.clip(self.oracle(s,obs),-1,1).astype(np.float32))
        a=self.film.act(np.concatenate([obs,zh.astype(np.float32)])); self.prev=a; return a

def run_avoid(clients, v, builder, specs, collect=False):
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock(); R_obs=[];R_lab=[];seqs=[]
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]
            orc=f2.make_avoidance_teacher(reveal=float(cell["reveal"]),mu=float(cell["mu"])).factory() if collect else None
            pol=builder(orc)
            r=f2.run_episode(c,sp["scenario"],"avoidance",pol,seed=int(sp["seed"]),mu=float(cell["mu"]),reveal=float(cell["reveal"]))
            res[i]=bool(r["success"])
            if collect and isinstance(pol,PhiDeploy):
                with lock:
                    if pol.obs_log: R_obs.append(np.stack(pol.obs_log)); R_lab.append(np.stack(pol.lab))
                    if len(pol.seq)>=2: sq=np.stack(pol.seq); seqs.append((sq[:,:72].copy(),sq[:,72:75].copy(),"avoid"))
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    return float(np.mean([x for x in res if x is not None])), (np.concatenate(R_obs,0) if R_obs else None, np.concatenate(R_lab,0) if R_lab else None), seqs

def run_drift(clients, v, builder, specs):
    res=[None]*len(specs); ctr={'i':0}; lock=threading.Lock()
    def worker(wi):
        c=clients[wi]
        while True:
            with lock:
                if ctr['i']>=len(specs): return
                i=ctr['i']; ctr['i']+=1
            sp=specs[i]; cell=sp["cell"]; pol=builder(None)
            r=f2.run_episode(c,sp["scenario"],"drift",pol,seed=int(sp["seed"]),mu=float(cell["mu"]),reveal=0.0)
            res[i]=bool(r["success"])
    with ThreadPoolExecutor(max_workers=len(clients)) as ex:
        for fut in [ex.submit(worker,w) for w in range(len(clients))]: fut.result()
    return float(np.mean([x for x in res if x is not None]))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--rounds",type=int,default=1)
    ap.add_argument("--teacher-epochs",type=int,default=2500); ap.add_argument("--phi-epochs",type=int,default=2000)
    a=ap.parse_args(); torch.manual_seed(0)
    avoid_all=INT._load_avoid_cells(); mus=sorted(set(round(c['mu'],3) for c in avoid_all))
    aval=[c for c in avoid_all if round(c['mu'],3) in {mus[1],mus[2]}]
    seqs=load_seqs(); TF={v:list(seqs[v]) for v in VEH}; PS={v:list(seqs[v]) for v in VEH}
    clients=[INT.ResilientChronoClient(stderr_log=RUN/f'_fs_w{w}_stderr.log') for w in range(8)]
    log={"rounds":[]}; best={"score":-1}; t0=time.time()
    try:
        enc=film=phi=None
        for rd in range(a.rounds+1):
            enc,film,bl=train_teacher(TF,epochs=a.teacher_epochs,enc=enc,film=film)
            phi,pl=train_phi(PS,enc,epochs=a.phi_epochs,phi=phi)
            row={"round":rd,"drift":{},"avoid":{}}
            for v in VEH:
                d3v._install_vehicle(v)
                dcells=INT._vehicle_drift_cells(v,pv)
                dspecs=[{"cell":c,"seed":int(f2._seed_for("fsdval",v,"drift",ci,i,round(c["mu"],3),round(c["beta"],3))),
                         "scenario":INT._drift_scenario(v,c,int(f2._seed_for("fsdval",v,"drift",ci,i,round(c["mu"],3),round(c["beta"],3))))}
                        for ci,c in enumerate(dcells) for i in range(3)]
                aspecs=INT._select_specs(v,[],aval,n_drift=0,n_avoid=3,namespace=f"fsaval{rd}")
                row["drift"][v]=run_drift(clients,v,lambda orc=None:PhiDeploy(film,phi),dspecs)
                row["avoid"][v]=run_avoid(clients,v,lambda orc=None:PhiDeploy(film,phi),aspecs)[0]
            md=float(np.mean(list(row["drift"].values()))); ma=float(np.mean(list(row["avoid"].values())))
            row["drift_mean"]=md; row["avoid_mean"]=ma; sc=md+ma
            print(f"ROUND {rd}: DRIFT(no label)={ {k:round(x,3) for k,x in row['drift'].items()} } mean {md:.3f} | "
                  f"AVOID(no label)={ {k:round(x,3) for k,x in row['avoid'].items()} } mean {ma:.3f}  [{time.time()-t0:.0f}s]", flush=True)
            log["rounds"].append(row)
            if sc>best["score"]:
                best={"score":sc,"round":rd}
                torch.save({"enc":enc.state_dict(),"film":film.state_dict(),"phi":phi.state_dict(),"round":rd},RUN/'selfid_fullscenario.pt')
            if rd==a.rounds: break
            for v in VEH:   # DAgger on AVOID only (drift is BC-sufficient from a reliable oracle)
                d3v._install_vehicle(v)
                ds=INT._select_specs(v,[],avoid_all,n_drift=0,n_avoid=2,namespace=f"fsdag{rd}")
                _,(ro,rl),sseq=run_avoid(clients,v,lambda orc:PhiDeploy(film,phi,oracle=orc),ds,collect=True)
                if ro is not None: TF[v].append((ro.astype(np.float32),rl.astype(np.float32),"avoid"))
                PS[v].extend(sseq)
    finally:
        for c in clients:
            try: c.close()
            except Exception: pass
    log["best"]=best; Path(RUN/'_selfid_fullscenario.json').write_text(json.dumps(log,indent=2))
    br=log["rounds"][best["round"]]
    print(f"\nDONE {time.time()-t0:.0f}s. BEST round {best['round']}: DRIFT mean={br['drift_mean']:.3f} AVOID mean={br['avoid_mean']:.3f}")
    print(f"  drift={ {k:round(x,3) for k,x in br['drift'].items()} }  avoid={ {k:round(x,3) for k,x in br['avoid'].items()} }")
if __name__=="__main__": main()
