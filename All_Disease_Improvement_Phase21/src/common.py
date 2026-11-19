from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix,roc_auc_score,average_precision_score,brier_score_loss,log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
ROOT=Path(__file__).resolve().parents[1];SEED=20261111
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,d):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def metrics(y,p,t):
    y=np.asarray(y);p=np.asarray(p,dtype=float);tn,fp,fn,tp=confusion_matrix(y,p>=t,labels=[0,1]).ravel()
    div=lambda a,b:float(a/b) if b else None
    specificity=div(tn,tn+fp);recall=div(tp,tp+fn)
    return dict(n=len(y),positive=int(y.sum()),negative=int((1-y).sum()),prevalence=float(y.mean()),tp=int(tp),fp=int(fp),tn=int(tn),fn=int(fn),threshold=float(t),precision=div(tp,tp+fp),recall=recall,fpr=div(fp,fp+tn),specificity=specificity,f1=div(2*tp,2*tp+fp+fn) or 0.,f2=div(5*tp,5*tp+4*fn+fp) or 0.,accuracy=div(tp+tn,len(y)),balanced_accuracy=(recall+specificity)/2 if recall is not None and specificity is not None else None,roc_auc=float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,average_precision=float(average_precision_score(y,p)) if y.sum() else None,brier=float(brier_score_loss(y,p)),log_loss=float(log_loss(y,p,labels=[0,1])))

def intervals(y,p,t,n=300,groups=None):
    rng=np.random.default_rng(SEED);y=np.asarray(y);p=np.asarray(p)
    keys=['precision','recall','fpr','specificity','f1','f2','roc_auc','average_precision','balanced_accuracy','accuracy','brier','log_loss']
    rows=[]
    if groups is not None:
        gg=np.asarray(groups);unique=np.unique(gg);blocks=[np.flatnonzero(gg==g) for g in unique]
    for _ in range(n):
        if groups is None:ix=rng.integers(0,len(y),len(y))
        else:
            sample=rng.integers(0,len(blocks),size=len(blocks))
            ix=np.concatenate([blocks[i] for i in sample])
        if len(np.unique(y[ix]))==2:rows.append(metrics(y[ix],p[ix],t))
    return {k:dict(low=float(np.percentile(v,2.5)),high=float(np.percentile(v,97.5)),valid_replicates=len(v)) if (v:=[r[k] for r in rows if r[k] is not None]) else None for k in keys}

def calibration_diagnostics(y,p):
    y=np.asarray(y);p=np.asarray(p);q=np.clip(p,1e-6,1-1e-6);bins=np.minimum((p*10).astype(int),9)
    ece=sum(np.mean(bins==b)*abs(y[bins==b].mean()-p[bins==b].mean()) for b in np.unique(bins))
    lr=LogisticRegression(C=1e6,max_iter=1500).fit(np.log(q/(1-q)).reshape(-1,1),y)
    return dict(ece10=float(ece),slope=float(lr.coef_[0,0]),intercept=float(lr.intercept_[0]),mean_score=float(p.mean()),observed_prevalence=float(y.mean()),clinical_probability_eligibility=False,research_score_availability=True)

def threshold_scenarios(y,p):
    from sklearn.metrics import precision_recall_curve
    y=np.asarray(y);pr,rr,ts=precision_recall_curve(y,p);pr=pr[:-1];rr=rr[:-1]
    tp=rr*y.sum();fp=np.divide(tp,pr,out=np.zeros_like(tp),where=pr>0)-tp;fpr=np.maximum(fp,0)/(len(y)-y.sum())
    f1=np.divide(2*pr*rr,pr+rr,out=np.zeros_like(pr),where=(pr+rr)>0)
    feasible=(pr>=.70)&(rr>=.75)&(fpr<=.15)
    base=feasible if feasible.any() else (fpr<=.15)&(tp>0)
    if not base.any():base=np.ones(len(ts),dtype=bool)
    choose=lambda mask,values: int((ix:=np.flatnonzero(mask))[np.argmax(values[ix])])
    balanced=choose(base,f1)
    highr=choose(rr>=.85,pr-1e-8*fpr)
    hp=(pr>=.70)&(fpr<=.15)&((tp+fp)>=5)
    hp_met=bool(hp.any())
    if not hp.any():hp=(fpr<=.05)&(tp>0)
    if not hp.any():hp=np.ones(len(ts),dtype=bool)
    highp=choose(hp,rr if hp_met else f1)
    scenarios={name:dict(threshold=float(ts[ix]),metrics=metrics(y,p,ts[ix]),constraints_met=bool(feasible[ix]) if name=='BALANCED' else bool(rr[ix]>=.85) if name=='HIGH_RECALL' else hp_met) for name,ix in [('BALANCED',balanced),('HIGH_RECALL',highr),('HIGH_PRECISION',highp)]}
    curve=pd.DataFrame(dict(threshold=ts,precision=pr,recall=rr,fpr=fpr,f1=f1,goal_feasible=feasible))
    return scenarios,curve

def rank_selection(row):
    m=row['scenarios']['BALANCED']['metrics'];feasible=m['precision'] is not None and m['precision']>=.7 and m['recall']>=.75 and m['fpr']<=.15
    return (int(feasible),int(m['fpr']<=.15),m['average_precision'] if feasible else m['f1'],m['average_precision'],-m['brier'])

class CalibratedResearchModel:
    """Calibration fitted to untouched real calibration people, not resampled data."""
    def __init__(self,pipeline,method='raw'):
        self.pipeline=pipeline;self.method=method;self.calibrator=None
    def calibrate(self,X,y):
        p=self.pipeline.predict_proba(X)[:,1]
        if self.method=='sigmoid':self.calibrator=LogisticRegression(C=1e6,max_iter=1000).fit(np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6))).reshape(-1,1),y)
        elif self.method=='isotonic':self.calibrator=IsotonicRegression(out_of_bounds='clip').fit(p,y)
        return self
    def predict_proba(self,X):
        p=self.pipeline.predict_proba(X)[:,1]
        if self.method=='sigmoid':p=self.calibrator.predict_proba(np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6))).reshape(-1,1))[:,1]
        elif self.method=='isotonic':p=self.calibrator.predict(p)
        return np.column_stack([1-p,p])
    def predict(self,X):return self.predict_proba(X)[:,1]>=.5
