import numpy as np
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE,ADASYN,SMOTENC,RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTEENN,SMOTETomek
from common import SEED

class PhysicalSpaceSampler(BaseEstimator):
    """Scale ONLY for neighbor distance; return physical base measurements, no derived fields."""
    def __init__(self,method='SMOTE',categorical_indices=None):
        self.method=method;self.categorical_indices=categorical_indices
    def fit_resample(self,X,y):
        X=np.asarray(X,dtype=float);yy=np.asarray(y);self.n_input_=len(X)
        cat=list(self.categorical_indices or []);num=[i for i in range(X.shape[1]) if i not in cat]
        counts=np.bincount(yy.astype(int),minlength=2)
        if min(counts)/max(counts)>=.8:
            self.n_output_=len(X);self.status_='SKIPPED_NEAR_BALANCED';self.max_derived_error_=0.;return X,yy
        self.numeric_indices_=num;self.scale_=StandardScaler().fit(X[:,num]);xx=X.copy();xx[:,num]=self.scale_.transform(xx[:,num])
        k=max(1,min(3,int(min(counts))-1));kwargs=dict(random_state=SEED)
        samplers={'RandomOverSampler':lambda:RandomOverSampler(**kwargs),'RandomUnderSampler':lambda:RandomUnderSampler(**kwargs),'SMOTE':lambda:SMOTE(k_neighbors=k,**kwargs),'ADASYN':lambda:ADASYN(n_neighbors=k,**kwargs),'SMOTENC':lambda:SMOTENC(categorical_features=cat,k_neighbors=k,**kwargs),'SMOTEENN':lambda:SMOTEENN(smote=SMOTE(k_neighbors=k,**kwargs),**kwargs),'SMOTETomek':lambda:SMOTETomek(smote=SMOTE(k_neighbors=k,**kwargs),**kwargs)}
        if self.method in ['SMOTE','ADASYN','SMOTEENN','SMOTETomek']:assert not cat
        self.sampler_=samplers[self.method]();zz,zy=self.sampler_.fit_resample(xx,yy);zz=np.asarray(zz,dtype=float);zz[:,num]=self.scale_.inverse_transform(zz[:,num])
        self.n_output_=len(zz);self.status_='RESAMPLED_BASE_MEASUREMENTS';self.category_supported_=True
        for c in cat:self.category_supported_ &= set(zz[:,c])<=set(X[:,c])
        assert self.category_supported_ and np.isfinite(zz).all()
        return zz,zy

class DeterministicDerivedFeatures(BaseEstimator,TransformerMixin):
    def __init__(self,base_names=None,specs=None):self.base_names=base_names;self.specs=specs
    def fit(self,X,y=None):
        self.applied_=[s for s in (self.specs or []) if s['a'] in self.base_names and s['b'] in self.base_names]
        self.output_names_=list(self.base_names)+[s['name'] for s in self.applied_];self.max_derived_error_=0.;return self
    def transform(self,X):
        xx=np.asarray(X,dtype=float);out=[xx]
        for spec in self.applied_:
            a=xx[:,self.base_names.index(spec['a'])];b=xx[:,self.base_names.index(spec['b'])]
            z=a*b if spec['kind']=='product' else np.divide(a,b,out=np.full(len(a),np.nan),where=b>0)
            out.append(z[:,None])
            expected=a*b if spec['kind']=='product' else np.divide(a,b,out=np.full(len(a),np.nan),where=b>0)
            assert np.allclose(z,expected,rtol=0,atol=0,equal_nan=True)
        return np.column_stack(out)
    def get_feature_names_out(self,input_features=None):return np.array(self.output_names_,dtype=object)
